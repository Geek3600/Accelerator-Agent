#!/usr/bin/env python3
"""Run a manifest-bound exact sample-project board simulation on remote VCS."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.board_acceptance_contract import (
    SYNTHESIS_ONLY_ROLES,
    canonical_contract_sha256,
    validate_exact_board_acceptance,
    validate_exact_board_preflight,
)
from accagent.framework.board_artifact_persistence import (
    board_remote_stage_root,
    persist_board_remote_artifacts,
)
from accagent.framework.active_board_job import (
    pending_exact_board_job,
    write_pending_exact_board_job_report,
)
from accagent.framework.fast_replay import (
    fast_replay_request_path,
    fast_replay_state_path,
    read_fast_replay_state,
    restore_inputs,
    update_fast_replay_state,
    validate_fast_replay_state,
)
from accagent.framework.fpga_ip_runtime import (
    ip_vcs_filelist_argument,
    stage_fpga_ip_runtime,
)
from accagent.framework.live_state import (
    activate_live_state_slot,
    board_run_binding,
    board_run_status,
    update_live_state_slot,
)
from accagent.framework.runtime_observation import (
    current_observation_selection_path,
    runtime_observation_selection,
)
from accagent.framework.board_progress import (
    BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
    pipeline_boundary_observation_authority,
    read_complete_jsonl,
    read_pipeline_trace_log,
    stage_internal_records_from_boundary_observations,
    summarize_runtime_stage_trace_log,
    summarize_stage_internal_observations,
    summarize_pipeline_boundary_observations,
    summarize_progress_events,
)
from accagent.framework.semantic_simulator import (
    REMOTE_SEMANTIC_JOB_CONTRACT,
    ZERO_TIME_LIVELOCK_EXIT_CODE,
    normalized_exit_signal,
    recover_exact_remote_semantic_job,
    remote_background_job_state,
    run_remote_background_command,
    semantic_vcs_compile_jobs,
    wait_for_existing_remote_job,
)
from accagent.framework.simulation_checkpoint import (
    CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION,
    CHECKPOINT_MANIFEST_SCHEMA_VERSION,
    CHECKPOINT_RESTORE_REPORT_SCHEMA_VERSION,
    checkpoint_contract,
    checkpoint_contract_errors,
    checkpoint_manifest_errors,
    checkpoint_request_errors,
    checkpoint_root,
    framework_checkpoint_contract,
    heavy_job_lease,
    simulation_execution_identity,
)


SCHEMA_VERSION = "spatialaccagent.board_vcs_functional_run.v1"
VCS_COMPILE_PLAN_SCHEMA_VERSION = "spatialaccagent.vcs_compile_plan.v1"
RUNTIME_MANIFEST_FIELDS = {
    "debug_observability_results",
    "dynamic_evidence_records",
    "elaborated_hierarchy",
    "execution_evidence",
    "pipeline_overlap_results",
    "protocol_monitor_results",
    "runtime_loader_results",
}
NATIVE_CHECKPOINT_SNAPSHOT = Path("checkpoint/native_state")
NATIVE_CHECKPOINT_SNAPSHOT_FILES = Path("checkpoint/native_state.FILES")
NATIVE_CHECKPOINT_CAPTURE_TCL = Path("checkpoint/ucli_capture.tcl")
NATIVE_CHECKPOINT_RESTORE_TCL = Path("checkpoint/ucli_restore.tcl")
FRESH_EXACT_BOARD_REPLAY_GENERATION_ENV = (
    "SPATIALACC_FRESH_EXACT_BOARD_REPLAY_GENERATION_SHA256"
)


def exact_board_remote_workdir(
    remote_stage_root: str,
    input_fingerprint_sha256: str,
    replay_generation_sha256: str = "",
) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", input_fingerprint_sha256):
        raise ValueError("exact-board input fingerprint must be 64 lowercase hex")
    if replay_generation_sha256:
        if not re.fullmatch(r"[0-9a-f]{64}", replay_generation_sha256):
            raise ValueError(
                "fresh exact-board replay generation must be 64 lowercase hex"
            )
        execution_identity = hashlib.sha256(
            (
                input_fingerprint_sha256
                + ":"
                + replay_generation_sha256
            ).encode("ascii")
        ).hexdigest()
        suffix = int(execution_identity, 16)
    else:
        suffix = int(input_fingerprint_sha256[12:], 16)
    return (
        f"{remote_stage_root}/{input_fingerprint_sha256[:12]}_{suffix}"
    )


def _systemverilog_code_and_string_literals(text: str) -> tuple[str, list[str]]:
    """Remove comments/strings from code while retaining real string literals."""

    code = list(text)
    literals: list[str] = []
    index = 0
    while index < len(text):
        if text.startswith("//", index):
            end = text.find("\n", index + 2)
            end = len(text) if end < 0 else end
            for cursor in range(index, end):
                code[cursor] = " "
            index = end
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = len(text) if end < 0 else end + 2
            for cursor in range(index, end):
                if code[cursor] != "\n":
                    code[cursor] = " "
            index = end
            continue
        if text[index] != '"':
            index += 1
            continue
        start = index
        index += 1
        literal: list[str] = []
        while index < len(text):
            character = text[index]
            if character == "\\" and index + 1 < len(text):
                literal.extend((character, text[index + 1]))
                index += 2
                continue
            if character == '"':
                index += 1
                break
            literal.append(character)
            index += 1
        literals.append("".join(literal))
        for cursor in range(start, index):
            if code[cursor] != "\n":
                code[cursor] = " "
    return "".join(code), literals


def _systemverilog_system_call_argument_counts(
    code: str, function_name: str
) -> tuple[list[int], bool]:
    pattern = re.compile(
        rf"(?<![A-Za-z0-9_$])\${re.escape(function_name)}\s*\("
    )
    counts: list[int] = []
    balanced = True
    matching = {")": "(", "]": "[", "}": "{"}
    for match in pattern.finditer(code):
        stack = ["("]
        cursor = match.end()
        comma_count = 0
        has_argument_text = False
        while cursor < len(code) and stack:
            character = code[cursor]
            if character in "([{":
                stack.append(character)
            elif character in matching:
                if not stack or stack[-1] != matching[character]:
                    balanced = False
                    break
                stack.pop()
                if not stack:
                    break
            elif character == "," and len(stack) == 1:
                comma_count += 1
            elif not character.isspace() and len(stack) == 1:
                has_argument_text = True
            cursor += 1
        if stack:
            balanced = False
            continue
        counts.append(comma_count + 1 if has_argument_text else 0)
    return counts, balanced


def checkpoint_hook_source_errors(
    manifest: dict[str, Any],
    testbench_path: Path | None,
    *,
    checkpoint_required: bool = False,
) -> list[str]:
    """Check the one minimal testbench hook used for a native VCS save."""

    # A regular board simulation does not require the acceleration hook.  The
    # hook is checked only for the forced Layer-3 capture flow so ordinary VCS
    # tests and final cold acceptance preserve their existing behavior.
    if not checkpoint_required:
        return []
    contract = framework_checkpoint_contract(manifest)
    if not contract:
        return []
    if not isinstance(testbench_path, Path) or not testbench_path.is_file():
        return ["declared simulation checkpoint contract has no readable testbench source"]
    try:
        text = testbench_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"simulation checkpoint testbench source is unreadable: {exc}"]
    code, literals = _systemverilog_code_and_string_literals(text)
    errors: list[str] = []
    literal_text = "\n".join(literals)
    if "SPATIALACC_NATIVE_CHECKPOINT_CAPTURE" not in literal_text:
        errors.append("simulation checkpoint testbench lacks native capture plusarg")
    if "SPATIALACC_NATIVE_CHECKPOINT_READY" not in literal_text:
        errors.append("simulation checkpoint testbench lacks native capture ready marker")
    if not re.search(r"(?<![A-Za-z0-9_$])\$stop\s*;", code):
        errors.append("simulation checkpoint testbench has no executable $stop")
    return errors


def checkpoint_execution_plan(
    run_dir: Path,
    manifest: dict[str, Any],
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build the minimal Layer-3 checkpoint execution plan.

    The only replay conditions are the current compiled-model/workload identity,
    the fixed capture cut, the three saved state files, and the one-time restore
    confirmation.  Historical hashes and calibration artifacts are ignored.
    """

    values = env if env is not None else os.environ
    required = str(values.get("SPATIALACC_CHECKPOINT_REQUIRED") or "") == "1"
    request_value = str(values.get("SPATIALACC_CHECKPOINT_REQUEST") or "").strip()
    if not request_value:
        if str(values.get("SPATIALACC_CHECKPOINT_FINAL_COLD") or "") == "1":
            return {
                "status": "pass",
                "mode": "full_cold_acceptance",
                "enabled": False,
                "adapter_enabled": False,
                "candidate_screening": False,
                "acceptance_eligible": True,
                "required_for_stage3_repair": required,
                "errors": [],
            }
        return {
            "status": "fail" if required else "pass",
            "mode": "repair_required" if required else "disabled",
            "enabled": False,
            "required_for_stage3_repair": required,
            "errors": ["Layer-3 replay requires a checkpoint request"] if required else [],
        }

    request_path = Path(request_value).expanduser().resolve()
    request = read_json(request_path) if request_path.is_file() else {}
    errors: list[str] = []
    if not request_path.is_file() or not request_path.is_relative_to(run_dir.resolve()):
        errors.append("checkpoint request is missing or outside the current run")
    elif request:
        errors.extend(checkpoint_request_errors(request))

    contract = framework_checkpoint_contract(manifest)
    errors.extend(checkpoint_contract_errors(contract))
    current_identity = simulation_execution_identity(manifest)
    request_identity = request.get("execution_identity", {})
    request_identity = request_identity if isinstance(request_identity, dict) else {}
    for field in ("compiled_model_sha256", "workload_sha256"):
        if request_identity.get(field) != current_identity.get(field):
            errors.append(f"checkpoint request {field} does not match the current board")

    decision = request.get("replay_decision", {})
    decision = decision if isinstance(decision, dict) else {}
    mode = str(decision.get("mode") or "")
    fast_replay_requested = str(values.get("SPATIALACC_FAST_REPLAY") or "") == "1"
    restore_check = str(values.get("SPATIALACC_FAST_REPLAY_RESTORE_CHECK") or "") == "1"
    fast_replay: dict[str, Any] = {"requested": fast_replay_requested, "used": False}
    selected_manifest_path: Path | None = None
    selected_manifest: dict[str, Any] = {}

    if fast_replay_requested:
        validation = validate_fast_replay_state(
            run_dir,
            read_fast_replay_state(run_dir),
            current_identity=current_identity,
            require_verified=not restore_check,
        )
        fast_replay["validation"] = validation
        if validation.get("status") != "ready":
            errors.extend(str(value) for value in validation.get("reasons", []) if str(value))
        else:
            mode = "native_exact_model"
            selected_manifest_path = Path(
                str(validation.get("checkpoint_manifest") or "")
            ).resolve()
            selected_manifest = read_json(selected_manifest_path)
            fast_replay.update(
                {
                    "used": True,
                    "remote_workdir": validation.get("remote_workdir"),
                    "simulator_path": validation.get("simulator_path"),
                    "checkpoint_manifest": str(selected_manifest_path),
                    "restore_check": restore_check,
                }
            )
    elif mode == "native_exact_model":
        selected_value = str(request.get("selected_checkpoint_manifest") or "")
        selected_manifest_path = Path(selected_value).expanduser().resolve()
        selected_manifest = read_json(selected_manifest_path)

    if mode not in {"cold_capture", "native_exact_model"}:
        errors.append("checkpoint request mode is invalid")
    if mode == "native_exact_model":
        if selected_manifest_path is None or not selected_manifest_path.is_file():
            errors.append("selected checkpoint manifest is missing")
        else:
            errors.extend(
                checkpoint_manifest_errors(
                    selected_manifest, artifact_root=selected_manifest_path.parent
                )
            )
            selected_identity = selected_manifest.get("execution_identity", {})
            selected_identity = (
                selected_identity if isinstance(selected_identity, dict) else {}
            )
            for field in ("compiled_model_sha256", "workload_sha256"):
                if selected_identity.get(field) != current_identity.get(field):
                    errors.append(f"selected checkpoint {field} does not match the current board")

    if errors:
        return {
            "status": "fail",
            "mode": "repair_required",
            "enabled": False,
            "required_for_stage3_repair": required,
            "request_path": str(request_path),
            "request": request,
            "contract": contract,
            "execution_identity": current_identity,
            "selected_checkpoint_manifest_path": str(selected_manifest_path) if selected_manifest_path else None,
            "selected_checkpoint_manifest": selected_manifest,
            "fast_replay": fast_replay,
            "errors": errors,
        }
    return {
        "status": "pass",
        "mode": mode,
        "enabled": True,
        "adapter_enabled": False,
        "candidate_screening": False,
        "acceptance_eligible": True,
        "required_for_stage3_repair": required,
        "request_path": str(request_path),
        "request": request,
        "contract": contract,
        "execution_identity": current_identity,
        "selected_checkpoint_manifest_path": str(selected_manifest_path) if selected_manifest_path else None,
        "selected_checkpoint_manifest": selected_manifest,
        "fast_replay": fast_replay,
        "errors": [],
        "policy": {
            "native_snapshot_requires_exact_compiled_model": True,
            "restore_requires_runtime_schema_match": True,
        },
    }

def checkpoint_runtime_plusargs(plan: dict[str, Any]) -> list[str]:
    if plan.get("enabled") is not True:
        return []
    args: list[str] = []
    if plan.get("mode") == "cold_capture":
        args.append("+SPATIALACC_NATIVE_CHECKPOINT_CAPTURE")
    return args


def checkpoint_equivalence_runtime_plusargs(plan: dict[str, Any]) -> list[str]:
    """Compatibility shim for retired VPI equivalence callers.

    Native VCS save/restore needs no second state-capsule calibration pass.
    """

    return []


def native_checkpoint_capture_tcl() -> str:
    """Stop at the testbench fixed cut and save the complete VCS state."""

    return "\n".join(
        (
            # The testbench owns the capture cut and stops VCS only after the
            # last weight beat has been accepted. A timed run could save a
            # startup state before that marker is reached.
            "run",
            # VCS cannot save while it is still stopped inside $stop.  A
            # zero-time run leaves that task without advancing the design.
            "run 0",
            f"save {NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}",
            'puts "SPATIALACC_NATIVE_CHECKPOINT_SAVE_PASS"',
            "quit",
            "",
        )
    )


def native_checkpoint_restore_tcl() -> str:
    """Restore one saved state and then run the original workload suffix."""

    return "\n".join(
        (
            f"restore {NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}",
            'puts "SPATIALACC_NATIVE_CHECKPOINT_RESTORE_PASS"',
            "run",
            "quit",
            "",
        )
    )


def checkpoint_equivalence_output_paths(
    manifest: dict[str, Any],
    output_plan: dict[str, Any],
) -> list[Path]:
    """List simulator outputs that must survive a restore calibration run."""

    values: list[Any] = [
        output_plan.get("simulation_log", {}).get("path"),
        output_plan.get("progress_event_log", {}).get("path"),
        output_plan.get("elaborated_hierarchy_report", {}).get("path"),
        output_plan.get("pipeline_overlap_report", {}).get("path"),
        manifest.get("rtl_output_file"),
        manifest.get("boundary_trace_file"),
    ]
    runtime_loader = output_plan.get("runtime_loader_report")
    if isinstance(runtime_loader, dict):
        values.append(runtime_loader.get("path"))
    for row in output_plan.get("protocol_monitor_reports", []):
        if isinstance(row, dict):
            values.append(row.get("path"))
    paths: list[Path] = []
    seen: set[str] = set()
    for value in values:
        relative = safe_relative_path(value)
        if relative is None or relative.as_posix() in seen:
            continue
        seen.add(relative.as_posix())
        paths.append(relative)
    return paths


def checkpoint_equivalence_archive_command(
    output_paths: list[Path],
    *,
    destination: Path,
) -> str:
    destination_text = shlex.quote(destination.as_posix())
    commands = ["set -e;", f"mkdir -p {destination_text};"]
    for path in output_paths:
        source = shlex.quote(path.as_posix())
        target = shlex.quote((destination / path).as_posix())
        parent = shlex.quote((destination / path.parent).as_posix())
        commands.extend(
            [
                f"rm -f -- {target};",
                f"if [ -f {source} ]; then mkdir -p {parent}; cp -- {source} {target}; fi;",
            ]
        )
    return " ".join(commands)


def checkpoint_equivalence_restore_cold_command(
    output_paths: list[Path],
) -> str:
    destination = Path("checkpoint/equivalence/restored_outputs")
    commands = [
        "set +e;",
        f"mkdir -p {shlex.quote(destination.as_posix())};",
        "archive_rc=0;",
    ]
    for path in output_paths:
        source = shlex.quote(path.as_posix())
        target = shlex.quote((destination / path).as_posix())
        parent = shlex.quote((destination / path.parent).as_posix())
        commands.extend(
            [
                f"rm -f -- {target};",
                (
                    f"if [ -f {source} ]; then mkdir -p {parent}; "
                    f"cp -- {source} {target} || archive_rc=$?; fi;"
                ),
            ]
        )
    if output_paths:
        commands.append(
            "rm -f -- "
            + " ".join(shlex.quote(path.as_posix()) for path in output_paths)
            + ";"
        )
    commands.extend(
        [
            "cp -a checkpoint/equivalence/cold_outputs/. ./;",
            "restore_rc=$?;",
            "if [ \"$restore_rc\" -ne 0 ]; then exit \"$restore_rc\"; fi;",
            "printf '%s\\n' \"$archive_rc\" > checkpoint/equivalence/archive.exit;",
            "exit 0;",
        ]
    )
    return " ".join(commands)


def checkpoint_vpi_restore_schema_verified(
    simulation_log_path: Path,
    schema_path: Path,
) -> bool:
    """Verify the framework VPI adapter re-enumerated the same runtime schema."""

    if not simulation_log_path.is_file() or not schema_path.is_file():
        return False
    schema_text = schema_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"(?m)^fnv1a64=([0-9a-fA-F]+)\s*$", schema_text)
    if match is None:
        return False
    expected = match.group(1).lower()
    restore_markers = re.findall(
        r"SPATIALACC_CHECKPOINT_RESTORE_PASS[^\n]*schema=([0-9a-fA-F]+)",
        simulation_log_path.read_text(encoding="utf-8", errors="ignore"),
    )
    return bool(restore_markers and restore_markers[-1].lower() == expected)


def simulation_runtime_failure_evidence(
    simulation_log_path: Path,
    *,
    max_tail_lines: int = 40,
    max_matched_lines: int = 16,
) -> dict[str, Any]:
    """Return bounded, hash-bound runtime failure evidence for Agent routing."""

    if not simulation_log_path.is_file():
        return {
            "schema_version": "spatialaccagent.simulation_runtime_failure_evidence.v1",
            "status": "missing",
            "path": str(simulation_log_path),
            "matched_lines": [],
            "failure_lines": [],
            "simulator_crash_lines": [],
            "tail_lines": [],
        }
    text = simulation_log_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    failure_pattern = re.compile(
        r"(?:\b(?:fatal|error)\b|"
        r"SPATIALACC_CHECKPOINT_(?:CAPTURE|RESTORE)_FAIL|"
        r"restored checkpoint[^\n]*(?:differ|fail|mismatch))",
        re.IGNORECASE,
    )
    checkpoint_pattern = re.compile(
        r"SPATIALACC_CHECKPOINT_(?:CAPTURE|RESTORE)(?:_PASS|_FAIL)?",
        re.IGNORECASE,
    )
    simulator_crash_pattern = re.compile(
        r"unexpected termination has occurred in .*\bsimv\b.*"
        r"due to a signal:\s*segmentation fault",
        re.IGNORECASE,
    )
    termination_pattern = re.compile(r"\$finish", re.IGNORECASE)
    failures = [line for line in lines if failure_pattern.search(line)]
    simulator_crashes = [
        line for line in lines if simulator_crash_pattern.search(line)
    ]
    matched = [
        line
        for line in lines
        if failure_pattern.search(line) or simulator_crash_pattern.search(line)
    ]
    checkpoint_markers = [
        line for line in lines if checkpoint_pattern.search(line)
    ]
    termination_markers = [
        line for line in lines if termination_pattern.search(line)
    ]
    return {
        "schema_version": "spatialaccagent.simulation_runtime_failure_evidence.v1",
        "status": "observed" if matched else "not_observed",
        "path": str(simulation_log_path),
        "sha256": sha256_file(simulation_log_path),
        "byte_count": simulation_log_path.stat().st_size,
        "matched_lines": matched[-max_matched_lines:],
        "failure_lines": failures[-max_matched_lines:],
        "simulator_crash_lines": simulator_crashes[-max_matched_lines:],
        "checkpoint_markers": checkpoint_markers[-max_matched_lines:],
        "termination_markers": termination_markers[-max_matched_lines:],
        "tail_lines": lines[-max_tail_lines:],
        "matched_lines_truncated": len(matched) > max_matched_lines,
        "simulator_crash_lines_truncated": (
            len(simulator_crashes) > max_matched_lines
        ),
        "checkpoint_markers_truncated": (
            len(checkpoint_markers) > max_matched_lines
        ),
        "termination_markers_truncated": (
            len(termination_markers) > max_matched_lines
        ),
        "tail_lines_truncated": len(lines) > max_tail_lines,
    }


def apply_simulation_terminal_log_result(
    simulate_result: dict[str, Any],
    simulation_log_path: Path,
) -> dict[str, Any]:
    """Treat a simulator fatal in the terminal log as a failed execution.

    Some VCS testbenches call ``$finish`` after ``$fatal`` and therefore leave
    the detached shell command with exit code zero.  The terminal simulator log
    is the authoritative result in that case.
    """

    normalized = dict(simulate_result)
    runtime_evidence = simulation_runtime_failure_evidence(simulation_log_path)
    normalized["runtime_failure_evidence"] = runtime_evidence
    terminal_failure_observed = bool(
        runtime_evidence.get("failure_lines")
        or runtime_evidence.get("simulator_crash_lines")
    )
    if normalized.get("status") == "pass" and terminal_failure_observed:
        normalized["status"] = "fail"
        normalized["failure_class"] = (
            "simulator_reported_process_crash"
            if runtime_evidence.get("simulator_crash_lines")
            else "simulator_reported_terminal_failure"
        )
        normalized["terminal_log_failure_overrode_successful_exit"] = True
    return normalized


def simulation_termination_provenance(
    simulate_result: dict[str, Any],
    simulation_log_path: Path,
    *,
    timeout_sec: int,
    progress_summary: dict[str, Any],
    input_fingerprint_sha256: str,
    live_progress: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Project existing process and simulator evidence into one termination record."""

    returncode = simulate_result.get("returncode")
    returncode = (
        int(returncode)
        if isinstance(returncode, int) and not isinstance(returncode, bool)
        else None
    )
    failure_class = str(simulate_result.get("failure_class") or "")
    remote_state = str(simulate_result.get("remote_state") or "unknown")
    adaptive_termination = simulate_result.get(
        "adaptive_semantic_stall_termination", {}
    )
    adaptive_termination = (
        adaptive_termination if isinstance(adaptive_termination, dict) else {}
    )
    zero_time_termination = simulate_result.get(
        "zero_time_livelock_termination", {}
    )
    zero_time_termination = (
        zero_time_termination if isinstance(zero_time_termination, dict) else {}
    )
    signal_number = (
        normalized_exit_signal(returncode) if remote_state == "done" else None
    )
    runner_process_provenance = simulate_result.get(
        "runner_process_provenance", {}
    )
    runner_process_provenance = (
        runner_process_provenance
        if isinstance(runner_process_provenance, dict)
        else {}
    )
    runner_attribution = str(runner_process_provenance.get("attribution") or "")
    if returncode == 0:
        source = "normal_process_exit"
    elif adaptive_termination.get("status") in {"pass", "recovered_completed_job"}:
        source = "framework_adaptive_semantic_stall_termination"
    elif zero_time_termination.get("status") in {"pass", "recovered_completed_job"}:
        source = "framework_zero_time_livelock_termination"
    elif failure_class == "remote_tool_poll_budget_exhausted":
        source = "wall_clock_poll_budget_expired"
    elif remote_state in {"lost", "missing"}:
        source = "remote_process_disappeared_without_exit_record"
    elif failure_class in {
        "remote_transport_failure",
        "remote_recovery_indeterminate",
        "remote_semantic_recovery_indeterminate",
    }:
        source = "remote_transport_indeterminate"
    elif runner_attribution == "runner_owned_simulator_process_signal_exit":
        source = "runner_owned_simulator_signal_exit"
    elif signal_number is not None:
        source = "non_framework_signal_exit"
    elif returncode is not None:
        source = "nonzero_process_exit"
    else:
        source = "unclassified_termination"

    runtime_evidence = simulation_runtime_failure_evidence(simulation_log_path)
    simulator_crash_observed = bool(
        runtime_evidence.get("simulator_crash_lines")
    )
    tail_lines = runtime_evidence.get("tail_lines", [])
    raw_terminal_tail = (
        "\n".join(str(value) for value in tail_lines)[-12_000:]
        if isinstance(tail_lines, list)
        else ""
    )
    policy = (
        progress_summary.get("policy", {})
        if isinstance(progress_summary.get("policy"), dict)
        else {}
    )
    terminal_event_seen = progress_summary.get("terminal_event_seen") is True
    live_progress = live_progress if isinstance(live_progress, dict) else {}
    live_snapshot = (
        live_progress.get("latest", {})
        if isinstance(live_progress.get("latest"), dict)
        else {}
    )
    last_committed_event = progress_summary.get("last_committed_progress_event")
    if not isinstance(last_committed_event, dict):
        last_committed_event = live_snapshot.get("last_committed_progress_event", {})
    if not isinstance(last_committed_event, dict):
        last_committed_event = {}
    observation_activity = live_snapshot.get("testbench_observation_activity", {})
    if not isinstance(observation_activity, dict):
        observation_activity = {}
    if not observation_activity and runner_process_provenance:
        observation_activity = {
            "schema_version": "spatialaccagent.testbench_observation_activity.v1",
            "runner_process_snapshot": runner_process_provenance.get(
                "last_running_process_snapshot", {}
            ),
            "testbench_observation_process": "not_observed",
            "other_testbench_file_io_callbacks": {
                "status": "not_directly_observable_from_runner",
            },
        }
    adaptive_stall_evidence = simulate_result.get(
        "adaptive_semantic_stall_evidence", {}
    )
    adaptive_stall_evidence = (
        adaptive_stall_evidence
        if isinstance(adaptive_stall_evidence, dict)
        else {}
    )
    pipeline_stall = adaptive_stall_evidence.get(
        "intra_layer_pipeline_violation_evidence", {}
    )
    pipeline_stall = pipeline_stall if isinstance(pipeline_stall, dict) else {}
    active_boundary_observation = last_committed_event.get(
        "active_boundary_observation", {}
    )
    active_boundary_observation = (
        active_boundary_observation
        if isinstance(active_boundary_observation, dict)
        else {}
    )
    proven_semantic_pipeline_stall = (
        source == "framework_adaptive_semantic_stall_termination"
        and failure_class == "adaptive_semantic_stall"
        and adaptive_stall_evidence.get("status") == "proven_semantic_stall"
        and pipeline_stall.get("status") == "proven_pipeline_violation"
        and all(
            field in active_boundary_observation
            for field in (
                "input_ready",
                "output_ready",
                "output_valid",
                "output_accept_count",
            )
        )
    )
    if terminal_event_seen:
        missing_report_cause = "terminal_event_observed"
    elif source == "normal_process_exit":
        missing_report_cause = "normal_exit_without_terminal_event"
    elif source in {
        "remote_transport_indeterminate",
        "unclassified_termination",
    }:
        missing_report_cause = "termination_indeterminate"
    else:
        missing_report_cause = "process_ended_before_terminal_event"
    complete_sources = {
        "normal_process_exit",
        "framework_adaptive_semantic_stall_termination",
        "framework_zero_time_livelock_termination",
        "wall_clock_poll_budget_expired",
        "remote_process_disappeared_without_exit_record",
        "runner_owned_simulator_signal_exit",
        "non_framework_signal_exit",
        "nonzero_process_exit",
    }
    return {
        "schema_version": "spatialaccagent.simulation_termination_provenance.v1",
        "status": "complete" if source in complete_sources else "indeterminate",
        "termination_source": source,
        "remote_state": remote_state,
        "exit_code": returncode,
        "signal_number": signal_number,
        "runner_failure_class": failure_class or None,
        "observed_duration_sec": simulate_result.get("duration_sec"),
        "wall_clock_budget": {
            "fixed_wall_clock_timeout": timeout_sec > 0,
            "configured_timeout_sec": timeout_sec if timeout_sec > 0 else None,
            "unbounded": timeout_sec <= 0,
            "expired": source == "wall_clock_poll_budget_expired",
        },
        "cycle_budget": {
            "fixed_cycle_timeout": policy.get("fixed_cycle_timeout") is True,
            "configured_cycle_limit": policy.get("cycle_limit"),
            "last_observed_cycle": progress_summary.get("last_cycle"),
        },
        "framework_termination": {
            "adaptive_semantic_stall": adaptive_termination.get("status"),
            "zero_time_livelock": zero_time_termination.get("status"),
        },
        "simulator_terminal_log": runtime_evidence,
        "raw_terminal_log_tail": raw_terminal_tail,
        "runner_process_provenance": runner_process_provenance,
        "final_committed_progress_event": last_committed_event,
        "testbench_observation_activity": observation_activity,
        "causal_classification": {
            "classification": (
                "simulator_process_crash"
                if simulator_crash_observed
                else "proven_semantic_pipeline_stall"
                if proven_semantic_pipeline_stall
                else "runner_owned_simulator_signal_exit_unattributed"
                if source == "runner_owned_simulator_signal_exit"
                else "deterministic_terminal_diagnostic_observed"
                if runtime_evidence.get("status") == "observed"
                else "external_or_unattributed_termination"
            ),
            "simulator_infrastructure_failure_proven": (
                simulator_crash_observed
            ),
            "deterministic_hdl_or_testbench_failure_proven": (
                runtime_evidence.get("status") == "observed"
                and not simulator_crash_observed
            ),
            "source_semantic_repair_eligible": proven_semantic_pipeline_stall,
        },
        "missing_completion_reports_causal_classification": missing_report_cause,
        "terminal_progress_event_seen": terminal_event_seen,
        "exact_source_replay_fingerprint_sha256": input_fingerprint_sha256,
    }


def _prepare_fresh_transfer_target(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)


def stage_checkpoint_inputs(plan: dict[str, Any], stage_dir: Path) -> list[dict[str, Any]]:
    if plan.get("enabled") is not True:
        return []
    fast_replay = plan.get("fast_replay", {})
    if isinstance(fast_replay, dict) and fast_replay.get("used") is True:
        # The simulator and state already live together in the saved remote
        # directory.  Staging local copies only adds delay and cannot affect
        # the restore command.
        return []
    checkpoint_dir = stage_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    staged: list[dict[str, Any]] = []
    write_json(checkpoint_dir / "request.json", plan.get("request", {}))
    return staged


def checkpoint_adapter_elaboration_args(
    plan: dict[str, Any],
    stage_dir: Path,
    command_cwd: Path,
) -> list[str]:
    return []


def checkpoint_adapter_compile_define_args(
    plan: dict[str, Any],
    executable: str,
) -> list[str]:
    """Enable the testbench VPI calls in every Verilog compile path.

    The VPI source/table are linked during elaboration, but the generated
    SystemVerilog testbench is normally compiled earlier by ``vlogan``.  The
    same adapter contract must therefore make the VPI call branch visible to
    every VCS Verilog compiler that can compile the testbench.
    """

    return []


def checkpoint_capture_report_errors(
    plan: dict[str, Any],
    report: dict[str, Any],
) -> list[str]:
    """Check only the native VCS save marker and its one snapshot path."""
    errors: list[str] = []
    if report.get("schema_version") != CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION:
        errors.append("checkpoint capture report schema_version is invalid")
    if report.get("status") != "pass":
        errors.append("checkpoint capture report status is not pass")
    if report.get("mode") != "cold_capture":
        errors.append("checkpoint capture report mode mismatch")
    state_artifacts = report.get("state_artifacts", [])
    native = [
        row
        for row in state_artifacts
        if isinstance(row, dict) and row.get("kind") == "native_vcs_snapshot"
    ] if isinstance(state_artifacts, list) else []
    if len(native) != 1:
        errors.append("checkpoint capture has no single native VCS snapshot")
    return errors


def same_source_checkpoint_calibration_eligibility(
    capture_report: dict[str, Any],
    state_artifacts: list[dict[str, Any]],
    *,
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    """Retired VPI calibration compatibility result.

    Native VCS save/restore has its own one-time restore confirmation.  This
    function remains only so old callers cannot route an execution back into
    the removed capsule/calibration path.
    """

    return {
        "schema_version": "spatialaccagent.native_vcs_restore_confirmation.v1",
        "status": "not_applicable",
        "eligible": False,
        "summary": "native VCS restore confirmation replaces VPI calibration",
        "blockers": [],
        "policy": {"execution_route": "native_vcs_restore_only"},
    }


def materialize_checkpoint_semantic_suffix(
    source: Path,
    destination: Path,
    *,
    anchor_sequence: int,
    anchor_cycle: int,
) -> dict[str, Any]:
    """Persist only committed semantic suffix rows used by equivalence."""

    errors: list[str] = []
    invalid_records: list[dict[str, Any]] = []
    invalid_record_count = 0
    record_count = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.unlink(missing_ok=True)
    if not source.is_file():
        return {
            "schema_version": (
                "spatialaccagent.checkpoint_semantic_suffix_materialization.v1"
            ),
            "status": "fail",
            "path": str(destination),
            "source_path": str(source),
            "source_present": False,
            "errors": [f"progress event log is missing: {source}"],
        }
    with source.open("rb") as stream, temporary.open("w", encoding="utf-8") as output:
        line_number = 0
        while True:
            raw = stream.readline()
            if not raw:
                break
            line_number += 1
            if not raw.endswith(b"\n"):
                errors.append("progress event log has a trailing partial record")
                break
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                invalid_record_count += 1
                if len(invalid_records) < 8:
                    preview = raw.rstrip(b"\n").decode(
                        "utf-8", errors="replace"
                    )
                    invalid_records.append(
                        {
                            "line_number": line_number,
                            "error": str(exc)[:500],
                            "raw_sha256": hashlib.sha256(raw).hexdigest(),
                            "raw_byte_count": len(raw),
                            "raw_preview": preview[:4096],
                            "raw_preview_truncated": len(preview) > 4096,
                        }
                    )
                errors.append("progress event log contains an invalid complete record")
                continue
            if not isinstance(row, dict):
                invalid_record_count += 1
                errors.append("progress event log contains a non-object record")
                continue
            sequence = row.get("sequence")
            cycle = row.get("cycle")
            after_anchor = (
                isinstance(sequence, int)
                and not isinstance(sequence, bool)
                and sequence >= anchor_sequence
            ) or (
                not isinstance(sequence, int)
                and isinstance(cycle, int)
                and not isinstance(cycle, bool)
                and cycle >= anchor_cycle
            )
            phase = str(row.get("phase") or "")
            if (
                not after_anchor
                or row.get("semantic_progress") is not True
                or row.get("event_kind") == "checkpoint_control"
                or phase.startswith("simulation_checkpoint_")
            ):
                continue
            output.write(
                json.dumps(
                    row,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                )
                + "\n"
            )
            record_count += 1
    if record_count == 0:
        errors.append("progress suffix contains no committed semantic records")
    if errors:
        temporary.unlink(missing_ok=True)
    else:
        temporary.replace(destination)
    return {
        "schema_version": (
            "spatialaccagent.checkpoint_semantic_suffix_materialization.v1"
        ),
        "status": "pass" if not errors else "fail",
        "path": str(destination),
        "source_path": str(source),
        "source_present": True,
        "source_sha256": sha256_file(source),
        "source_byte_count": source.stat().st_size,
        "record_count": record_count,
        "invalid_record_count": invalid_record_count,
        "invalid_records": invalid_records,
        "invalid_records_truncated": invalid_record_count > len(invalid_records),
        "byte_count": destination.stat().st_size if destination.is_file() else 0,
        "sha256": sha256_file(destination) if destination.is_file() else None,
        "errors": list(dict.fromkeys(errors)),
    }


def checkpoint_restore_real_progress_count(records: list[Any]) -> int:
    """Count hardware progress after restore, excluding checkpoint control events."""

    count = 0
    for row in records:
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase") or "")
        if (
            row.get("semantic_progress") is True
            and row.get("event_kind") == "semantic_progress"
            and not phase.startswith("simulation_checkpoint_")
        ):
            count += 1
    return count


def same_source_equivalence_progress_contract(
    base_contract: dict[str, Any],
    cold_progress_path: Path,
    capture_report: dict[str, Any],
    cold_run_result: dict[str, Any],
) -> dict[str, Any]:
    """Bind restore termination to the exact executed cold semantic suffix."""

    capture_sequence = capture_report.get("captured_sequence")
    capture_cycle = capture_report.get("captured_cycle")
    errors: list[str] = []
    if (
        not isinstance(capture_sequence, int)
        or isinstance(capture_sequence, bool)
        or not isinstance(capture_cycle, int)
        or isinstance(capture_cycle, bool)
    ):
        errors.append("capture report has no integer sequence/cycle anchor")
    expected: list[dict[str, Any]] = []
    if not cold_progress_path.is_file():
        errors.append("cold progress event log is missing")
    else:
        with cold_progress_path.open("rb") as stream:
            while True:
                raw = stream.readline()
                if not raw:
                    break
                if not raw.endswith(b"\n"):
                    errors.append("cold progress event log has a trailing partial record")
                    break
                try:
                    row = json.loads(raw)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    errors.append("cold progress event log contains an invalid record")
                    continue
                if not isinstance(row, dict):
                    errors.append("cold progress event log contains a non-object record")
                    continue
                sequence = row.get("sequence")
                cycle = row.get("cycle")
                after_anchor = bool(
                    isinstance(capture_sequence, int)
                    and isinstance(capture_cycle, int)
                    and (
                        (
                            isinstance(sequence, int)
                            and not isinstance(sequence, bool)
                            and sequence >= capture_sequence
                        )
                        or (
                            not isinstance(sequence, int)
                            and isinstance(cycle, int)
                            and not isinstance(cycle, bool)
                            and cycle >= capture_cycle
                        )
                    )
                )
                phase = str(row.get("phase") or "")
                if (
                    after_anchor
                    and row.get("semantic_progress") is True
                    and row.get("event_kind") == "semantic_progress"
                    and not phase.startswith("simulation_checkpoint_")
                ):
                    expected.append(row)
    stall = cold_run_result.get("adaptive_semantic_stall_evidence", {})
    termination = cold_run_result.get("adaptive_semantic_stall_termination", {})
    termination_evidence = (
        termination.get("evidence", {}) if isinstance(termination, dict) else {}
    )
    cold_terminal_cycle = (
        stall.get("latest_cycle")
        if isinstance(stall, dict) and isinstance(stall.get("latest_cycle"), int)
        else termination_evidence.get("latest_cycle")
        if isinstance(termination_evidence, dict)
        and isinstance(termination_evidence.get("latest_cycle"), int)
        else None
    )
    if not isinstance(cold_terminal_cycle, int):
        errors.append("cold run has no evidence-bound terminal cycle")
    if not expected:
        errors.append("cold suffix has no semantic record at or after the capture anchor")
    oracle = {
        "schema_version": "spatialaccagent.same_source_equivalence_progress_oracle.v1",
        "status": "ready" if not errors else "not_ready",
        "capture_sequence": capture_sequence,
        "capture_cycle": capture_cycle,
        "cold_terminal_cycle": cold_terminal_cycle,
        "cold_terminal": {
            "returncode": cold_run_result.get("returncode"),
            "failure_class": cold_run_result.get("failure_class"),
        },
        "expected_semantic_records": expected,
        "expected_semantic_record_count": len(expected),
        "cold_progress_path": str(cold_progress_path),
        "cold_progress_sha256": (
            sha256_file(cold_progress_path) if cold_progress_path.is_file() else None
        ),
        "errors": errors,
        "policy": {
            "exact_executed_cold_cycles_are_not_a_fixed_timeout": True,
            "first_missing_or_different_semantic_record_terminates_calibration": True,
            "full_framework_suffix_comparison_remains_mandatory": True,
        },
    }
    oracle["oracle_sha256"] = canonical_contract_sha256(
        {key: value for key, value in oracle.items() if key != "oracle_sha256"}
    )
    return {
        **(base_contract if isinstance(base_contract, dict) else {}),
        "same_source_equivalence_oracle": oracle,
    }


def framework_checkpoint_manifest(
    plan: dict[str, Any],
    capture_report: dict[str, Any],
    state_artifacts: list[dict[str, Any]],
    *,
    equivalence_report: dict[str, Any] | None = None,
    remote_workdir: str | None = None,
) -> dict[str, Any]:
    """Store the smallest reusable exact-simulator checkpoint record."""
    state_schema = capture_report.get("state_schema", {})
    state_schema = state_schema if isinstance(state_schema, dict) else {}
    identity = plan.get("execution_identity", {})
    identity = identity if isinstance(identity, dict) else {}
    cut = plan.get("request", {}).get("semantic_cut", {})
    cut = cut if isinstance(cut, dict) else {}
    checkpoint_projection = {
        "execution_identity": identity,
        "semantic_cut": cut,
        "state_artifacts": [
            {
                key: row.get(key)
                for key in ("path", "kind", "byte_count")
            }
            for row in state_artifacts
            if isinstance(row, dict)
        ],
        "remote_workdir": remote_workdir,
    }
    state_bytes = sum(
        int(row.get("byte_count") or 0)
        for row in state_artifacts
        if isinstance(row, dict)
    )
    return {
        "schema_version": CHECKPOINT_MANIFEST_SCHEMA_VERSION,
        "status": "pass",
        "checkpoint_id": canonical_contract_sha256(checkpoint_projection),
        "created_at_unix_sec": time.time(),
        "execution_identity": identity,
        "semantic_cut": cut,
        "state_schema": state_schema,
        "state_artifacts": state_artifacts,
        "total_state_bytes": state_bytes,
        "remote_acknowledgment_status": "pending",
        "remote_workdir": remote_workdir,
        "capture_report": capture_report,
    }

def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def persist_zero_time_livelock_recovery(
    run_dir: Path,
    simulate_result: dict[str, Any],
    *,
    remote_workdir: str,
    input_fingerprint_sha256: str,
) -> bool:
    """Persist a fresh, exact-job zero-time termination for later recovery."""

    evidence = simulate_result.get("zero_time_livelock_evidence", {})
    termination = simulate_result.get("zero_time_livelock_termination", {})
    live_snapshot = read_json(
        run_dir / "verification" / "vcs" / "live" / "live_progress.json"
    )
    if not (
        simulate_result.get("status") == "fail"
        and simulate_result.get("returncode") == ZERO_TIME_LIVELOCK_EXIT_CODE
        and simulate_result.get("remote_workdir") == remote_workdir
        and live_snapshot.get("input_fingerprint_sha256")
        == input_fingerprint_sha256
        and live_snapshot.get("remote_workdir") == remote_workdir
        and isinstance(evidence, dict)
        and evidence.get("schema_version")
        == "spatialaccagent.zero_time_livelock_evidence.v1"
        and evidence.get("status") == "proven_zero_time_livelock"
        and evidence.get("remote_workdir") == remote_workdir
        and live_snapshot.get("zero_time_livelock_evidence") == evidence
        and isinstance(termination, dict)
        and termination.get("schema_version")
        == "spatialaccagent.zero_time_livelock_termination.v1"
        and termination.get("status") == "pass"
        and termination.get("remote_exit_code")
        == ZERO_TIME_LIVELOCK_EXIT_CODE
        and termination.get("remote_workdir") == remote_workdir
        and termination.get("evidence") == evidence
    ):
        return False

    write_json(
        run_dir
        / "verification"
        / "vcs"
        / "live"
        / "zero_time_livelock_recovery.json",
        {
            "schema_version": "spatialaccagent.zero_time_livelock_recovery.v1",
            "input_fingerprint_sha256": input_fingerprint_sha256,
            "remote_workdir": remote_workdir,
            "evidence": evidence,
            "termination": termination,
        },
    )
    return True


def bind_zero_time_livelock_recovery(
    run_dir: Path,
    simulate_result: dict[str, Any],
    *,
    remote_workdir: str,
    input_fingerprint_sha256: str,
) -> dict[str, Any]:
    """Bind a supervised zero-time termination to its exact recovered VCS job."""

    if (
        simulate_result.get("status") != "fail"
        or simulate_result.get("returncode") != ZERO_TIME_LIVELOCK_EXIT_CODE
        or str(simulate_result.get("remote_workdir") or "") != remote_workdir
    ):
        return simulate_result

    live_dir = run_dir / "verification" / "vcs" / "live"
    live_snapshot = read_json(live_dir / "live_progress.json")
    recovery = read_json(live_dir / "zero_time_livelock_recovery.json")
    evidence = recovery.get("evidence", {})
    termination = recovery.get("termination", {})
    if not (
        recovery.get("schema_version")
        == "spatialaccagent.zero_time_livelock_recovery.v1"
        and recovery.get("input_fingerprint_sha256")
        == input_fingerprint_sha256
        and recovery.get("remote_workdir") == remote_workdir
        and live_snapshot.get("input_fingerprint_sha256")
        == input_fingerprint_sha256
        and live_snapshot.get("remote_workdir") == remote_workdir
        and isinstance(evidence, dict)
        and evidence.get("schema_version")
        == "spatialaccagent.zero_time_livelock_evidence.v1"
        and evidence.get("status") == "proven_zero_time_livelock"
        and evidence.get("remote_workdir") == remote_workdir
        and isinstance(termination, dict)
        and termination.get("schema_version")
        == "spatialaccagent.zero_time_livelock_termination.v1"
        and termination.get("status") == "pass"
        and termination.get("remote_exit_code")
        == ZERO_TIME_LIVELOCK_EXIT_CODE
        and termination.get("remote_workdir") == remote_workdir
        and termination.get("evidence") == evidence
    ):
        return simulate_result

    result = dict(simulate_result)
    result["failure_class"] = "zero_time_simulation_livelock"
    result["summary"] = (
        "remote VCS simulation was terminated after proven zero-time "
        "simulation livelock"
    )
    result["zero_time_livelock_evidence"] = evidence
    result["zero_time_livelock_termination"] = {
        key: termination.get(key)
        for key in (
            "schema_version",
            "status",
            "remote_exit_code",
            "remote_pid",
            "remote_workdir",
            "fixed_wall_clock_timeout",
            "fixed_cycle_timeout",
        )
        if key in termination
    }
    return result


def preflight_manifest_projection_sha256(manifest: dict[str, Any]) -> str:
    projection = {
        key: value
        for key, value in manifest.items()
        if key not in RUNTIME_MANIFEST_FIELDS
    }
    projection["status"] = "ready"
    return canonical_contract_sha256(projection)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_") or "run"


def verified_file(row: dict[str, Any], label: str, errors: list[str]) -> Path | None:
    path = Path(str(row.get("path") or ""))
    expected = str(row.get("sha256") or "")
    if not path.is_file():
        errors.append(f"{label} is missing: {path}")
        return None
    if not expected or sha256_file(path) != expected:
        errors.append(f"{label} hash mismatch: {path}")
        return None
    return path


def source_row(
    row: dict[str, Any],
    label: str,
    errors: list[str],
) -> dict[str, Any] | None:
    raw_path = row.get("path") or row.get("local_path")
    expected = row.get("sha256") or row.get("local_sha256")
    normalized = {
        "path": str(raw_path or ""),
        "sha256": str(expected or ""),
    }
    path = verified_file(normalized, label, errors)
    if path is None:
        return None
    return {
        "path": path.resolve(),
        "sha256": str(expected),
        "source_id": str(row.get("source_id") or ""),
        "role": str(row.get("role") or ""),
        "staged_path": row.get("staged_path"),
    }


def selected_simulation_sources(
    identity: dict[str, Any],
    errors: list[str],
) -> list[dict[str, Any]]:
    closure = identity.get("selected_simulation_source_closure")
    if isinstance(closure, dict):
        if closure.get("status") not in {None, "pass", "ready"}:
            errors.append("selected simulation source closure status is not pass")
        rows = next(
            (
                closure.get(key)
                for key in ("source_files", "sources", "files", "materialized_sources")
                if isinstance(closure.get(key), list)
            ),
            [],
        )
    elif isinstance(closure, list):
        rows = closure
    else:
        errors.append("board source identity does not declare selected_simulation_source_closure")
        rows = []

    selected: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"selected simulation source closure[{index}] is not an object")
            continue
        entry = source_row(row, f"selected simulation source closure[{index}]", errors)
        if entry is None:
            continue
        if entry["path"] in seen_paths:
            errors.append(f"selected simulation source closure repeats path: {entry['path']}")
            continue
        seen_paths.add(entry["path"])
        selected.append(entry)
    if not selected:
        errors.append("selected simulation source closure is empty")
    return selected


def is_synthesis_source(role: str, path: Path) -> bool:
    normalized_role = role.strip().lower().replace("-", "_")
    return normalized_role in SYNTHESIS_ONLY_ROLES or any(
        part.lower() == "synth" for part in path.parts
    )


def module_declarations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return re.findall(
        r"\bmodule\s+(?:automatic\s+)?([A-Za-z_][A-Za-z0-9_$]*)\b",
        text,
    )


def duplicate_module_errors(source_entries: list[dict[str, Any]]) -> list[str]:
    owners: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    def agent_owned(entry: dict[str, Any]) -> bool:
        source_id = str(entry.get("source_id") or "")
        role = str(entry.get("role") or "").lower()
        return source_id.startswith(("generated-board-source:", "certified_kernel.")) or role in {
            "compute_slot_adapter",
            "generated_kernel",
            "multilayer_harness",
            "protocol_monitor",
            "testbench",
        }

    for entry in source_entries:
        path = entry["path"]
        for module in set(module_declarations(path)):
            owner = owners.get(module)
            if owner is not None and (agent_owned(owner) or agent_owned(entry)):
                errors.append(
                    f"VCS source closure declares module {module} more than once across agent-owned sources: "
                    f"{owner['path']} and {path}"
                )
            elif owner is None:
                owners[module] = entry
    return errors


def safe_relative_path(value: Any) -> Path | None:
    path = Path(str(value or ""))
    if not path.name or path.is_absolute() or ".." in path.parts:
        return None
    return path


def supplemental_jsonl_output_paths(
    testbench_path: Path | None,
    planned_paths: set[Path],
) -> list[Path]:
    """Discover bounded testbench observation sidecars without a case-specific name."""

    if not isinstance(testbench_path, Path) or not testbench_path.is_file():
        return []
    try:
        text = testbench_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    _, literals = _systemverilog_code_and_string_literals(text)
    paths: set[Path] = set()
    for literal in literals:
        relative = safe_relative_path(literal)
        if (
            relative is not None
            and relative.suffix.lower() == ".jsonl"
            and relative.parts[0] == "reports"
            and relative not in planned_paths
        ):
            paths.add(relative)
    return sorted(paths)[:16]


MAX_SUPPLEMENTAL_VCD_BYTES = 64 * 1024 * 1024
VCS_ZERO_DELAY_LOOP_MARKERS = (
    "possible zero delay loop",
    "delta-cycles exceeded the threshold-limit",
)


def environment_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def supplemental_vcd_output_paths(testbench_path: Path | None) -> list[Path]:
    """Discover only byte-bounded VCDs declared by the current testbench."""

    if not isinstance(testbench_path, Path) or not testbench_path.is_file():
        return []
    try:
        text = testbench_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    code, literals = _systemverilog_code_and_string_literals(text)
    dump_limits = [
        int(match.group(1))
        for match in re.finditer(r"\$dumplimit\s*\(\s*(\d+)\s*\)", code)
    ]
    if not any(0 < value <= MAX_SUPPLEMENTAL_VCD_BYTES for value in dump_limits):
        return []
    paths = {
        relative
        for literal in literals
        if (relative := safe_relative_path(literal)) is not None
        and relative.suffix.lower() == ".vcd"
        and relative.parts[0] == "reports"
    }
    return sorted(paths)[:4]


def vcd_time_summary(payload: bytes) -> dict[str, Any]:
    timestamps = [
        int(match.group(1))
        for match in re.finditer(rb"(?m)^#(\d+)\s*$", payload)
    ]
    header = payload[: min(len(payload), 256 * 1024)].decode(
        "utf-8", errors="replace"
    )
    timescale_match = re.search(
        r"\$timescale\s+(.+?)\s+\$end", header, flags=re.DOTALL
    )
    variable_rows = []
    for match in re.finditer(
        r"\$var\s+\S+\s+(\d+)\s+(\S+)\s+(.+?)\s+\$end",
        header,
    ):
        variable_rows.append(
            {
                "width": int(match.group(1)),
                "identifier": match.group(2),
                "reference": match.group(3).strip(),
            }
        )
    recent_payload = payload[payload.rfind(b"\n#", 0, max(len(payload) - 1, 0)) :]
    recent_identifiers: set[str] = set()
    for raw_line in recent_payload.splitlines():
        line = raw_line.decode("utf-8", errors="replace").strip()
        if re.fullmatch(r"[01xXzZ]\S+", line):
            recent_identifiers.add(line[1:])
        elif re.fullmatch(r"[bBrR][^ ]+\s+\S+", line):
            recent_identifiers.add(line.rsplit(maxsplit=1)[-1])
    recent_variables = [
        row for row in variable_rows if row["identifier"] in recent_identifiers
    ][:64]
    return {
        "status": "ready" if timestamps else "no_timestamp",
        "timescale": " ".join(timescale_match.group(1).split())
        if timescale_match
        else None,
        "variable_count": len(variable_rows),
        "timestamp_count": len(timestamps),
        "first_timestamp": timestamps[0] if timestamps else None,
        "previous_timestamp": timestamps[-2] if len(timestamps) >= 2 else None,
        "last_timestamp": timestamps[-1] if timestamps else None,
        "simulation_time_advanced": bool(
            len(timestamps) >= 2 and timestamps[-1] > timestamps[-2]
        ),
        "recent_changed_variables": recent_variables,
    }


def summarize_supplemental_vcd(path: Path) -> dict[str, Any]:
    byte_count = path.stat().st_size
    if byte_count > MAX_SUPPLEMENTAL_VCD_BYTES:
        return {
            "status": "too_large",
            "byte_count": byte_count,
            "maximum_byte_count": MAX_SUPPLEMENTAL_VCD_BYTES,
        }
    return {
        **vcd_time_summary(path.read_bytes()),
        "byte_count": byte_count,
        "maximum_byte_count": MAX_SUPPLEMENTAL_VCD_BYTES,
    }


def summarize_vcs_loop_report(path: Path) -> dict[str, Any]:
    byte_count = path.stat().st_size
    with path.open("rb") as stream:
        head = stream.read(6000)
        if byte_count > 6000:
            stream.seek(max(0, byte_count - 6000))
            tail = stream.read(6000)
        else:
            tail = b""
    bounded = head + tail
    text = bounded.decode("utf-8", errors="replace")
    lower = text.lower()
    markers = [marker for marker in VCS_ZERO_DELAY_LOOP_MARKERS if marker in lower]
    return {
        "status": "ready",
        "native_loop_detected": bool(markers or byte_count),
        "matched_markers": markers,
        "excerpt": text,
    }


def _flatten_scalar_record(value: Any) -> dict[str, Any]:
    flattened: dict[str, Any] = {}

    def visit(item: Any, prefix: str, depth: int) -> None:
        if len(flattened) >= 128 or depth > 4:
            return
        if item is None or isinstance(item, (bool, int, float, str)):
            if prefix:
                flattened[prefix] = item
            return
        if isinstance(item, dict):
            for key, child in item.items():
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                visit(child, child_prefix, depth + 1)

    visit(value, "", 0)
    return flattened


def summarize_supplemental_jsonl(path: Path) -> dict[str, Any]:
    parsed = read_complete_jsonl(path)
    records = [
        row for row in parsed.get("records", []) if isinstance(row, dict)
    ]
    scalar_records = [_flatten_scalar_record(row) for row in records]
    return {
        "status": "ready" if records else "empty",
        "record_count": len(records),
        "invalid_record_count": len(parsed.get("invalid_records", [])),
        "trailing_partial_byte_count": int(
            parsed.get("trailing_partial_byte_count") or 0
        ),
        "schema_versions": sorted(
            {str(row.get("schema_version")) for row in records if row.get("schema_version")}
        ),
        "probe_ids": sorted(
            {str(row.get("probe_id")) for row in records if row.get("probe_id")}
        ),
        "probe_revisions": sorted(
            {
                int(row.get("probe_revision"))
                for row in records
                if isinstance(row.get("probe_revision"), int)
            }
        ),
        "first_scalar_record": scalar_records[0] if scalar_records else {},
        "last_scalar_record": scalar_records[-1] if scalar_records else {},
        "tail_scalar_records": scalar_records[-16:],
    }


def read_boundary_trace_records(path: Path) -> dict[str, Any]:
    """Read the boundary trace in either the current JSONL or JSON form."""

    if path.suffix.lower() == ".jsonl":
        return read_complete_jsonl(path)
    try:
        parsed_value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        parsed_value = None
    rows = (
        parsed_value.get("boundary_trace")
        if isinstance(parsed_value, dict)
        else parsed_value
    )
    if not isinstance(rows, list):
        return {
            "status": "invalid",
            "records": [],
            "invalid_records": [{"error": "boundary trace is not a list"}],
            "trailing_partial_byte_count": 0,
        }
    return {
        "status": "ready",
        "records": [row for row in rows if isinstance(row, dict)],
        "invalid_records": [],
        "trailing_partial_byte_count": 0,
    }


def summarize_boundary_trace_observations(
    path: Path,
    semantic_manifest_reference: dict[str, Any],
    testbench: dict[str, Any],
    simulation_log_path: Path | None = None,
) -> dict[str, Any]:
    """Create bounded current-DAG evidence for SACG/CCTG and repair."""

    parsed = read_boundary_trace_records(path)
    records = list(parsed.get("records", []))
    pipeline_log = (
        read_pipeline_trace_log(simulation_log_path)
        if simulation_log_path is not None
        else {"status": "not_requested", "records": [], "unparsed": 0}
    )
    records.extend(pipeline_log.get("records", []))
    semantic_path = Path(str(semantic_manifest_reference.get("path") or ""))
    semantic_manifest = read_json(semantic_path) if semantic_path.is_file() else {}
    authority = pipeline_boundary_observation_authority(
        semantic_manifest,
        semantic_manifest_path=semantic_path,
        testbench_source={
            "source_id": testbench.get("source_id"),
            "sha256": testbench.get("sha256"),
        },
    )
    summary = summarize_pipeline_boundary_observations(
        records if isinstance(records, list) else [],
        authority,
        testbench.get("debug_observability_contract")
        if isinstance(testbench, dict)
        else None,
    )
    stage_trace_records = (
        pipeline_log.get("stage_records", [])
        if isinstance(pipeline_log.get("stage_records"), list)
        else []
    )
    stage_snapshot_records = stage_internal_records_from_boundary_observations(
        records if isinstance(records, list) else [], authority
    )
    stage_internal_summary = summarize_stage_internal_observations(
        [*stage_trace_records, *stage_snapshot_records], authority
    )
    summary.update(
        {
            "trace_path": str(path),
            "trace_sha256": sha256_file(path) if path.is_file() else None,
            "trace_parse_status": parsed.get("status"),
            "trace_invalid_record_count": len(parsed.get("invalid_records", [])),
            "trace_trailing_partial_byte_count": int(
                parsed.get("trailing_partial_byte_count") or 0
            ),
            "simulation_log_trace_status": pipeline_log.get("status"),
            "simulation_log_trace_record_count": len(
                pipeline_log.get("records", [])
            ),
            "simulation_log_unparsed_trace_line_count": int(
                pipeline_log.get("unparsed") or 0
            ),
            "simulation_log_stage_trace_record_count": len(
                stage_trace_records
            ),
            "boundary_trace_stage_snapshot_record_count": len(
                stage_snapshot_records
            ),
            "simulation_log_unparsed_stage_trace_line_count": int(
                pipeline_log.get("stage_unparsed") or 0
            ),
            "stage_internal_observation_summary": stage_internal_summary,
            "plain_language_summary": (
                "按当前模型的全部数据边界统计输入、输出、是否真正传输、"
                "已接收次数以及首条和末条数据；信息不完整时不能当作通过。"
            ),
        }
    )
    return summary


def safe_relative_cwd(value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def external_fixture_staging_contract(
    manifest: dict[str, Any], errors: list[str]
) -> dict[str, Any]:
    """Validate portable, hash-bound files already admitted by board preflight."""

    fixture = manifest.get("external_simulation_fixture")
    empty = {
        "files": [],
        "runtime_files": [],
        "include_directories": {},
        "synopsys_sim_setup": None,
    }
    if fixture is None:
        return empty
    if not isinstance(fixture, dict):
        errors.append("board external_simulation_fixture is not an object")
        return empty

    fixture_path = verified_file(
        fixture, "external_simulation_fixture report", errors
    )
    if fixture_path is None:
        return empty
    fixture_report = read_json(fixture_path)
    materialized_rows = fixture_report.get("materialized_files")
    if not isinstance(materialized_rows, list):
        errors.append("external simulation fixture report has no materialized_files")
        materialized_rows = []
    source_authority: dict[str, dict[str, Any]] = {}
    artifact_authority: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(materialized_rows):
        if not isinstance(row, dict):
            errors.append(f"external fixture materialized_files[{index}] is not an object")
            continue
        source_id = str(row.get("source_id") or "")
        artifact_id = str(row.get("artifact_id") or "")
        if source_id:
            if source_id in source_authority:
                errors.append(
                    f"external fixture materialized_files repeat source_id: {source_id}"
                )
            else:
                source_authority[source_id] = row
        if artifact_id:
            if artifact_id in artifact_authority:
                errors.append(
                    f"external fixture materialized_files repeat artifact_id: {artifact_id}"
                )
            else:
                artifact_authority[artifact_id] = row

    files: list[dict[str, Any]] = []
    staged_files: dict[str, dict[str, Any]] = {}

    def resolve_file(
        row: Any, label: str, kind: str, *, stage_global: bool = True
    ) -> dict[str, Any] | None:
        if not isinstance(row, dict):
            errors.append(f"{label} is not an object")
            return None
        source_id = str(row.get("source_id") or "")
        artifact_id = str(row.get("artifact_id") or "")
        candidates = []
        if source_id and source_id in source_authority:
            candidates.append(source_authority[source_id])
        if artifact_id and artifact_id in artifact_authority:
            candidates.append(artifact_authority[artifact_id])
        unique_candidates = {
            (str(candidate.get("source_id") or ""), str(candidate.get("artifact_id") or "")):
            candidate
            for candidate in candidates
        }
        if len(unique_candidates) != 1:
            errors.append(
                f"{label} does not resolve to exactly one fixture materialized_file"
            )
            return None
        authority_row = next(iter(unique_candidates.values()))
        for field in (
            "path",
            "sha256",
            "staged_path",
            "source_id",
            "artifact_id",
            "remote_path",
        ):
            if str(row.get(field) or "") != str(authority_row.get(field) or ""):
                errors.append(f"{label}.{field} differs from fixture materialized_files")
                return None
        staged_path = safe_relative_path(authority_row.get("staged_path"))
        if staged_path is None:
            errors.append(f"{label}.staged_path is not a safe relative path")
            return None
        path = verified_file(authority_row, label, errors)
        if path is None:
            return None
        target_path = Path("sources") / staged_path
        staged_key = target_path.as_posix()
        normalized = {
            "path": path.resolve(),
            "sha256": str(authority_row.get("sha256") or ""),
            "staged_path": target_path,
            "kind": kind,
        }
        if not stage_global:
            return normalized
        existing = staged_files.get(staged_key)
        if existing is not None:
            if existing["sha256"] != normalized["sha256"]:
                errors.append(
                    f"external fixture staged path has conflicting content: {staged_key}"
                )
                return None
            return existing
        staged_files[staged_key] = normalized
        files.append(normalized)
        return normalized

    raw_setup = fixture.get("synopsys_sim_setup")
    setup_files_for_identity = (
        raw_setup.get("files", []) if isinstance(raw_setup, dict) else []
    )
    setup_source_ids = {
        str(row.get("source_id") or "")
        for row in setup_files_for_identity
        if isinstance(row, dict) and str(row.get("source_id") or "")
    }
    setup_artifact_ids = {
        str(row.get("artifact_id") or "")
        for row in setup_files_for_identity
        if isinstance(row, dict) and str(row.get("artifact_id") or "")
    }
    runtime_files: list[dict[str, Any]] = []
    runtime_rows = fixture.get("runtime_auxiliary_files", [])
    if not isinstance(runtime_rows, list):
        errors.append(
            "external_simulation_fixture.runtime_auxiliary_files is not a list"
        )
        runtime_rows = []
    for index, row in enumerate(runtime_rows):
        if isinstance(row, dict) and (
            str(row.get("source_id") or "") in setup_source_ids
            or str(row.get("artifact_id") or "") in setup_artifact_ids
        ):
            continue
        label = f"external_simulation_fixture.runtime_auxiliary_files[{index}]"
        runtime_staged_path = (
            safe_relative_path(row.get("runtime_staged_path"))
            if isinstance(row, dict)
            else None
        )
        if runtime_staged_path is None:
            errors.append(f"{label}.runtime_staged_path is not a safe relative path")
        normalized = resolve_file(
            row,
            label,
            "runtime_auxiliary_file",
            stage_global=False,
        )
        if normalized is not None and runtime_staged_path is not None:
            runtime_files.append(
                {**normalized, "runtime_staged_path": runtime_staged_path}
            )

    include_directories: dict[str, Path] = {}
    include_paths: set[str] = set()
    raw_include_directories = fixture.get("include_directories", [])
    if not isinstance(raw_include_directories, list):
        errors.append("external_simulation_fixture.include_directories is not a list")
        raw_include_directories = []
    for index, row in enumerate(raw_include_directories):
        label = f"external_simulation_fixture.include_directories[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} is not an object")
            continue
        include_dir_id = str(row.get("include_dir_id") or "").strip()
        staged_root = safe_relative_path(row.get("staged_path"))
        if not include_dir_id or include_dir_id in include_directories:
            errors.append(f"{label}.include_dir_id is missing or duplicated")
        if staged_root is None:
            errors.append(f"{label}.staged_path is not a safe relative path")
        elif staged_root.as_posix() in include_paths:
            errors.append(f"{label}.staged_path is duplicated")
        else:
            include_paths.add(staged_root.as_posix())
        member_source_ids = row.get("member_source_ids")
        if (
            not isinstance(member_source_ids, list)
            or not member_source_ids
            or not all(isinstance(value, str) and value for value in member_source_ids)
            or len(member_source_ids) != len(set(member_source_ids))
        ):
            errors.append(f"{label}.member_source_ids must be a non-empty unique string list")
            member_source_ids = []
        if include_dir_id and include_dir_id not in include_directories and staged_root is not None:
            include_directories[include_dir_id] = Path("sources") / staged_root
        for member_index, source_id in enumerate(member_source_ids):
            authority_row = source_authority.get(source_id)
            if authority_row is None:
                errors.append(
                    f"{label}.member_source_ids[{member_index}] is not a materialized fixture source"
                )
                continue
            member_staged_path = safe_relative_path(authority_row.get("staged_path"))
            if member_staged_path is None or member_staged_path.parent != staged_root:
                errors.append(
                    f"{label}.member_source_ids[{member_index}] is outside the declared staged include directory"
                )
                continue
            resolve_file(authority_row, f"{label}.member_source_ids[{member_index}]", "include_file")

    staged_synopsys_setup: Path | None = None
    setup = raw_setup
    if setup is not None:
        if not isinstance(setup, dict):
            errors.append("external_simulation_fixture.synopsys_sim_setup is not an object")
        else:
            setup_files = setup.get("files")
            if not isinstance(setup_files, list) or not setup_files:
                errors.append(
                    "external_simulation_fixture.synopsys_sim_setup.files must be a non-empty list"
                )
                setup_files = []
            setup_remote_path = str(setup.get("remote_path") or "")
            main_rows: list[dict[str, Any]] = []
            for index, row in enumerate(setup_files):
                normalized = resolve_file(
                    row,
                    f"external_simulation_fixture.synopsys_sim_setup.files[{index}]",
                    "synopsys_sim_setup",
                )
                if (
                    normalized is not None
                    and isinstance(row, dict)
                    and str(row.get("remote_path") or "") == setup_remote_path
                ):
                    main_rows.append(normalized)
            if len(main_rows) != 1:
                errors.append(
                    "external_simulation_fixture.synopsys_sim_setup does not identify exactly one staged root setup file"
                )
            else:
                main = main_rows[0]
                for field, expected in (
                    ("path", str(main["path"])),
                    ("sha256", main["sha256"]),
                    (
                        "staged_path",
                        main["staged_path"].relative_to("sources").as_posix(),
                    ),
                ):
                    actual = str(setup.get(field) or "")
                    if actual != expected:
                        errors.append(
                            f"external_simulation_fixture.synopsys_sim_setup.{field} does not bind its staged root file"
                        )
                staged_synopsys_setup = main["staged_path"]

    return {
        "files": files,
        "runtime_files": runtime_files,
        "include_directories": include_directories,
        "synopsys_sim_setup": staged_synopsys_setup,
    }


def sample_runtime_auxiliary_contract(
    manifest: dict[str, Any], errors: list[str]
) -> list[dict[str, Any]]:
    rows = manifest.get("sample_runtime_auxiliary_files", [])
    if not isinstance(rows, list):
        errors.append("board sample_runtime_auxiliary_files is not a list")
        return []
    normalized: list[dict[str, Any]] = []
    by_runtime_path: dict[str, str] = {}
    for index, row in enumerate(rows):
        label = f"sample_runtime_auxiliary_files[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} is not an object")
            continue
        path = verified_file(row, label, errors)
        runtime_staged_path = safe_relative_path(row.get("runtime_staged_path"))
        if runtime_staged_path is None:
            errors.append(f"{label}.runtime_staged_path is not a safe relative path")
        if path is None or runtime_staged_path is None:
            continue
        digest = str(row.get("sha256") or "")
        runtime_key = runtime_staged_path.as_posix()
        existing_hash = by_runtime_path.get(runtime_key)
        if existing_hash is not None:
            if existing_hash != digest:
                errors.append(
                    f"sample runtime auxiliary path has conflicting content: {runtime_key}"
                )
            continue
        by_runtime_path[runtime_key] = digest
        normalized.append(
            {
                "path": path.resolve(),
                "sha256": digest,
                "runtime_staged_path": runtime_staged_path,
                "kind": "sample_runtime_auxiliary_file",
            }
        )
    return normalized


def explicit_work_library(
    argv: list[str | dict[str, str]], label: str, errors: list[str]
) -> str:
    indexes = [index for index, token in enumerate(argv) if token == "-work"]
    if len(indexes) != 1:
        errors.append(f"{label} must contain exactly one explicit -work <library>")
        return ""
    index = indexes[0]
    library = argv[index + 1] if index + 1 < len(argv) else None
    if not isinstance(library, str) or re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_$.-]*", library
    ) is None:
        errors.append(f"{label} has an unsafe or missing explicit -work library")
        return ""
    return library


def validated_vcs_compile_plan(
    manifest: dict[str, Any],
    preflight: dict[str, Any],
    verified_source_ids: set[str],
    verified_include_dir_ids: set[str],
    configured_tool: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    plan = manifest.get("vcs_compile_plan")
    if not isinstance(plan, dict):
        errors.append("board simulation vcs_compile_plan is missing")
        return {}
    if plan.get("schema_version") != VCS_COMPILE_PLAN_SCHEMA_VERSION:
        errors.append("board simulation vcs_compile_plan schema_version is invalid")
    if plan.get("status") != "ready":
        errors.append("board simulation vcs_compile_plan status is not ready")

    plan_sha256 = canonical_contract_sha256(plan)
    if manifest.get("vcs_compile_plan_sha256") != plan_sha256:
        errors.append("board simulation vcs_compile_plan_sha256 does not match the complete plan")
    if preflight.get("vcs_compile_plan_sha256") != plan_sha256:
        errors.append("exact board preflight did not verify this vcs_compile_plan hash")

    top_module = str(plan.get("top_module") or "")
    output = safe_relative_path(plan.get("output"))
    if not top_module or top_module != str(manifest.get("top_module") or ""):
        errors.append("vcs_compile_plan top_module differs from the board simulation top_module")
    if output is None:
        errors.append("vcs_compile_plan output is not a safe relative path")

    tool_binding = plan.get("tool_binding")
    if not isinstance(tool_binding, dict):
        errors.append("vcs_compile_plan tool_binding is missing")
    else:
        expected_tool = dict(configured_tool)
        expected_tool["port"] = int(configured_tool.get("port") or 22)
        for field in ("role", "name", "host", "port", "executable"):
            if tool_binding.get(field) != expected_tool.get(field):
                errors.append(f"vcs_compile_plan tool_binding differs from tool profile: {field}")
    authority = plan.get("compile_authority")
    if not isinstance(authority, dict):
        errors.append("vcs_compile_plan compile_authority is missing")

    commands = plan.get("ordered_commands")
    if not isinstance(commands, list) or not commands:
        errors.append("vcs_compile_plan ordered_commands is empty")
        return {}
    resolved_commands: list[dict[str, Any]] = []
    covered_source_ids: list[str] = []
    elaboration_indexes: list[int] = []
    allowed_command_fields = {
        "order",
        "phase",
        "tool_role",
        "executable",
        "argv",
        "source_ids",
        "cwd",
        "env",
        "shell",
        "authority_refs",
    }
    for index, raw in enumerate(commands):
        label = f"vcs_compile_plan.ordered_commands[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{label} is not an object")
            continue
        unknown_fields = sorted(set(raw) - allowed_command_fields)
        if unknown_fields:
            errors.append(f"{label} contains unsupported fields: {unknown_fields}")
        if raw.get("order") != index or isinstance(raw.get("order"), bool):
            errors.append(f"{label}.order is not the contiguous execution order")
        phase = str(raw.get("phase") or "")
        if phase not in {"compile", "elaborate"}:
            errors.append(f"{label}.phase is invalid")
        if phase == "elaborate":
            elaboration_indexes.append(index)
        if raw.get("shell") is not False:
            errors.append(f"{label}.shell must be false")
        tool_role = str(raw.get("tool_role") or "")
        executable = raw.get("executable")
        if not tool_role:
            errors.append(f"{label}.tool_role is missing")
        elif tool_role != str(configured_tool.get("role") or ""):
            errors.append(f"{label}.tool_role differs from the configured simulator role")
        if (
            not isinstance(executable, str)
            or not executable
            or "\x00" in executable
            or "\n" in executable
        ):
            errors.append(f"{label}.executable is invalid")

        cwd = safe_relative_cwd(raw.get("cwd"))
        if cwd is None:
            errors.append(f"{label}.cwd is not a safe relative directory")
        env = raw.get("env")
        if not isinstance(env, dict):
            errors.append(f"{label}.env is not an object")
            env = {}
        elif any(
            re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(key)) is None
            or not isinstance(value, str)
            or "\x00" in value
            or "\n" in value
            for key, value in env.items()
        ):
            errors.append(f"{label}.env contains an invalid name or value")

        authority_refs = raw.get("authority_refs")
        if (
            not isinstance(authority_refs, list)
            or not authority_refs
            or not all(isinstance(value, str) and value for value in authority_refs)
        ):
            errors.append(f"{label}.authority_refs is empty or invalid")

        argv = raw.get("argv")
        if not isinstance(argv, list) or not argv:
            errors.append(f"{label}.argv is empty")
            argv = []
        source_tokens: list[str] = []
        include_tokens: list[str] = []
        normalized_argv: list[str | dict[str, str]] = []
        for token_index, token in enumerate(argv):
            if isinstance(token, str):
                if not token or "\x00" in token or "\n" in token:
                    errors.append(f"{label}.argv[{token_index}] is an invalid literal token")
                normalized_argv.append(token)
                continue
            if isinstance(token, dict) and set(token) == {"source_id"}:
                source_id = token.get("source_id")
                if not isinstance(source_id, str) or not source_id:
                    errors.append(f"{label}.argv[{token_index}].source_id is invalid")
                    continue
                source_tokens.append(source_id)
                normalized_argv.append({"source_id": source_id})
                continue
            if isinstance(token, dict) and set(token) == {"include_dir_id"}:
                include_dir_id = token.get("include_dir_id")
                if (
                    not isinstance(include_dir_id, str)
                    or not include_dir_id
                    or include_dir_id not in verified_include_dir_ids
                ):
                    errors.append(
                        f"{label}.argv[{token_index}].include_dir_id is unknown or invalid"
                    )
                    continue
                include_tokens.append(include_dir_id)
                normalized_argv.append({"include_dir_id": include_dir_id})
                continue
            errors.append(
                f"{label}.argv[{token_index}] is not a literal, source_id, or include_dir_id token"
            )
        declared_source_ids = raw.get("source_ids")
        if not isinstance(declared_source_ids, list) or declared_source_ids != source_tokens:
            errors.append(f"{label}.source_ids does not exactly match argv source tokens in order")
        if phase == "elaborate" and source_tokens:
            errors.append(f"{label} elaboration command must not compile source tokens")
        if phase == "elaborate" and include_tokens:
            errors.append(f"{label} elaboration command must not contain include-dir tokens")
        work_library = (
            explicit_work_library(normalized_argv, label, errors)
            if phase == "compile"
            else ""
        )
        covered_source_ids.extend(source_tokens)
        resolved_commands.append(
            {
                "phase": phase,
                "tool_role": tool_role,
                "executable": executable,
                "argv": normalized_argv,
                "source_ids": source_tokens,
                "include_dir_ids": include_tokens,
                "work_library": work_library,
                "cwd": cwd,
                "env": env,
            }
        )

    if elaboration_indexes != [len(commands) - 1]:
        errors.append("vcs_compile_plan must end with exactly one elaboration command")
    elif output is not None:
        elaboration_literals = [
            token
            for token in resolved_commands[-1]["argv"]
            if isinstance(token, str)
        ]
        if top_module not in elaboration_literals:
            errors.append("vcs_compile_plan elaboration argv does not contain top_module")
        if output.as_posix() not in elaboration_literals:
            errors.append("vcs_compile_plan elaboration argv does not contain output")
    if (
        len(covered_source_ids) != len(verified_source_ids)
        or len(set(covered_source_ids)) != len(covered_source_ids)
        or set(covered_source_ids) != verified_source_ids
    ):
        errors.append(
            "vcs_compile_plan source tokens do not cover each preflight-verified compile source ID exactly once"
        )
    declared_compile_order = manifest.get("compile_source_ids")
    if (
        not isinstance(declared_compile_order, list)
        or not all(isinstance(value, str) and value for value in declared_compile_order)
        or covered_source_ids != declared_compile_order
    ):
        errors.append(
            "vcs_compile_plan source token order does not exactly match manifest compile_source_ids"
        )
    return {
        "plan": plan,
        "sha256": plan_sha256,
        "top_module": top_module,
        "output": output,
        "commands": resolved_commands,
    }


def execution_output_plan(
    manifest: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    raw = manifest.get("execution_outputs")
    if not isinstance(raw, dict):
        errors.append("board simulation execution_outputs is missing")
        return {}
    plan: dict[str, Any] = {}
    for key in (
        "compile_log",
        "simulation_log",
        "progress_event_log",
        "elaborated_hierarchy_report",
        "pipeline_overlap_report",
    ):
        row = raw.get(key) if isinstance(raw.get(key), dict) else {}
        path = safe_relative_path(row.get("path"))
        schema_version = str(row.get("schema_version") or "")
        if path is None or (
            (key.endswith("_report") or key == "progress_event_log")
            and not schema_version
        ):
            errors.append(f"board simulation execution_outputs.{key} is invalid")
            continue
        if (
            key == "progress_event_log"
            and schema_version != BOARD_PROGRESS_EVENT_SCHEMA_VERSION
        ):
            errors.append(
                "board simulation execution_outputs.progress_event_log has an unsupported schema_version"
            )
            continue
        plan[key] = {"path": path, "schema_version": schema_version}
    runtime_binding = manifest.get("runtime_constant_binding")
    if isinstance(runtime_binding, dict) and runtime_binding.get("enabled") is True:
        row = (
            raw.get("runtime_loader_report")
            if isinstance(raw.get("runtime_loader_report"), dict)
            else {}
        )
        path = safe_relative_path(row.get("path"))
        schema_version = str(row.get("schema_version") or "")
        if path is None or not schema_version:
            errors.append(
                "board simulation execution_outputs.runtime_loader_report is invalid"
            )
        else:
            plan["runtime_loader_report"] = {
                "path": path,
                "schema_version": schema_version,
            }
    performance_row = (
        raw.get("performance_counter_report")
        if isinstance(raw.get("performance_counter_report"), dict)
        else {}
    )
    if performance_row:
        path = safe_relative_path(performance_row.get("path"))
        schema_version = str(performance_row.get("schema_version") or "")
        if path is None or not schema_version:
            errors.append(
                "board simulation execution_outputs.performance_counter_report is invalid"
            )
        else:
            plan["performance_counter_report"] = {
                "path": path,
                "schema_version": schema_version,
            }
    protocol_rows = raw.get("protocol_monitor_reports", [])
    protocol: list[dict[str, Any]] = []
    if not isinstance(protocol_rows, list):
        errors.append("board simulation execution_outputs.protocol_monitor_reports is not a list")
        protocol_rows = []
    seen_interfaces: set[str] = set()
    seen_paths: set[Path] = set()
    for index, row in enumerate(protocol_rows):
        row = row if isinstance(row, dict) else {}
        interface = str(row.get("interface") or "")
        path = safe_relative_path(row.get("path"))
        schema_version = str(row.get("schema_version") or "")
        if not interface or interface in seen_interfaces or path is None or path in seen_paths or not schema_version:
            errors.append(f"board simulation execution_outputs.protocol_monitor_reports[{index}] is invalid")
            continue
        seen_interfaces.add(interface)
        seen_paths.add(path)
        protocol.append({"interface": interface, "path": path, "schema_version": schema_version})
    if not protocol:
        errors.append("board simulation execution_outputs has no protocol monitor reports")
    plan["protocol_monitor_reports"] = protocol
    planned_paths = [
        row["path"]
        for key, row in plan.items()
        if key != "protocol_monitor_reports" and isinstance(row, dict) and isinstance(row.get("path"), Path)
    ] + [row["path"] for row in protocol]
    if len(planned_paths) != len(set(planned_paths)):
        errors.append("board simulation execution output paths are not unique")
    reserved = {
        Path("board_simulation_manifest.json"),
        Path("board_simulation_executed_manifest.json"),
        Path("vcs_stage.tar.gz"),
    }
    if set(planned_paths).intersection(reserved):
        errors.append("board simulation execution output path would overwrite a control manifest")
    return plan


def structured_monitor_specs(
    manifest: dict[str, Any],
    outputs: dict[str, Any],
    errors: list[str],
) -> list[dict[str, Any]]:
    contract = (
        manifest.get("protocol_monitor_contract")
        if isinstance(manifest.get("protocol_monitor_contract"), dict)
        else {}
    )
    monitors = contract.get("monitors", []) if isinstance(contract.get("monitors"), list) else []
    planned = {
        str(row.get("interface") or ""): row
        for row in outputs.get("protocol_monitor_reports", [])
        if isinstance(row, dict)
    }
    specs: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_paths: set[Path] = set()
    for index, monitor in enumerate(monitors):
        if not isinstance(monitor, dict):
            errors.append(f"protocol monitor contract monitors[{index}] is not an object")
            continue
        monitor_id = str(monitor.get("monitor_id") or "")
        interface = str(monitor.get("interface") or "")
        report = monitor.get("structured_report") if isinstance(monitor.get("structured_report"), dict) else {}
        planned_report = planned.get(interface, {})
        remote_path = planned_report.get("path")
        schema_version = str(planned_report.get("schema_version") or "")
        required_fields = report.get("required_fields", [])
        if not monitor_id or monitor_id in seen_ids:
            errors.append(f"protocol monitor contract monitors[{index}] has a missing or duplicate monitor_id")
        if remote_path is None or remote_path in seen_paths:
            errors.append(f"protocol monitor contract monitors[{index}] has an unsafe or duplicate report path")
        if not schema_version or not isinstance(required_fields, list):
            errors.append(f"protocol monitor contract monitors[{index}] report schema/required_fields are missing")
        if (
            monitor_id
            and monitor_id not in seen_ids
            and remote_path is not None
            and remote_path not in seen_paths
            and schema_version
            and isinstance(required_fields, list)
        ):
            specs.append(
                {
                    "monitor_id": monitor_id,
                    "interface": interface,
                    "remote_path": remote_path,
                    "schema_version": schema_version,
                    "required_fields": sorted({str(value) for value in required_fields if str(value)}),
                }
            )
        if monitor_id:
            seen_ids.add(monitor_id)
        if remote_path is not None:
            seen_paths.add(remote_path)
    declared_interfaces = {str(row.get("interface") or "") for row in specs}
    if declared_interfaces != set(planned):
        errors.append("protocol monitor contract and execution output interfaces do not match exactly")
    if not specs:
        errors.append("protocol monitor contract has no structured monitor reports")
    return specs


def validate_manifest(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    manifest_path = run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
    identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
    semantic_path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    binding_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
    accelerator_catalog_path = run_dir / "verification" / "model_weights" / "transformer_block_weight_catalog.json"
    manifest = read_json(manifest_path)
    identity = read_json(identity_path)
    semantic = read_json(semantic_path)
    binding = read_json(binding_path)
    accelerator_catalog = read_json(accelerator_catalog_path)
    errors: list[str] = []
    identity_sha256 = sha256_file(identity_path) if identity_path.is_file() else None
    exact_board_preflight = validate_exact_board_preflight(identity_path, manifest_path)
    exact_board_preflight_passed = exact_board_preflight.get("status") == "pass"
    if not exact_board_preflight_passed:
        errors.extend(
            f"exact board preflight: {error}"
            for error in exact_board_preflight.get("blockers", [])
            if str(error)
        )
    if manifest.get("status") not in {"ready", "pass"}:
        errors.append("board simulation preflight manifest status is not ready/pass")
    identity_passed = (
        identity.get("status") == "pass"
        and identity.get("exact_user_sample_wrapper") is True
        and exact_board_preflight_passed
    )
    if not identity_passed:
        errors.append("exact sample-project wrapper identity is not pass")
    source_identity_bound = bool(
        identity_sha256 and manifest.get("source_identity_sha256") == identity_sha256
    )
    if not source_identity_bound:
        errors.append("board simulation manifest does not bind the current sample-source identity hash")
    if semantic.get("status") != "ready":
        errors.append("semantic testbench/reference vectors are not ready")
    board_vectors = semantic.get("board", {}) if isinstance(semantic.get("board"), dict) else {}
    model_layer_count = int(
        board_vectors.get("model_layer_count")
        or accelerator_catalog.get("target_layer_count")
        or 0
    )
    declared_target_layers = board_vectors.get("expected_target_layers")
    if declared_target_layers is None:
        # Historical full-model semantic fixtures predate the explicit board
        # scope fields. Their board manifest remains the workload authority.
        declared_target_layers = manifest.get("target_layer_count")
    target_layer_count = int(declared_target_layers or 0)
    validation_layer_indices = board_vectors.get("validation_layer_indices")
    if validation_layer_indices is None:
        validation_layer_indices = list(range(target_layer_count))
    if (
        model_layer_count <= 0
        or target_layer_count <= 0
        or validation_layer_indices != list(range(target_layer_count))
        or target_layer_count > model_layer_count
    ):
        errors.append("semantic board validation workload is malformed")
    covers_full_model = target_layer_count == model_layer_count
    reference_captured = (
        board_vectors.get("all_target_layer_reference_captured") is True
        if covers_full_model
        else board_vectors.get("scoped_layer_reference_captured") is True
    )
    if not reference_captured:
        errors.append("board golden boundaries were not captured for the validation scope")
    all_target_layers = (
        binding.get("status") == "pass"
        and binding.get("all_target_layers") is covers_full_model
        and manifest.get("all_target_layers") is covers_full_model
    )
    if not all_target_layers:
        errors.append("DUT binding does not prove the configured board validation scope")
    if binding.get("accelerator_scope") != "transformer_blocks_only":
        errors.append("board DUT binding scope is not transformer_blocks_only")
    if binding.get("default_or_identity_weight_fallback_disabled") is not True:
        errors.append("board DUT binding does not disable default/identity weight fallback")
    catalog_tensors = [row for row in accelerator_catalog.get("tensors", []) if isinstance(row, dict)]
    catalog_tensor_hashes = {
        str(row.get("source_slice_sha256"))
        for row in catalog_tensors
        if row.get("source_slice_sha256")
    }
    scoped_catalog_rows = [
        row
        for row in catalog_tensors
        if row.get("layer_index") in validation_layer_indices
    ]
    catalog_has_explicit_layer_indices = any(
        "layer_index" in row for row in catalog_tensors
    )
    if not scoped_catalog_rows and covers_full_model and not catalog_has_explicit_layer_indices:
        # The legacy full-model catalog schema did not annotate each tensor
        # with a layer index. This is intentionally unavailable to scoped
        # validation, which must prove its exact layer coverage.
        scoped_catalog_rows = catalog_tensors
    scoped_tensor_hashes = {
        str(row.get("source_slice_sha256"))
        for row in scoped_catalog_rows
        if row.get("source_slice_sha256")
    }
    required_tensor_hashes = scoped_tensor_hashes
    catalog_ok = (
        accelerator_catalog.get("status") == "pass"
        and accelerator_catalog.get("accelerator_scope") == "transformer_blocks_only"
        and accelerator_catalog.get("scope_coverage_complete") is True
        and accelerator_catalog.get("tensor_count") == len(catalog_tensors)
        and len(catalog_tensor_hashes) == len(catalog_tensors)
    )
    if not catalog_ok:
        errors.append("complete transformer-block weight catalog is not ready")
    if not scoped_catalog_rows:
        errors.append("transformer-block weight catalog does not cover the validation scope")
    binding_hashes = {
        str(value)
        for value in (
            binding.get("board_consumed_tensor_hashes", [])
            if isinstance(binding.get("board_consumed_tensor_hashes"), list)
            else []
        )
        if str(value)
    }
    simulation_binding_hashes = {
        str(value)
        for value in (
            manifest.get("board_consumed_tensor_hashes", [])
            if isinstance(manifest.get("board_consumed_tensor_hashes"), list)
            else []
        )
        if str(value)
    }
    real_model_weights_consumed = (
        catalog_ok
        and exact_board_preflight_passed
        and binding.get("dut_consumes_bound_weights") is True
        and binding.get("scope_coverage_complete") is True
        and scoped_tensor_hashes == binding_hashes
        and scoped_tensor_hashes == simulation_binding_hashes
    )
    if not real_model_weights_consumed:
        errors.append("board DUT binding does not cover every validation-layer transformer-block tensor hash")
    if (
        int(binding.get("model_layer_count", model_layer_count) or 0) != model_layer_count
        or int(binding.get("bound_layer_count") or 0) != target_layer_count
        or binding.get("validation_layer_indices", validation_layer_indices)
        != validation_layer_indices
        or int(manifest.get("model_layer_count", model_layer_count) or 0)
        != model_layer_count
        or int(manifest.get("bound_layer_count") or 0) != target_layer_count
        or manifest.get("validation_layer_indices", validation_layer_indices)
        != validation_layer_indices
    ):
        errors.append("board DUT binding does not match the configured validation workload")

    selected_sources = selected_simulation_sources(identity, errors)
    for entry in selected_sources:
        if is_synthesis_source(entry["role"], entry["path"]):
            errors.append(f"selected simulation source closure contains synthesis source: {entry['path']}")

    source_rows = manifest.get("source_files", []) if isinstance(manifest.get("source_files"), list) else []
    source_paths: list[Path] = []
    source_entries: list[dict[str, Any]] = []
    seen_source_paths: set[Path] = set()
    for index, row in enumerate(source_rows):
        if not isinstance(row, dict):
            errors.append(f"source_files[{index}] is not an object")
            continue
        entry = source_row(row, f"source_files[{index}]", errors)
        if entry is None:
            continue
        if entry["path"] in seen_source_paths:
            errors.append(f"VCS source list repeats path: {entry['path']}")
            continue
        seen_source_paths.add(entry["path"])
        source_paths.append(entry["path"])
        source_entries.append(entry)
        if not entry["source_id"]:
            errors.append(f"source_files[{index}] source_id is missing")
        if is_synthesis_source(entry["role"], entry["path"]):
            errors.append(f"VCS source list contains synthesis source: {entry['path']}")

    manifest_keys = {(entry["path"], entry["sha256"]) for entry in source_entries}
    verified_compile_source_ids = {
        str(value)
        for value in exact_board_preflight.get("verified_compile_source_ids", [])
        if str(value)
    }
    manifest_source_order = [entry["source_id"] for entry in source_entries]
    manifest_source_ids = {source_id for source_id in manifest_source_order if source_id}
    if len(manifest_source_order) != len(manifest_source_ids):
        errors.append("VCS source list contains duplicate or missing source_id values")
    if not verified_compile_source_ids or manifest_source_ids != verified_compile_source_ids:
        errors.append(
            "VCS source list does not exactly match the preflight-verified transformed compile source IDs"
        )
    if manifest.get("compile_source_ids") != manifest_source_order:
        errors.append(
            "manifest compile_source_ids order does not exactly match source_files"
        )
    external_fixture_staging = external_fixture_staging_contract(manifest, errors)
    sample_runtime_auxiliary = sample_runtime_auxiliary_contract(manifest, errors)
    compile_plan = validated_vcs_compile_plan(
        manifest,
        exact_board_preflight,
        verified_compile_source_ids,
        set(external_fixture_staging["include_directories"]),
        tool_profile(run_dir),
        errors,
    )

    known_synthesis_keys: set[tuple[Path, str]] = set()
    materialized_rows = (
        identity.get("materialized_sources", [])
        if isinstance(identity.get("materialized_sources"), list)
        else []
    )
    identity_source_rows = (
        identity.get("source_hashes", [])
        if isinstance(identity.get("source_hashes"), list)
        else []
    )
    for row in [*materialized_rows, *identity_source_rows]:
        if not isinstance(row, dict):
            continue
        path = Path(str(row.get("local_path") or row.get("path") or ""))
        digest = str(row.get("local_sha256") or row.get("sha256") or "")
        if path.name and digest and is_synthesis_source(str(row.get("role") or ""), path):
            known_synthesis_keys.add((path.resolve(), digest))
    if manifest_keys.intersection(known_synthesis_keys):
        errors.append("VCS source list contains a sample-project synthesis source")

    testbench = manifest.get("testbench", {}) if isinstance(manifest.get("testbench"), dict) else {}
    testbench_entry = source_row(testbench, "board testbench", errors)
    testbench_path = testbench_entry["path"] if testbench_entry is not None else None
    if testbench_entry is not None and not any(
        entry["source_id"] == testbench_entry["source_id"]
        and entry["path"] == testbench_entry["path"]
        and entry["sha256"] == testbench_entry["sha256"]
        for entry in source_entries
    ):
        errors.append("board testbench is not a member of the preflight compile source set")
    checkpoint_required = (
        str(os.environ.get("SPATIALACC_CHECKPOINT_REPLAY") or "") == "1"
        or str(os.environ.get("SPATIALACC_CHECKPOINT_REQUIRED") or "") == "1"
    )
    errors.extend(
        checkpoint_hook_source_errors(
            manifest,
            testbench_path,
            checkpoint_required=checkpoint_required,
        )
    )
    errors.extend(duplicate_module_errors(source_entries))

    artifacts = manifest.get("artifacts", {}) if isinstance(manifest.get("artifacts"), dict) else {}
    artifact_paths = {}
    runtime_binding = manifest.get("runtime_constant_binding")
    runtime_enabled = (
        isinstance(runtime_binding, dict) and runtime_binding.get("enabled") is True
    )
    artifact_names = ["input", "weight_image", "expected_output"]
    if runtime_enabled:
        artifact_names.append("runtime_image")
    for name in artifact_names:
        row = artifacts.get(name, {}) if isinstance(artifacts.get(name), dict) else {}
        path = verified_file(row, f"board artifact {name}", errors)
        if path:
            artifact_paths[name] = path
    if artifacts.get("input", {}).get("sha256") != board_vectors.get("input_vector", {}).get("sha256"):
        errors.append("board testbench input does not match the target-model random input vector hash")
    if artifacts.get("expected_output", {}).get("sha256") != board_vectors.get("expected_output", {}).get("sha256"):
        errors.append("board expected output does not match the target-model transformer-block boundary vector hash")
    weight = artifacts.get("weight_image", {}) if isinstance(artifacts.get("weight_image"), dict) else {}
    reference_path = run_dir / "verification" / "model_reference" / "reference_manifest.json"
    reference = read_json(reference_path)
    if weight.get("source_checkpoint_sha256") != reference.get("weights", {}).get("source_checkpoint_sha256"):
        errors.append("board weight image does not match the target checkpoint hash")
    if weight.get("scope_coverage_complete") is not True:
        errors.append("board weight image is not complete for all target layers")
    if weight.get("accelerator_scope") != "transformer_blocks_only":
        errors.append("board weight image scope is not transformer_blocks_only")
    if weight.get("accelerator_weight_catalog_sha256") != (
        sha256_file(accelerator_catalog_path) if accelerator_catalog_path.exists() else None
    ):
        errors.append("board weight image does not bind the current transformer-block weight catalog hash")
    image_tensor_hashes = {
        str(value)
        for value in weight.get("packed_tensor_hashes", weight.get("tensor_hashes", []))
        if str(value)
    }
    complete_scope_weight_image = (
        catalog_ok
        and bool(scoped_catalog_rows)
        and weight.get("scope_coverage_complete") is True
        and weight.get("accelerator_scope") == "transformer_blocks_only"
        and required_tensor_hashes == image_tensor_hashes
    )
    if not complete_scope_weight_image:
        errors.append("board weight image does not contain every transformer-block tensor hash")

    wrapper_entries = [
        entry
        for entry in selected_sources
        if entry["role"].strip().lower() in {"wrapper", "board_wrapper", "sample_wrapper"}
    ]
    wrapper_module_declared = (
        len(wrapper_entries) == 1
        and str(identity.get("top_module") or "") in module_declarations(wrapper_entries[0]["path"])
    )
    wrapper_preserved_in_compile_set = (
        len(wrapper_entries) == 1
        and wrapper_entries[0]["source_id"] in verified_compile_source_ids
        and (wrapper_entries[0]["path"], wrapper_entries[0]["sha256"]) in manifest_keys
    )
    validation_mode = str(
        manifest.get("validation_mode") or "exact_sample_physical_ddr"
    )
    if validation_mode == "compute_slot_axi":
        slot_abi = (
            identity.get("compute_slot_abi")
            if isinstance(identity.get("compute_slot_abi"), dict)
            else {}
        )
        slot_module = str(slot_abi.get("slot_module") or "")
        slot_adapter_entries = [
            entry
            for entry in source_entries
            if entry["role"].strip().lower() == "compute_slot_adapter"
            and slot_module in module_declarations(entry["path"])
        ]
        exact_sample_wrapper_unmodified = (
            manifest.get("exact_sample_wrapper_unmodified") is True
            and identity_passed
            and source_identity_bound
            and exact_board_preflight_passed
            and wrapper_module_declared
            and len(slot_adapter_entries) == 1
            and slot_adapter_entries[0]["source_id"] in verified_compile_source_ids
            and not wrapper_preserved_in_compile_set
            and not any(
                is_synthesis_source(entry["role"], entry["path"])
                for entry in source_entries
            )
        )
    else:
        exact_sample_wrapper_unmodified = (
            manifest.get("exact_sample_wrapper_unmodified") is True
            and identity_passed
            and source_identity_bound
            and exact_board_preflight_passed
            and wrapper_preserved_in_compile_set
            and wrapper_module_declared
            and not any(
                is_synthesis_source(entry["role"], entry["path"])
                for entry in source_entries
            )
        )
    if not exact_sample_wrapper_unmodified:
        errors.append("board simulation manifest does not prove the exact sample wrapper is unmodified")

    reference_input = reference.get("input", {}) if isinstance(reference.get("input"), dict) else {}
    random_input_stimulus = (
        reference.get("status") == "ready"
        and reference_input.get("source") == "random"
        and reference_input.get("seed") is not None
        and artifacts.get("input", {}).get("sha256") == board_vectors.get("input_vector", {}).get("sha256")
    )
    if not random_input_stimulus:
        errors.append("board input is not the hash-bound reproducible random target-model stimulus")
    if not manifest.get("top_module") or not manifest.get("pass_regex"):
        errors.append("board simulation top_module/pass_regex is missing")
    for key in ("rtl_output_file", "boundary_trace_file"):
        if safe_relative_path(manifest.get(key)) is None:
            errors.append(f"board simulation {key} must be a safe path relative to the VCS stage directory")
    output_plan = execution_output_plan(manifest, errors)
    monitor_specs = structured_monitor_specs(manifest, output_plan, errors)
    vcs = manifest.get("vcs", {}) if isinstance(manifest.get("vcs"), dict) else {}
    if not isinstance(vcs.get("runtime_plusargs"), dict):
        errors.append("board simulation VCS runtime_plusargs are missing")
    resolved = {
        "manifest_path": str(manifest_path),
        "identity_path": str(identity_path),
        "semantic_path": str(semantic_path),
        "binding_path": str(binding_path),
        "accelerator_catalog_path": str(accelerator_catalog_path),
        "reference_path": str(reference_path),
        "source_paths": source_paths,
        "source_entries": source_entries,
        "artifact_paths": artifact_paths,
        "testbench_path": testbench_path,
        "structured_monitor_specs": monitor_specs,
        "execution_output_plan": output_plan,
        "vcs_compile_plan": compile_plan,
        "external_fixture_staging": external_fixture_staging,
        "sample_runtime_auxiliary": sample_runtime_auxiliary,
        "exact_board_preflight": exact_board_preflight,
        "weight_binding_evidence": {
            "binding_status": binding.get("status"),
            "binding_accelerator_scope": binding.get("accelerator_scope"),
            "binding_all_target_layers": binding.get("all_target_layers") is True,
            "required_tensor_hashes": sorted(required_tensor_hashes),
            "validation_scope_tensor_hashes": sorted(scoped_tensor_hashes),
            "binding_hashes": sorted(binding_hashes),
            "simulation_binding_hashes": sorted(simulation_binding_hashes),
            "image_tensor_hashes": sorted(image_tensor_hashes),
        },
        "evidence": {
            "exact_sample_wrapper_unmodified": exact_sample_wrapper_unmodified,
            "accelerator_scope": binding.get("accelerator_scope"),
            "all_target_layers": all_target_layers,
            "model_layer_count": model_layer_count,
            "target_layer_count": target_layer_count,
            "validation_layer_indices": validation_layer_indices,
            "real_model_weights_consumed": real_model_weights_consumed,
            "complete_scope_weight_image": complete_scope_weight_image,
            "required_transformer_block_tensor_count": len(required_tensor_hashes),
            "random_input_stimulus": random_input_stimulus,
            "source_identity_bound": source_identity_bound,
            "selected_simulation_source_count": len(selected_sources),
            "verified_compile_source_count": len(verified_compile_source_ids),
            "exact_board_preflight_passed": exact_board_preflight_passed,
        },
    }
    return manifest, resolved, errors


def tool_profile(run_dir: Path) -> dict[str, Any]:
    profile = read_json(run_dir / "input" / "tool_profile.json")
    for tool in profile.get("tools", []):
        if isinstance(tool, dict) and tool.get("role") == "functional_verification":
            return tool
    return {}


def run_command(argv: list[str], timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def transport_is_indeterminate(result: subprocess.CompletedProcess[str]) -> bool:
    text = f"{result.stdout}\n{result.stderr}".lower()
    return any(
        marker in text
        for marker in (
            "broken pipe",
            "connection closed",
            "connection refused",
            "connection reset",
            "connection timed out",
            "connection unexpectedly closed",
            "lost connection",
            "network is unreachable",
            "no route to host",
            "operation timed out",
        )
    )


def run_transfer_command(argv: list[str], timeout_sec: int) -> subprocess.CompletedProcess[str]:
    while True:
        result = run_command(argv)
        if result.returncode == 0 or timeout_sec > 0 or not transport_is_indeterminate(result):
            return result
        time.sleep(15.0)


def run_stream_transfer_command(
    argv: list[str],
    destination: Path,
    timeout_sec: int,
) -> subprocess.CompletedProcess[str]:
    """Stream a remote byte range to disk without retaining it in memory."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    while True:
        with destination.open("wb") as stream:
            raw_result = subprocess.run(
                argv,
                stdout=stream,
                stderr=subprocess.PIPE,
                check=False,
            )
        result = subprocess.CompletedProcess(
            argv,
            raw_result.returncode,
            "",
            (raw_result.stderr or b"").decode("utf-8", errors="replace"),
        )
        if result.returncode == 0 or timeout_sec > 0 or not transport_is_indeterminate(result):
            if result.returncode != 0:
                destination.unlink(missing_ok=True)
            return result
        destination.unlink(missing_ok=True)
        time.sleep(15.0)


def run_or_recover_remote_command(
    *,
    host: str,
    port: int,
    command: str,
    remote_dir: str,
    cwd: Path,
    timeout_sec: int,
    label: str,
    progress_callback: Any = None,
) -> dict[str, Any]:
    """Attach to a deterministic detached step before considering relaunch."""

    state = remote_background_job_state(
        host,
        port,
        remote_dir,
        cwd,
        label,
    )
    if state.get("certainty") != "determinate":
        return {
            "status": "fail",
            "returncode": 255,
            "failure_class": "remote_recovery_indeterminate",
            "remote_job_preserved": True,
            "remote_state_probe": state,
            "summary": "checkpoint calibration job state is indeterminate",
        }
    if state.get("state") in {"running", "done"}:
        result = wait_for_existing_remote_job(
            host,
            port,
            remote_dir,
            cwd,
            timeout_sec,
            label,
            progress_callback=progress_callback,
        )
        return {
            **result,
            "recovered_existing_job": True,
            "remote_state_probe": state,
        }
    result = run_remote_background_command(
        host,
        port,
        command,
        remote_dir,
        cwd,
        timeout_sec,
        label,
        progress_callback=progress_callback,
    )
    return {
        **result,
        "recovered_existing_job": False,
        "remote_state_probe": state,
    }


def cctg_progress_contract(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Bind a conservative live-frontier budget to completed lower-layer evidence."""

    binding = read_json(
        run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
    )
    harness = (
        binding.get("multilayer_harness")
        if isinstance(binding.get("multilayer_harness"), dict)
        else manifest.get("multilayer_harness")
        if isinstance(manifest.get("multilayer_harness"), dict)
        else {}
    )
    integration = (
        manifest.get("board_integration_contract")
        if isinstance(manifest.get("board_integration_contract"), dict)
        else binding.get("board_integration_contract")
        if isinstance(binding.get("board_integration_contract"), dict)
        else {}
    )
    scheduler = (
        integration.get("scheduler")
        if isinstance(integration.get("scheduler"), dict)
        else {}
    )
    pipeline = (
        integration.get("intra_layer_spatial_pipeline")
        if isinstance(integration.get("intra_layer_spatial_pipeline"), dict)
        else {}
    )
    stats_path = run_dir / "verification" / "single_layer" / "single_layer_sim_stats.json"
    stats = read_json(stats_path)
    cycles = stats.get("cycles")
    stats_input = stats.get("input_beats")
    stats_output = stats.get("output_beats")
    stats_expected = stats.get("expected_beats")
    target_output = (
        scheduler.get("accepted_output_beats_per_layer")
        if scheduler.get("accepted_output_beats_per_layer") is not None
        else harness.get("accepted_output_beats_per_layer")
    )
    target_input = (
        scheduler.get("accepted_input_beats_per_layer")
        if scheduler.get("accepted_input_beats_per_layer") is not None
        else harness.get("accepted_input_beats_per_layer")
        if harness.get("accepted_input_beats_per_layer") is not None
        else stats_input
    )
    certificate = harness.get("single_layer_promotion_certificate")
    certificate = certificate if isinstance(certificate, dict) else {}
    certificate_path = Path(str(certificate.get("path") or ""))
    if not certificate_path.is_absolute():
        certificate_path = (run_dir / certificate_path).resolve()
    if (
        stats.get("status") != "pass"
        or not isinstance(target_input, int)
        or isinstance(target_input, bool)
        or target_input <= 0
        or not isinstance(target_output, int)
        or isinstance(target_output, bool)
        or target_output <= 0
        or not isinstance(cycles, int)
        or isinstance(cycles, bool)
        or cycles <= 0
        or not isinstance(stats_input, int)
        or isinstance(stats_input, bool)
        or not isinstance(stats_output, int)
        or isinstance(stats_output, bool)
        or not isinstance(stats_expected, int)
        or isinstance(stats_expected, bool)
        or not certificate_path.is_file()
        or not stats_path.is_file()
    ):
        return {}
    if (
        stats_input != target_input
        or stats_output != target_output
        or stats_expected != target_output
    ):
        return {}
    elastic_pipeline_required = bool(
        pipeline.get("pipeline_semantics")
        == "elastic_rate_insensitive_token_pipeline"
        and pipeline.get("different_tokens_overlap_across_required_dataflow")
        is True
        and (
            pipeline.get("serial_leaf_execution_forbidden") is True
            or pipeline.get("serial_leaf_execution") is False
        )
        and (
            pipeline.get("enabled") is True
            or pipeline.get("preserved") is True
            or pipeline.get("status") == "ready"
        )
    )
    return {
        "schema_version": "spatialaccagent.cctg_progress_budget_contract.v1",
        "target_input_beats": target_input,
        "target_output_beats": target_output,
        "single_layer_cycles": cycles,
        "certificate_sha256": sha256_file(certificate_path),
        "single_layer_stats_sha256": sha256_file(stats_path),
        "certified_single_layer_binding_sha256": binding.get(
            "certified_single_layer_binding_sha256"
        ),
        "source_closure_sha256": (
            integration.get("source_closure_sha256")
            or (
                binding.get("exact_board_identity_hashes", {}).get(
                    "source_closure_sha256"
                )
                if isinstance(binding.get("exact_board_identity_hashes"), dict)
                else None
            )
        ),
        "intra_layer_pipeline_contract": {
            "required": elastic_pipeline_required,
            "first_output_no_later_than_final_input": True,
            "required_dataflow_edges_must_observe_different_tokens_in_flight": True,
            "heterogeneous_stage_latency_supported": True,
            "stage_turnover_gaps_are_diagnostic": True,
            "all_planned_spatial_stages_same_cycle_required": False,
            "whole_sequence_operator_barriers_forbidden": True,
            "board_integration_contract_sha256": canonical_contract_sha256(
                integration
            ),
        },
    }


class LiveProgressObserver:
    """Persist sparse, flushed progress evidence while the remote simulator runs."""

    ZERO_TIME_LIVELOCK_UNCHANGED_SNAPSHOT_LIMIT = 3

    def __init__(
        self,
        *,
        host: str,
        port: int,
        run_dir: Path,
        remote_path: Path,
        fingerprint: str,
        progress_contract: dict[str, Any] | None = None,
        remote_time_probe_paths: list[Path] | None = None,
        native_loop_report_path: Path | None = None,
        live_namespace: str = "live",
    ) -> None:
        self.host = host
        self.port = port
        self.remote_path = remote_path
        self.fingerprint = fingerprint
        self.progress_contract = (
            progress_contract if isinstance(progress_contract, dict) else {}
        )
        self.remote_time_probe_paths = tuple(remote_time_probe_paths or [])
        self.native_loop_report_path = native_loop_report_path
        namespace = safe_id(live_namespace)
        self.live_dir = run_dir / "verification" / "vcs" / namespace
        self.raw_path = self.live_dir / "progress_events.jsonl"
        self.snapshot_path = self.live_dir / "live_progress.json"
        self.history_path = self.live_dir / "live_progress_history.jsonl"
        self.epoch_path = self.live_dir / "observation_epoch.json"
        self.last_record_count = -1
        self._last_running_signature: tuple[int, int | None, int, int | None] | None = None
        self._unchanged_running_snapshot_count = 0
        self._last_simulator_cpu_ticks: int | None = None
        self._cpu_active_without_progress_snapshot_count = 0
        self.zero_time_livelock_evidence: dict[str, Any] = {}
        self._epoch: dict[str, Any] = {}
        prior = read_json(self.snapshot_path)
        if prior.get("input_fingerprint_sha256") != fingerprint:
            self._clear_epoch_files()

    def _clear_epoch_files(self) -> None:
        for path in (
            self.raw_path,
            self.snapshot_path,
            self.history_path,
            self.epoch_path,
        ):
            path.unlink(missing_ok=True)

    @staticmethod
    def _normalized_start_bytes(
        start_bytes: dict[Path, int] | None,
    ) -> dict[str, int]:
        normalized: dict[str, int] = {}
        for path, byte_count in (start_bytes or {}).items():
            relative = safe_relative_path(path)
            if relative is None or not isinstance(byte_count, int) or byte_count < 0:
                continue
            normalized[relative.as_posix()] = byte_count
        return normalized

    def begin_epoch(
        self,
        remote_dir: str,
        *,
        remote_start_byte: int,
        signal_start_bytes: dict[Path, int] | None = None,
        signal_start_metadata: dict[Path, dict[str, int]] | None = None,
    ) -> dict[str, Any]:
        """Start one fresh observation epoch before a new remote replay.

        A native restore resumes file descriptors saved in the checkpoint, so
        progress and boundary JSONL files can contain records from before the
        restore.  The byte positions below are the exclusive lower bounds for
        this run.  They are persisted so a restarted local controller attaches
        to the same epoch instead of treating old records as current evidence.
        """

        if not remote_dir:
            raise ValueError("observation epoch requires a remote work directory")
        if not isinstance(remote_start_byte, int) or remote_start_byte < 0:
            raise ValueError("observation epoch start byte must be non-negative")
        previous = read_json(self.epoch_path)
        generation = int(previous.get("generation") or 0) + 1
        self.live_dir.mkdir(parents=True, exist_ok=True)
        self._clear_epoch_files()
        normalized_starts = self._normalized_start_bytes(signal_start_bytes)
        normalized_starts.setdefault(self.remote_path.as_posix(), remote_start_byte)
        normalized_metadata: dict[str, dict[str, int]] = {}
        for path, metadata in (signal_start_metadata or {}).items():
            relative = safe_relative_path(path)
            if relative is None or not isinstance(metadata, dict):
                continue
            row = {
                key: int(metadata[key])
                for key in ("device", "inode", "byte_count")
                if isinstance(metadata.get(key), int) and metadata[key] >= 0
            }
            if {"device", "inode", "byte_count"}.issubset(row):
                normalized_metadata[relative.as_posix()] = row
        self._epoch = {
            "schema_version": "spatialaccagent.layer3_observation_epoch.v1",
            "generation": generation,
            "input_fingerprint_sha256": self.fingerprint,
            "remote_workdir": remote_dir,
            "progress_event_log": self.remote_path.as_posix(),
            "remote_start_byte": remote_start_byte,
            "signal_start_bytes": normalized_starts,
            "signal_start_metadata": normalized_metadata,
        }
        write_json(self.epoch_path, self._epoch)
        signal_binding = f"{self.fingerprint}@{remote_dir}"
        try:
            activate_live_state_slot(
                self.live_dir.parents[2],
                "signals",
                {
                    "status": "collecting",
                    "observation_epoch": self._epoch,
                    "record_count": 0,
                },
                binding=signal_binding,
            )
        except OSError:
            pass
        self.raw_path.parent.mkdir(parents=True, exist_ok=True)
        self.raw_path.write_bytes(b"")
        self.last_record_count = -1
        self._last_running_signature = None
        self._unchanged_running_snapshot_count = 0
        self._last_simulator_cpu_ticks = None
        self._cpu_active_without_progress_snapshot_count = 0
        self.zero_time_livelock_evidence = {}
        return dict(self._epoch)

    def bind_or_begin_epoch(self, remote_dir: str) -> dict[str, Any]:
        """Rebind a restarted controller to the exact active observation epoch."""

        saved = read_json(self.epoch_path)
        if (
            saved.get("input_fingerprint_sha256") == self.fingerprint
            and saved.get("remote_workdir") == remote_dir
            and isinstance(saved.get("remote_start_byte"), int)
            and int(saved["remote_start_byte"]) >= 0
        ):
            self._epoch = saved
            return dict(saved)
        return self.begin_epoch(remote_dir, remote_start_byte=0)

    def epoch(self) -> dict[str, Any]:
        return dict(self._epoch or read_json(self.epoch_path))

    def _effective_progress_start_byte(self, remote_dir: str) -> int:
        """Return the current-run start offset, even after a file is recreated."""

        start_byte = int(self._epoch.get("remote_start_byte") or 0)
        starts = self._epoch.get("signal_start_metadata", {})
        starts = starts if isinstance(starts, dict) else {}
        start_metadata = starts.get(self.remote_path.as_posix(), {})
        start_metadata = start_metadata if isinstance(start_metadata, dict) else {}
        if start_byte == 0 and not start_metadata:
            return 0
        current = remote_file_metadata(
            host=self.host,
            port=self.port,
            remote_dir=remote_dir,
            relative=self.remote_path,
            timeout_sec=60,
        )
        replaced = bool(
            current
            and (
                (
                    isinstance(start_metadata.get("device"), int)
                    and isinstance(start_metadata.get("inode"), int)
                    and (
                        current.get("device") != start_metadata.get("device")
                        or current.get("inode") != start_metadata.get("inode")
                    )
                )
                or int(current.get("byte_count") or 0) < start_byte
            )
        )
        if not replaced:
            return start_byte
        if self._epoch.get("progress_file_recreated") is not True:
            self.raw_path.parent.mkdir(parents=True, exist_ok=True)
            self.raw_path.write_bytes(b"")
            self._epoch["progress_file_recreated"] = True
            self._epoch["progress_file_metadata_after_recreate"] = current
            write_json(self.epoch_path, self._epoch)
        return 0

    def _remote_tail(
        self,
        remote_dir: str,
        relative: Path,
        local_name: str,
    ) -> bytes:
        temporary = self.live_dir / local_name
        remote_file = f"{remote_dir.rstrip('/')}/{relative.as_posix()}"
        copied = run_stream_transfer_command(
            [
                "ssh",
                "-p",
                str(self.port),
                "-o",
                "StrictHostKeyChecking=no",
                self.host,
                f"tail -c 1048576 -- {shlex.quote(remote_file)}",
            ],
            temporary,
            60,
        )
        if copied.returncode != 0 or not temporary.is_file():
            temporary.unlink(missing_ok=True)
            return b""
        payload = temporary.read_bytes()
        temporary.unlink(missing_ok=True)
        return payload

    def _simulation_time_probe(self, remote_dir: str) -> dict[str, Any]:
        probes = []
        for index, relative in enumerate(self.remote_time_probe_paths):
            payload = self._remote_tail(
                remote_dir,
                relative,
                f"time_probe_{index:02d}.vcd.tail.tmp",
            )
            summary = vcd_time_summary(payload) if payload else {"status": "missing"}
            probes.append({"relative_path": relative.as_posix(), **summary})
        timestamps = [
            int(row["last_timestamp"])
            for row in probes
            if isinstance(row.get("last_timestamp"), int)
        ]
        return {
            "status": "ready" if timestamps else "pending",
            "last_timestamp": max(timestamps) if timestamps else None,
            "probes": probes,
        }

    def _native_loop_probe(self, remote_dir: str) -> dict[str, Any]:
        if not isinstance(self.native_loop_report_path, Path):
            return {"status": "disabled", "native_loop_detected": False}
        payload = self._remote_tail(
            remote_dir,
            self.native_loop_report_path,
            "native_loop_report.tail.tmp",
        )
        text = payload.decode("utf-8", errors="replace")
        lower = text.lower()
        markers = [
            marker for marker in VCS_ZERO_DELAY_LOOP_MARKERS if marker in lower
        ]
        return {
            "status": "ready" if payload else "pending",
            "native_loop_detected": bool(markers),
            "matched_markers": markers,
            "excerpt": text[-4000:] if markers else "",
        }

    def _simulator_cpu_probe(
        self,
        remote_dir: str,
        process_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """Read monotonic CPU ticks for live simulator processes only."""

        processes = process_snapshot.get("processes", [])
        pids = [
            int(row["pid"])
            for row in processes
            if isinstance(row, dict)
            and isinstance(row.get("pid"), int)
            and "simv" in str(row.get("command") or "").lower()
        ]
        if not pids:
            return {"status": "not_observed", "total_ticks": None, "processes": []}
        command = " ; ".join(
            (
                f"if test -r /proc/{pid}/stat; then "
                f"awk '{{print {pid}, $14 + $15}}' /proc/{pid}/stat; fi"
            )
            for pid in pids
        )
        result = run_transfer_command(
            [
                "ssh",
                "-p",
                str(self.port),
                "-o",
                "StrictHostKeyChecking=no",
                self.host,
                f"cd {shlex.quote(remote_dir)} && {command}",
            ],
            60,
        )
        rows: list[dict[str, int]] = []
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) != 2 or not all(part.isdigit() for part in parts):
                    continue
                rows.append({"pid": int(parts[0]), "cpu_ticks": int(parts[1])})
        return {
            "status": "ready" if rows else "not_observed",
            "processes": rows,
            "total_ticks": sum(row["cpu_ticks"] for row in rows) if rows else None,
        }

    def _has_current_proven_semantic_stall(self, remote_dir: str) -> bool:
        """Reuse a bound failure witness instead of re-copying a live log."""

        snapshot = read_json(self.snapshot_path)
        evidence = snapshot.get("adaptive_semantic_stall_evidence")
        return bool(
            snapshot.get("input_fingerprint_sha256") == self.fingerprint
            and snapshot.get("remote_workdir") == remote_dir
            and isinstance(evidence, dict)
            and evidence.get("status") == "proven_semantic_stall"
        )

    def __call__(self, observation: dict[str, Any]) -> None:
        state = str(observation.get("state") or "unknown")
        poll_attempt = int(observation.get("poll_attempt") or 0)
        if state not in {"running", "done"}:
            return
        if state == "running" and poll_attempt not in {1} and poll_attempt % 4:
            return
        remote_dir = str(observation.get("remote_workdir") or "")
        if not remote_dir:
            return
        if self._has_current_proven_semantic_stall(remote_dir):
            return
        self.bind_or_begin_epoch(remote_dir)
        self.live_dir.mkdir(parents=True, exist_ok=True)
        prior_byte_count = self.raw_path.stat().st_size if self.raw_path.is_file() else 0
        remote_start_byte = self._effective_progress_start_byte(remote_dir)
        use_full_snapshot = (
            remote_start_byte == 0
            and (state == "done" or poll_attempt == 1 or not self.raw_path.is_file())
        )
        if use_full_snapshot:
            temporary = self.raw_path.with_suffix(".jsonl.tmp")
            copied = run_transfer_command(
                [
                    "scp",
                    "-q",
                    "-P",
                    str(self.port),
                    "-o",
                    "StrictHostKeyChecking=no",
                    f"{self.host}:{remote_dir}/{self.remote_path.as_posix()}",
                    str(temporary),
                ],
                60,
            )
            if copied.returncode != 0 or not temporary.is_file():
                temporary.unlink(missing_ok=True)
                return
            os.replace(temporary, self.raw_path)
            transfer_mode = "full_snapshot"
            received_byte_count = self.raw_path.stat().st_size
        else:
            temporary = self.raw_path.with_suffix(".jsonl.increment.tmp")
            remote_file = f"{remote_dir.rstrip('/')}/{self.remote_path.as_posix()}"
            remote_offset = remote_start_byte + prior_byte_count
            copied = run_stream_transfer_command(
                [
                    "ssh",
                    "-p",
                    str(self.port),
                    "-o",
                    "StrictHostKeyChecking=no",
                    self.host,
                    f"tail -c +{remote_offset + 1} -- {shlex.quote(remote_file)}",
                ],
                temporary,
                60,
            )
            if copied.returncode != 0 or not temporary.is_file():
                temporary.unlink(missing_ok=True)
                return
            received_byte_count = temporary.stat().st_size
            if received_byte_count:
                with self.raw_path.open("ab") as destination, temporary.open("rb") as source:
                    shutil.copyfileobj(source, destination)
            temporary.unlink(missing_ok=True)
            transfer_mode = (
                "epoch_suffix"
                if remote_start_byte
                else "incremental_append"
            )
        parsed = read_complete_jsonl(self.raw_path)
        records = parsed.get("records", [])
        summary = summarize_progress_events(
            records if isinstance(records, list) else [],
            self.progress_contract,
        )
        last_committed_event = (
            dict(records[-1])
            if isinstance(records, list)
            and records
            and isinstance(records[-1], dict)
            else {}
        )
        record_count = int(summary.get("record_count") or 0)
        last_cycle_value = summary.get("last_cycle")
        last_cycle = (
            int(last_cycle_value)
            if isinstance(last_cycle_value, int)
            else None
        )
        running_signature = (
            record_count,
            last_cycle,
            int(parsed.get("committed_byte_count") or 0),
            None,
        )
        simulation_time_probe = self._simulation_time_probe(remote_dir)
        native_loop_probe = self._native_loop_probe(remote_dir)
        process_snapshot = (
            observation.get("process_snapshot")
            if isinstance(observation.get("process_snapshot"), dict)
            else {}
        )
        simulator_cpu_probe = self._simulator_cpu_probe(
            remote_dir,
            process_snapshot,
        )
        simulator_cpu_ticks = simulator_cpu_probe.get("total_ticks")
        simulation_time_watermark = simulation_time_probe.get("last_timestamp")
        running_signature = (
            running_signature[0],
            running_signature[1],
            running_signature[2],
            int(simulation_time_watermark)
            if isinstance(simulation_time_watermark, int)
            else None,
        )
        if state == "running":
            if running_signature == self._last_running_signature:
                self._unchanged_running_snapshot_count += 1
                if (
                    isinstance(simulator_cpu_ticks, int)
                    and isinstance(self._last_simulator_cpu_ticks, int)
                    and simulator_cpu_ticks > self._last_simulator_cpu_ticks
                ):
                    self._cpu_active_without_progress_snapshot_count += 1
                else:
                    self._cpu_active_without_progress_snapshot_count = 0
            else:
                self._unchanged_running_snapshot_count = 0
                self._cpu_active_without_progress_snapshot_count = 0
                self.zero_time_livelock_evidence = {}
            self._last_running_signature = running_signature
            self._last_simulator_cpu_ticks = (
                simulator_cpu_ticks
                if isinstance(simulator_cpu_ticks, int)
                else None
            )
            if (
                self._unchanged_running_snapshot_count
                >= self.ZERO_TIME_LIVELOCK_UNCHANGED_SNAPSHOT_LIMIT
                and (
                    native_loop_probe.get("native_loop_detected") is True
                    or self._cpu_active_without_progress_snapshot_count
                    >= self.ZERO_TIME_LIVELOCK_UNCHANGED_SNAPSHOT_LIMIT
                )
            ):
                self.zero_time_livelock_evidence = {
                    "schema_version": "spatialaccagent.zero_time_livelock_evidence.v1",
                    "status": "proven_zero_time_livelock",
                    "remote_workdir": remote_dir,
                    "remote_pid": observation.get("pid"),
                    "last_cycle": last_cycle,
                    "last_semantic_progress_cycle": summary.get(
                        "last_semantic_progress_cycle"
                    ),
                    "last_progress_event_count": record_count,
                    "committed_progress_bytes": running_signature[2],
                    "simulation_time_watermark": simulation_time_watermark,
                    "simulation_time_probe": simulation_time_probe,
                    "native_loop_report": native_loop_probe,
                    "simulator_cpu_probe": simulator_cpu_probe,
                    "consecutive_unchanged_running_snapshots": (
                        self._unchanged_running_snapshot_count
                    ),
                    "consecutive_cpu_active_without_progress_snapshots": (
                        self._cpu_active_without_progress_snapshot_count
                    ),
                    "required_unchanged_running_snapshots": (
                        self.ZERO_TIME_LIVELOCK_UNCHANGED_SNAPSHOT_LIMIT
                    ),
                    "fixed_wall_clock_timeout": False,
                    "fixed_cycle_timeout": False,
                    "reason": (
                        "the simulator kept consuming CPU while the independent "
                        "simulation-time watermark and flushed progress record set "
                        "remained unchanged across repeated observer snapshots"
                    ),
                }
        else:
            self._last_running_signature = None
            self._unchanged_running_snapshot_count = 0
            self._last_simulator_cpu_ticks = None
            self._cpu_active_without_progress_snapshot_count = 0
        simulator_process_observed = (
            process_snapshot.get("simulator_like_process_observed") is True
        )
        vcd_probe_ready = any(
            row.get("status") == "ready"
            for row in simulation_time_probe.get("probes", [])
            if isinstance(row, dict)
        )
        observation_activity = {
            "schema_version": (
                "spatialaccagent.testbench_observation_activity.v1"
            ),
            "runner_process_snapshot": process_snapshot,
            "simulator_process_observed": simulator_process_observed,
            "testbench_observation_process": (
                "simulator_process" if simulator_process_observed else "not_observed"
            ),
            "vcd_dumping": {
                "configured": bool(self.remote_time_probe_paths),
                "observed": vcd_probe_ready,
                "active_during_last_running_observation": (
                    state == "running" and vcd_probe_ready
                ),
                "last_timestamp": simulation_time_probe.get("last_timestamp"),
            },
            "progress_file_io": {
                "complete_record_count": record_count,
                "last_committed_event": last_committed_event,
                "write_observed_during_last_observation": received_byte_count > 0,
                "committed_byte_count": parsed.get("committed_byte_count"),
            },
            "other_testbench_file_io_callbacks": {
                "status": "not_directly_observable_from_runner",
            },
        }
        snapshot = {
            **summary,
            "input_fingerprint_sha256": self.fingerprint,
            "remote_workdir": remote_dir,
            "remote_progress_event_log": self.remote_path.as_posix(),
            "observation_epoch": self.epoch(),
            "local_progress_event_log": str(self.raw_path),
            "progress_event_log_sha256": sha256_file(self.raw_path),
            "process_state": state,
            "remote_pid": observation.get("pid"),
            "poll_attempt": poll_attempt,
            "observed_unix_time": time.time(),
            "committed_byte_count": parsed.get("committed_byte_count"),
            "trailing_partial_byte_count": parsed.get(
                "trailing_partial_byte_count"
            ),
            "invalid_jsonl_records": parsed.get("invalid_records", []),
            "simulation_time_probe": simulation_time_probe,
            "native_loop_report": native_loop_probe,
            "simulator_cpu_probe": simulator_cpu_probe,
            "last_committed_progress_event": last_committed_event,
            "testbench_observation_activity": observation_activity,
            "live_transfer": {
                "mode": transfer_mode,
                "prior_byte_count": prior_byte_count,
                "remote_start_byte": remote_start_byte,
                "received_byte_count": received_byte_count,
                "local_byte_count": self.raw_path.stat().st_size,
                "final_full_snapshot": state == "done",
            },
            "zero_time_livelock_evidence": self.zero_time_livelock_evidence,
            "policy": {
                **summary.get("policy", {}),
                "observer_never_terminates_the_remote_job": True,
                "simulation_timeout_policy_unchanged": True,
                "unchanged_progress_alone_never_proves_zero_time_livelock": True,
                "active_simulator_cpu_with_unchanged_progress_proves_zero_time_livelock": True,
            },
        }
        snapshot_tmp = self.snapshot_path.with_suffix(".json.tmp")
        write_json(snapshot_tmp, snapshot)
        os.replace(snapshot_tmp, self.snapshot_path)
        try:
            update_live_state_slot(
                self.live_dir.parents[2],
                "signals",
                {
                    "status": "complete" if state == "done" else "collecting",
                    "observation_epoch": snapshot.get("observation_epoch", {}),
                    "record_count": record_count,
                    "last_cycle": last_cycle,
                    "last_semantic_progress_cycle": summary.get(
                        "last_semantic_progress_cycle"
                    ),
                    "process_state": state,
                    "final_writeback_progress": summary.get(
                        "final_writeback_progress"
                    ),
                    "last_progress_event": last_committed_event,
                },
                binding=f"{self.fingerprint}@{remote_dir}",
            )
        except OSError:
            pass
        if record_count != self.last_record_count:
            with self.history_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(snapshot, sort_keys=True) + "\n")
            self.last_record_count = record_count

    def report(self) -> dict[str, Any]:
        snapshot = read_json(self.snapshot_path)
        return {
            "status": "ready" if snapshot else "pending_first_flushed_event",
            "snapshot": str(self.snapshot_path),
            "history": str(self.history_path),
            "raw_progress_event_log": str(self.raw_path),
            "latest": snapshot,
            "zero_time_livelock_evidence": self.zero_time_livelock_evidence,
        }


def materialize_vcs_library_setup(
    stage_dir: Path,
    commands: list[dict[str, Any]],
    staged_synopsys_setup: Path | None,
    staged_targets: dict[str, str],
) -> str | None:
    libraries = sorted(
        {
            str(command.get("work_library") or "")
            for command in commands
            if command.get("phase") == "compile"
            and str(command.get("work_library") or "")
        }
    )
    library_paths = {
        library: Path("vcs_lib") / library for library in libraries
    }
    for relative in library_paths.values():
        (stage_dir / relative).mkdir(parents=True, exist_ok=True)

    command_cwds = sorted(
        {command["cwd"] for command in commands}, key=lambda path: path.as_posix()
    )
    for cwd in command_cwds:
        setup_relative = cwd / "synopsys_sim.setup"
        setup_key = setup_relative.as_posix()
        if setup_key in staged_targets:
            return f"generated VCS library map collides with staged file: {setup_key}"
        lines = []
        for library, library_path in library_paths.items():
            relative_path = os.path.relpath(library_path, start=cwd).replace(os.sep, "/")
            lines.append(f"{library}:{relative_path}")
        if staged_synopsys_setup is not None:
            relative_vendor_map = os.path.relpath(
                staged_synopsys_setup, start=cwd
            ).replace(os.sep, "/")
            lines.append(f"OTHERS={relative_vendor_map}")
        setup_path = stage_dir / setup_relative
        setup_path.parent.mkdir(parents=True, exist_ok=True)
        setup_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        staged_targets[setup_key] = sha256_file(setup_path)
    return None


def execute_pending_exact_board_job(
    run_dir: Path,
    timeout_sec: int,
    pending_job: dict[str, Any],
) -> dict[str, Any] | None:
    """Attach to a sealed VCS job without rebuilding any board inputs."""

    job = pending_job["job"]
    job_path = Path(pending_job["job_path"])
    manifest_path = Path(pending_job["manifest_path"])
    manifest = read_json(manifest_path)
    fingerprint = str(job["input_fingerprint_sha256"])
    if job.get("preflight_manifest_projection_sha256") != preflight_manifest_projection_sha256(manifest):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "phase": "active_exact_job_observation",
            "failure_class": "active_exact_job_manifest_changed",
            "input_fingerprint_sha256": fingerprint,
            "remote_workdir": job.get("remote_workdir"),
            "remote_job_preserved": True,
            "errors": ["the pending exact VCS job no longer matches the board manifest"],
        }

    tool = tool_profile(run_dir)
    host = str(tool.get("host") or "")
    port = int(tool.get("port") or 22)
    payload = job.get("payload") if isinstance(job.get("payload"), list) else []
    if not host or not payload:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "phase": "active_exact_job_observation",
            "failure_class": "active_exact_job_contract_invalid",
            "input_fingerprint_sha256": fingerprint,
            "remote_workdir": job.get("remote_workdir"),
            "remote_job_preserved": True,
            "errors": ["the pending exact VCS job has no usable remote tool or payload contract"],
        }

    output_rows: dict[str, Path] = {}
    execution_outputs = job.get("execution_outputs")
    if isinstance(execution_outputs, dict):
        for name, row in execution_outputs.items():
            if isinstance(row, dict):
                relative = safe_relative_path(row.get("path"))
                if relative is not None:
                    output_rows[str(name)] = relative
            elif isinstance(row, list):
                for index, item in enumerate(row):
                    if isinstance(item, dict):
                        relative = safe_relative_path(item.get("path"))
                        if relative is not None:
                            output_rows[f"{name}_{index}"] = relative
    progress_path = output_rows.get("progress_event_log")
    observer = (
        LiveProgressObserver(
            host=host,
            port=port,
            run_dir=run_dir,
            remote_path=progress_path,
            fingerprint=fingerprint,
            progress_contract=cctg_progress_contract(run_dir, manifest),
            native_loop_report_path=output_rows.get("simulation_log"),
            live_namespace="active_exact_job",
        )
        if progress_path is not None
        else None
    )
    out_dir = run_dir / "verification" / "vcs"
    out_dir.mkdir(parents=True, exist_ok=True)
    recovered = recover_exact_remote_semantic_job(
        host,
        port,
        str(job.get("remote_stage_root") or ""),
        fingerprint,
        out_dir,
        job_path,
        payload,
        timeout_sec,
        str(job.get("simulate_command") or ""),
        progress_callback=observer,
        allow_relaunch=False,
        allow_initial_simulation_launch=True,
    )
    if recovered is None:
        # Candidate discovery completed and found no remote copy of this sealed
        # contract.  The regular path below may perform its one initial launch.
        return None
    if recovered.get("recovery_state") == "indeterminate":
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "phase": "active_exact_job_observation",
            "failure_class": "remote_semantic_recovery_indeterminate",
            "input_fingerprint_sha256": fingerprint,
            "remote_workdir": job.get("remote_workdir"),
            "remote_job_preserved": True,
            "remote_job_reuse": recovered or {"status": "fail", "summary": "exact remote job was not found"},
            "errors": ["the pending exact VCS job could not be attached deterministically"],
        }

    remote_dir = str(recovered["remote_dir"])
    board_dir = run_dir / "verification" / "board_simulation"
    compile_result = dict(recovered.get("compile") or {})
    simulate_result = dict(recovered.get("simulate") or {})
    semantic_stall_evidence = simulate_result.get(
        "adaptive_semantic_stall_evidence", {}
    )
    reuse_live_progress = bool(
        observer is not None
        and simulate_result.get("failure_class") == "adaptive_semantic_stall"
        and isinstance(semantic_stall_evidence, dict)
        and semantic_stall_evidence.get("status") == "proven_semantic_stall"
    )
    copied_outputs: dict[str, dict[str, Any]] = {}
    for name, relative in output_rows.items():
        if name == "progress_event_log" and reuse_live_progress:
            local_path = observer.raw_path
            available = local_path.is_file()
            copied_outputs[name] = {
                "path": str(local_path),
                "relative_path": relative.as_posix(),
                "copied": available,
                "sha256": sha256_file(local_path) if available else None,
                "transfer": "reused_bound_live_progress",
                "full_remote_log_downloaded": False,
            }
            continue
        local_path = board_dir / relative
        if name == "simulation_log" and reuse_live_progress:
            _prepare_fresh_transfer_target(local_path)
            log_tail = observer._remote_tail(
                remote_dir,
                relative,
                "active_exact_simulation_log.tail.tmp",
            )
            if log_tail:
                local_path.write_bytes(log_tail)
            available = local_path.is_file()
            copied_outputs[name] = {
                "path": str(local_path),
                "relative_path": relative.as_posix(),
                "copied": available,
                "sha256": sha256_file(local_path) if available else None,
                "transfer": "bounded_remote_log_tail",
                "full_remote_log_downloaded": False,
            }
            continue
        _prepare_fresh_transfer_target(local_path)
        copied = run_transfer_command(
            [
                "scp",
                "-q",
                "-P",
                str(port),
                "-o",
                "StrictHostKeyChecking=no",
                f"{host}:{remote_dir}/{relative.as_posix()}",
                str(local_path),
            ],
            timeout_sec,
        )
        available = copied.returncode == 0 and local_path.is_file()
        if not available:
            local_path.unlink(missing_ok=True)
        copied_outputs[name] = {
            "path": str(local_path),
            "relative_path": relative.as_posix(),
            "copied": available,
            "sha256": sha256_file(local_path) if available else None,
        }

    progress_summary: dict[str, Any] = {}
    if reuse_live_progress:
        latest = observer.report().get("latest", {}) if observer is not None else {}
        progress_summary = latest if isinstance(latest, dict) else {}
    else:
        progress_row = copied_outputs.get("progress_event_log", {})
        progress_local = Path(str(progress_row.get("path") or ""))
        if progress_row.get("copied") is True:
            parsed = read_complete_jsonl(progress_local)
            progress_summary = summarize_progress_events(
                parsed.get("records", []), cctg_progress_contract(run_dir, manifest)
            )
            progress_summary["invalid_record_count"] = len(parsed.get("invalid_records", []))
            records = parsed.get("records", [])
            if isinstance(records, list) and records and isinstance(records[-1], dict):
                progress_summary["last_committed_progress_event"] = dict(records[-1])

    if reuse_live_progress:
        progress_summary["invalid_record_count"] = 0
    simulation_log_row = copied_outputs.get("simulation_log", {})
    simulation_log_path = Path(str(simulation_log_row.get("path") or ""))
    simulate_result = apply_simulation_terminal_log_result(
        simulate_result, simulation_log_path
    )
    simulate_result["termination_provenance"] = simulation_termination_provenance(
        simulate_result,
        simulation_log_path,
        timeout_sec=timeout_sec,
        progress_summary=progress_summary,
        input_fingerprint_sha256=fingerprint,
        live_progress=observer.report() if observer is not None else {},
    )
    terminal_success = (
        compile_result.get("status") == "pass"
        and simulate_result.get("status") == "pass"
    )
    job_lost = simulate_result.get("failure_class") == "remote_job_lost"
    phase = "active_exact_job_observation" if job_lost else "active_exact_job_collection" if terminal_success else "remote_vcs"
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "verification_layer": "layer3_real_board_axi_ddr",
        "status": "fail",
        "phase": phase,
        "active_exact_job_attachment": True,
        "stage_pass_eligible": False,
        "input_fingerprint_sha256": fingerprint,
        "remote_workdir": remote_dir,
        "manifest": str(manifest_path),
        "source_identity": str(run_dir / "verification" / "board_interface" / "board_source_identity.json"),
        "source_identity_sha256": job.get("source_identity_sha256"),
        "source_closure_sha256": job.get("source_closure_sha256"),
        "compile_source_set_sha256": job.get("compile_source_set_sha256"),
        "exact_job_contract_bound": True,
        "exact_board_preflight_at_launch": True,
        "exact_board_preflight_passed": True,
        "exact_board_acceptance_passed": False,
        "compile": compile_result,
        "run": simulate_result,
        "termination_provenance": simulate_result["termination_provenance"],
        "returncode": simulate_result.get("returncode", compile_result.get("returncode")),
        "compile_log": copied_outputs.get("compile_log", {}).get("path"),
        "sim_log": copied_outputs.get("simulation_log", {}).get("path"),
        "outputs": copied_outputs,
        "required_outputs_copied": False,
        "structured_monitors_passed": False,
        "pipeline_overlap_passed": False,
        "progress_event_log_valid": bool(progress_summary.get("terminal_event_seen")),
        "progress_event_summary": progress_summary,
        "live_progress": observer.report() if observer is not None else {},
        "remote_job_reuse": {
            "status": "pass",
            "real_tool_was_not_relaunched": True,
            "remote_workdir": remote_dir,
            **dict(recovered.get("identity") or {}),
        },
        "remote_job_recovery_contract": {
            "status": "pass",
            "job_contract": str(job_path),
            "job_contract_sha256": sha256_file(job_path),
            "policy": "pending exact VCS jobs are attached and never relaunched",
        },
    }
    if terminal_success:
        capture = collect_completed_native_checkpoint(
            run_dir,
            timeout_sec,
            manifest,
            remote_dir,
            simulation_log_path,
        )
        if capture.get("status") == "pass":
            checkpoint_plan = capture["checkpoint_plan"]
            report.update(
                {
                    "status": "checkpoint_capture_complete",
                    "hardware_validation_status": "checkpoint_capture_complete",
                    "phase": "remote_vcs",
                    "summary": (
                        "completed Layer-3 native checkpoint collected; "
                        "one restore confirmation is required before reuse"
                    ),
                    "simulation_execution_identity": checkpoint_plan.get(
                        "execution_identity", {}
                    ),
                    "checkpoint_execution": {
                        key: checkpoint_plan.get(key)
                        for key in (
                            "status",
                            "mode",
                            "enabled",
                            "candidate_screening",
                            "acceptance_eligible",
                            "request_path",
                            "request_sha256",
                            "policy",
                        )
                    },
                    "checkpoint_artifacts": capture["checkpoint_artifacts"],
                    "fast_replay_used": False,
                    "compile_reused": False,
                    "weight_load_skipped": False,
                    "second_vcs_compile_was_not_launched": False,
                    "simulator_path": "vcs_work/simv",
                }
            )
            report.pop("failure_class", None)
            report.pop("errors", None)
            return report
        report["failure_class"] = "active_exact_job_terminal_acceptance_required"
        report["errors"] = [
            "the sealed job completed, but full acceptance must be collected against its launch identity"
        ]
    elif job_lost:
        report["failure_class"] = "remote_job_lost"
    return report


def collect_completed_native_checkpoint(
    run_dir: Path,
    timeout_sec: int,
    manifest: dict[str, Any],
    remote_dir: str,
    simulation_log_path: Path,
) -> dict[str, Any]:
    """Persist a native snapshot already saved by a completed exact VCS job.

    This is a local bookkeeping step.  It never launches VCS, reloads weights,
    copies the large native state, or recreates the remote snapshot.
    """

    request_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "vcs_stage"
        / "checkpoint"
        / "request.json"
    )
    checkpoint_plan = checkpoint_execution_plan(
        run_dir,
        manifest,
        env={
            "SPATIALACC_CHECKPOINT_REQUIRED": "1",
            "SPATIALACC_CHECKPOINT_REQUEST": str(request_path),
        },
    )
    if (
        checkpoint_plan.get("status") != "pass"
        or checkpoint_plan.get("mode") != "cold_capture"
    ):
        return {
            "status": "fail",
            "checkpoint_plan": checkpoint_plan,
            "errors": checkpoint_plan.get("errors", []),
        }

    simulation_log = (
        simulation_log_path.read_text(encoding="utf-8", errors="ignore")
        if simulation_log_path.is_file()
        else ""
    )
    ready_match = re.search(
        r"SPATIALACC_NATIVE_CHECKPOINT_READY\s+sequence=(\d+)\s+cycle=(\d+)",
        simulation_log,
    )
    tool = tool_profile(run_dir)
    host = str(tool.get("host") or "")
    port = int(tool.get("port") or 22)
    available = run_transfer_command(
        [
            "ssh",
            "-p",
            str(port),
            "-o",
            "StrictHostKeyChecking=no",
            host,
            "cd "
            + shlex.quote(remote_dir)
            + " && test -f "
            + shlex.quote(NATIVE_CHECKPOINT_SNAPSHOT.as_posix())
            + " && test -f "
            + shlex.quote(f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli")
            + " && test -d "
            + shlex.quote(NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix()),
        ],
        timeout_sec,
    )
    capture_report = {
        "schema_version": CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION,
        "status": (
            "pass"
            if ready_match
            and "SPATIALACC_NATIVE_CHECKPOINT_SAVE_PASS" in simulation_log
            and available.returncode == 0
            else "fail"
        ),
        "mode": "cold_capture",
        "captured_sequence": int(ready_match.group(1)) if ready_match else None,
        "captured_cycle": int(ready_match.group(2)) if ready_match else None,
        "state_artifacts": [
            {
                "kind": "native_vcs_snapshot",
                "path": NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
                "remote_path": NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
                "remote_ucli_path": f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli",
                "remote_files_path": NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix(),
            }
        ],
        "native_ready_marker_seen": bool(ready_match),
        "native_save_marker_seen": (
            "SPATIALACC_NATIVE_CHECKPOINT_SAVE_PASS" in simulation_log
        ),
        "native_snapshot_available": available.returncode == 0,
    }
    errors = checkpoint_capture_report_errors(checkpoint_plan, capture_report)
    incoming = checkpoint_root(run_dir) / ".incoming_fast_replay"
    if incoming.exists():
        shutil.rmtree(incoming)
    incoming.mkdir(parents=True, exist_ok=True)
    write_json(incoming / "capture_report.json", capture_report)
    if errors:
        return {
            "status": "fail",
            "checkpoint_plan": checkpoint_plan,
            "checkpoint_artifacts": {
                "status": "fail",
                "mode": "cold_capture",
                "capture_report": str(incoming / "capture_report.json"),
                "errors": list(dict.fromkeys(errors)),
            },
            "errors": errors,
        }

    state_artifacts = [
        {
            "path": "native_state",
            "kind": "native_vcs_snapshot",
            "remote_path": NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
            "remote_ucli_path": f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli",
            "remote_files_path": NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix(),
            "byte_count": 0,
        }
    ]
    checkpoint_manifest = framework_checkpoint_manifest(
        checkpoint_plan,
        capture_report,
        state_artifacts,
        remote_workdir=remote_dir,
    )
    checkpoint_id = str(checkpoint_manifest["checkpoint_id"])
    final_dir = checkpoint_root(run_dir) / checkpoint_id
    write_json(incoming / "manifest.json", checkpoint_manifest)
    if final_dir.exists():
        shutil.rmtree(final_dir)
    incoming.rename(final_dir)
    return {
        "status": "pass",
        "checkpoint_plan": checkpoint_plan,
        "checkpoint_artifacts": {
            "status": "pass",
            "mode": "cold_capture",
            "checkpoint_id": checkpoint_id,
            "manifest": str(final_dir / "manifest.json"),
            "total_state_bytes": checkpoint_manifest.get("total_state_bytes", 0),
            "errors": [],
            "remote_acknowledgment_status": "pending",
        },
    }


def saved_replay_command(
    saved_job: dict[str, Any],
    replay: dict[str, Any],
) -> tuple[str | None, dict[str, Path], list[str]]:
    """Build a restore command from the remote job captured with the snapshot."""

    simulator_path = str(replay.get("simulator_path") or "")
    runtime_args, errors = saved_workload_args(saved_job, simulator_path)
    if runtime_args is None:
        return None, {}, errors
    runtime_args = [
        value
        for value in runtime_args
        if not value.startswith("+SPATIALACC_OBSERVATION_SELECTION=")
    ]
    runtime_args.append(
        "+SPATIALACC_OBSERVATION_SELECTION=observation/current_selection.json"
    )
    restore_log = Path("reports/fast_replay_restore.log")
    command = (
        "set -e; mkdir -p reports checkpoint; "
        + f"./{simulator_path}"
        + " -ucli -do "
        + shlex.quote(NATIVE_CHECKPOINT_RESTORE_TCL.as_posix())
        + " "
        + " ".join(shlex.quote(value) for value in runtime_args)
        + " +SPATIALACC_NATIVE_CHECKPOINT_RESTORE"
        + f" > {shlex.quote(restore_log.as_posix())} 2>&1"
    )
    # Do not remove preexisting reports, memory images, or snapshot files.
    # Native simulator state includes live testbench state at the save cut.
    return command, {"restore_log": restore_log}, []


def saved_workload_args(
    saved_job: dict[str, Any],
    simulator_path: str,
) -> tuple[list[str] | None, list[str]]:
    """Extract only real workload plusargs from one saved VCS command."""

    raw_command = str(saved_job.get("simulate_command") or "").strip()
    try:
        tokens = shlex.split(raw_command)
    except ValueError:
        return None, ["saved replay command cannot be read"]
    simulator_token = f"./{simulator_path}"
    try:
        simulator_index = tokens.index(simulator_token)
    except ValueError:
        return None, ["saved replay command does not use the saved simulator"]

    runtime_args: list[str] = []
    skip_next = False
    for token in tokens[simulator_index + 1 :]:
        if token == ">":
            break
        if skip_next:
            skip_next = False
            continue
        # The saved command can be a capture command.  Keep only the original
        # workload arguments; VCS owns restore through its UCLI script.
        if token in {"-ucli", "-do"}:
            skip_next = token == "-do"
            continue
        if (
            token == "+SPATIALACC_NATIVE_CHECKPOINT_CAPTURE"
            or token == "+SPATIALACC_NATIVE_CHECKPOINT_RESTORE"
            or token.startswith("+SPATIALACC_CHECKPOINT_")
        ):
            continue
        runtime_args.append(token)
    if not runtime_args:
        return None, ["saved replay has no original workload arguments"]
    return runtime_args, []


def materialize_current_observation_selection(run_dir: Path) -> Path:
    """Return the one runtime selection used by the next Layer-3 execution."""

    selection = current_observation_selection_path(run_dir)
    if not selection.is_file():
        runtime_observation_selection(run_dir, {}, persist=True)
    return selection


def stage_current_observation_selection(run_dir: Path, stage_dir: Path) -> Path:
    """Copy the latest runtime selection into one cold VCS payload."""

    source = materialize_current_observation_selection(run_dir)
    destination = stage_dir / "observation" / "current_selection.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def upload_current_observation_selection(
    run_dir: Path,
    *,
    host: str,
    port: int,
    remote_dir: str,
    timeout_sec: int,
) -> subprocess.CompletedProcess[str]:
    """Replace the saved workdir's selection before every native restore."""

    selection = materialize_current_observation_selection(run_dir)
    prepare = run_transfer_command(
        [
            "ssh", "-p", str(port), "-o", "StrictHostKeyChecking=no", host,
            "cd " + shlex.quote(remote_dir) + " && mkdir -p observation",
        ],
        timeout_sec,
    )
    if prepare.returncode != 0:
        return prepare
    return run_transfer_command(
        [
            "scp", "-q", "-P", str(port), "-o", "StrictHostKeyChecking=no",
            str(selection),
            f"{host}:{remote_dir}/observation/current_selection.json",
        ],
        timeout_sec,
    )


def remote_file_metadata(
    *,
    host: str,
    port: int,
    remote_dir: str,
    relative: Path,
    timeout_sec: int,
) -> dict[str, int] | None:
    """Read one remote output identity without copying its historical records."""

    safe_relative = safe_relative_path(relative)
    if safe_relative is None:
        return None
    remote_file = f"{remote_dir.rstrip('/')}/{safe_relative.as_posix()}"
    result = run_transfer_command(
        [
            "ssh",
            "-p",
            str(port),
            "-o",
            "StrictHostKeyChecking=no",
            host,
            (
                f"if test -f {shlex.quote(remote_file)}; then "
                f"stat -c '%d %i %s' {shlex.quote(remote_file)}; "
                "else printf '0 0 0\\n'; fi"
            ),
        ],
        timeout_sec,
    )
    if result.returncode != 0:
        return None
    values = re.findall(r"\d+", result.stdout)
    if len(values) < 3:
        return None
    return {
        "device": int(values[-3]),
        "inode": int(values[-2]),
        "byte_count": int(values[-1]),
    }


def remote_file_byte_count(
    *,
    host: str,
    port: int,
    remote_dir: str,
    relative: Path,
    timeout_sec: int,
) -> int | None:
    metadata = remote_file_metadata(
        host=host,
        port=port,
        remote_dir=remote_dir,
        relative=relative,
        timeout_sec=timeout_sec,
    )
    return metadata.get("byte_count") if metadata is not None else None


def copy_remote_file_suffix(
    *,
    host: str,
    port: int,
    remote_dir: str,
    relative: Path,
    start_byte: int,
    destination: Path,
    timeout_sec: int,
) -> subprocess.CompletedProcess[str]:
    """Copy only the records written after a replay observation epoch began."""

    safe_relative = safe_relative_path(relative)
    if safe_relative is None or start_byte < 0:
        return subprocess.CompletedProcess([], 2, "", "unsafe epoch output path")
    _prepare_fresh_transfer_target(destination)
    remote_file = f"{remote_dir.rstrip('/')}/{safe_relative.as_posix()}"
    return run_stream_transfer_command(
        [
            "ssh",
            "-p",
            str(port),
            "-o",
            "StrictHostKeyChecking=no",
            host,
            f"tail -c +{start_byte + 1} -- {shlex.quote(remote_file)}",
        ],
        destination,
        timeout_sec,
    )


def saved_recapture_command(
    saved_job: dict[str, Any],
    replay: dict[str, Any],
) -> tuple[str | None, dict[str, Path], list[str]]:
    """Recreate one native snapshot with a saved compiled simulator only."""

    simulator_path = str(replay.get("simulator_path") or "")
    runtime_args, errors = saved_workload_args(saved_job, simulator_path)
    if runtime_args is None:
        return None, {}, errors

    capture_log = Path("reports/fast_replay_recapture.log")
    stale_outputs = [
        "reports/simulation.log",
        "reports/progress_event_log.jsonl",
        "reports/boundary_trace.jsonl",
        "reports/connected_kernel_delta_transition.jsonl",
        "reports/rtl_output.bin",
        NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
        f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli",
    ]
    command = (
        "set -e; mkdir -p reports checkpoint checkpoint/state; rm -f -- "
        + " ".join(shlex.quote(path) for path in stale_outputs)
        + "; rm -rf -- "
        + shlex.quote(NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix())
        + "; "
        + f"./{simulator_path}"
        + " -ucli -do "
        + shlex.quote(NATIVE_CHECKPOINT_CAPTURE_TCL.as_posix())
        + " "
        + " ".join(shlex.quote(value) for value in runtime_args)
        + " +SPATIALACC_NATIVE_CHECKPOINT_CAPTURE"
        + f" > {shlex.quote(capture_log.as_posix())} 2>&1"
    )
    return command, {"capture_log": capture_log}, []


def execute_saved_fast_recapture(run_dir: Path, timeout_sec: int) -> dict[str, Any]:
    """Replace one bad native snapshot without compiling the saved model again."""

    manifest, resolved, errors = validate_manifest(run_dir)
    if errors:
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_recapture_validation",
            "failure_class": "fast_replay_current_manifest_invalid",
            "errors": errors,
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
        }
    current_identity = simulation_execution_identity(manifest)
    state = read_fast_replay_state(run_dir)
    state_identity = state.get("identity", {})
    state_identity = state_identity if isinstance(state_identity, dict) else {}
    identity_errors = [
        f"saved compiled simulator {field} does not match the current Layer-3 run"
        for field in ("compiled_model_sha256", "workload_sha256")
        if state_identity.get(field) != current_identity.get(field)
    ]
    # A failed capture can retain an older remote directory in its durable
    # state.  Recapture must bind to the current successful Layer-3 runner,
    # never to that historical field.
    runner = read_json(
        run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    )
    runner_identity = runner.get("simulation_execution_identity", {})
    runner_identity = runner_identity if isinstance(runner_identity, dict) else {}
    runner_compile = runner.get("compile", {})
    runner_compile = runner_compile if isinstance(runner_compile, dict) else {}
    remote_dir = str(runner.get("remote_workdir") or "").strip()
    simulator_path = str(runner.get("simulator_path") or "").strip()
    simulator = Path(simulator_path)
    if state.get("status") != "repair_required":
        identity_errors.append("fast replay state is not awaiting native snapshot recapture")
    if runner_identity != current_identity:
        identity_errors.append(
            "current Layer-3 runner identity does not match the current board manifest"
        )
    if runner_compile.get("status") != "pass":
        identity_errors.append("current Layer-3 runner has no successful VCS compile")
    if not remote_dir.startswith("/"):
        identity_errors.append("saved compiled simulator remote directory is missing")
    if not simulator_path or simulator.is_absolute() or ".." in simulator.parts:
        identity_errors.append("saved compiled simulator path is missing or unsafe")
    if identity_errors:
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_recapture_validation",
            "failure_class": "fast_replay_recapture_identity_invalid",
            "errors": identity_errors,
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
        }

    checkpoint_plan = checkpoint_execution_plan(run_dir, manifest)
    if (
        checkpoint_plan.get("status") != "pass"
        or checkpoint_plan.get("mode") != "cold_capture"
    ):
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_recapture_validation",
            "failure_class": "fast_replay_recapture_request_invalid",
            "errors": list(checkpoint_plan.get("errors") or [
                "native snapshot recapture requires a current cold-capture request"
            ]),
            "checkpoint_execution": checkpoint_plan,
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
        }

    tool = tool_profile(run_dir)
    host = str(tool.get("host") or "")
    port = int(tool.get("port") or 22)
    if not host:
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_recapture_validation",
            "failure_class": "fast_replay_tool_missing",
            "errors": ["Layer-3 VCS remote host is missing"],
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
        }

    board_dir = run_dir / "verification" / "board_simulation"
    board_dir.mkdir(parents=True, exist_ok=True)
    out_dir = run_dir / "verification" / "vcs"
    out_dir.mkdir(parents=True, exist_ok=True)
    replay_dir = board_dir / "fast_replay" / "recapture"
    job_path = replay_dir / "saved_job.json"
    _prepare_fresh_transfer_target(job_path)
    job_download = run_transfer_command(
        [
            "scp", "-q", "-P", str(port), "-o", "StrictHostKeyChecking=no",
            f"{host}:{remote_dir}/.spatialacc_semantic_job.json", str(job_path),
        ],
        timeout_sec,
    )
    saved_job = read_json(job_path) if job_download.returncode == 0 else {}
    replay = {"simulator_path": simulator_path}
    command, outputs, command_errors = saved_recapture_command(saved_job, replay)
    if command is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_recapture_validation",
            "failure_class": "fast_replay_saved_job_invalid",
            "errors": command_errors or ["saved recapture command is unavailable"],
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
            "stderr_tail": job_download.stderr[-4000:],
        }

    local_tcl = replay_dir / NATIVE_CHECKPOINT_CAPTURE_TCL
    local_tcl.parent.mkdir(parents=True, exist_ok=True)
    local_tcl.write_text(native_checkpoint_capture_tcl(), encoding="utf-8")
    upload = run_transfer_command(
        [
            "scp", "-q", "-P", str(port), "-o", "StrictHostKeyChecking=no",
            str(local_tcl), f"{host}:{remote_dir}/{NATIVE_CHECKPOINT_CAPTURE_TCL.as_posix()}",
        ],
        timeout_sec,
    )
    availability = run_transfer_command(
        [
            "ssh", "-p", str(port), "-o", "StrictHostKeyChecking=no", host,
            "cd " + shlex.quote(remote_dir) + " && test -x "
            + shlex.quote(simulator_path) + " && test -f "
            + shlex.quote(NATIVE_CHECKPOINT_CAPTURE_TCL.as_posix()),
        ],
        timeout_sec,
    )
    if upload.returncode != 0 or availability.returncode != 0:
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_recapture_validation",
            "failure_class": "fast_replay_remote_artifact_missing",
            "errors": ["saved Layer-3 simulator or updated native capture script is missing"],
            "remote_workdir": remote_dir,
            "simulator_path": simulator_path,
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
        }

    simulate_result = run_remote_background_command(
        host, port, command, remote_dir, out_dir, timeout_sec,
        "vcs_fast_replay_recapture",
    )
    capture_log = outputs["capture_log"]
    local_capture_log = replay_dir / capture_log
    _prepare_fresh_transfer_target(local_capture_log)
    capture_download = run_transfer_command(
        [
            "scp", "-q", "-P", str(port), "-o", "StrictHostKeyChecking=no",
            f"{host}:{remote_dir}/{capture_log.as_posix()}", str(local_capture_log),
        ],
        timeout_sec,
    )
    simulate_result = apply_simulation_terminal_log_result(
        simulate_result, local_capture_log
    )
    capture_text = (
        local_capture_log.read_text(encoding="utf-8", errors="ignore")
        if local_capture_log.is_file() else ""
    )
    ready_match = re.search(
        r"SPATIALACC_NATIVE_CHECKPOINT_READY\s+sequence=(\d+)\s+cycle=(\d+)",
        capture_text,
    )
    save_marker_seen = "SPATIALACC_NATIVE_CHECKPOINT_SAVE_PASS" in capture_text
    snapshot_available = run_transfer_command(
        [
            "ssh", "-p", str(port), "-o", "StrictHostKeyChecking=no", host,
            "cd " + shlex.quote(remote_dir) + " && test -f "
            + shlex.quote(NATIVE_CHECKPOINT_SNAPSHOT.as_posix()) + " && test -f "
            + shlex.quote(f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli")
            + " && test -d " + shlex.quote(NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix()),
        ],
        timeout_sec,
    ).returncode == 0
    capture_report = {
        "schema_version": CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION,
        "status": "pass" if ready_match and save_marker_seen and snapshot_available else "fail",
        "mode": "cold_capture",
        "captured_sequence": int(ready_match.group(1)) if ready_match else None,
        "captured_cycle": int(ready_match.group(2)) if ready_match else None,
        "state_artifacts": [{
            "kind": "native_vcs_snapshot",
            "path": NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
            "remote_path": NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
            "remote_ucli_path": f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli",
            "remote_files_path": NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix(),
        }],
        "native_ready_marker_seen": bool(ready_match),
        "native_save_marker_seen": save_marker_seen,
        "native_snapshot_available": snapshot_available,
    }
    checkpoint_errors = checkpoint_capture_report_errors(checkpoint_plan, capture_report)
    incoming_dir = checkpoint_root(run_dir) / ".incoming_fast_replay"
    if incoming_dir.exists():
        shutil.rmtree(incoming_dir)
    incoming_dir.mkdir(parents=True, exist_ok=True)
    write_json(incoming_dir / "capture_report.json", capture_report)
    checkpoint_artifacts: dict[str, Any] = {
        "status": "fail",
        "mode": "cold_capture",
        "capture_report": str(incoming_dir / "capture_report.json"),
        "errors": list(dict.fromkeys(checkpoint_errors)),
    }
    if not checkpoint_errors:
        checkpoint_manifest = framework_checkpoint_manifest(
            checkpoint_plan,
            capture_report,
            [{
                "path": "native_state",
                "kind": "native_vcs_snapshot",
                "remote_path": NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
                "remote_ucli_path": f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli",
                "remote_files_path": NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix(),
                "byte_count": 0,
            }],
            remote_workdir=remote_dir,
        )
        checkpoint_id = str(checkpoint_manifest["checkpoint_id"])
        final_dir = checkpoint_root(run_dir) / checkpoint_id
        write_json(incoming_dir / "manifest.json", checkpoint_manifest)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        incoming_dir.rename(final_dir)
        checkpoint_artifacts = {
            "status": "pass",
            "mode": "cold_capture",
            "checkpoint_id": checkpoint_id,
            "manifest": str(final_dir / "manifest.json"),
            "total_state_bytes": 0,
            "errors": [],
            "remote_acknowledgment_status": "pending",
        }
    captured = (
        not checkpoint_errors
        and simulate_result.get("status") == "pass"
        and capture_download.returncode == 0
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "verification_layer": "layer3_real_board_axi_ddr",
        "status": "checkpoint_capture_complete" if captured else "fail",
        "hardware_validation_status": "checkpoint_capture_complete" if captured else "fail",
        "stage_pass_eligible": False,
        "phase": "fast_replay_recapture",
        "summary": (
            "reused the saved Layer-3 VCS simulator to recapture the native checkpoint"
            if captured else "saved Layer-3 simulator recapture did not complete"
        ),
        "simulation_execution_identity": current_identity,
        "checkpoint_execution": {
            key: checkpoint_plan.get(key)
            for key in ("status", "mode", "enabled", "candidate_screening", "acceptance_eligible", "request_path", "request_sha256", "policy")
        },
        "checkpoint_artifacts": checkpoint_artifacts,
        "fast_replay_used": False,
        "compile_reused": True,
        "weight_load_skipped": False,
        "second_vcs_compile_was_not_launched": True,
        "remote_workdir": remote_dir,
        "simulator_path": simulator_path,
        "compile": {"status": "pass", "reused": True, "summary": "reused saved remote VCS simulator; no VCS compile was launched"},
        "run": simulate_result,
        "outputs": {"capture_log": {"path": str(local_capture_log), "copied": capture_download.returncode == 0 and local_capture_log.is_file()}},
    }


def execute_saved_fast_replay(run_dir: Path, timeout_sec: int) -> dict[str, Any]:
    """Run a saved Layer-3 simulator without current-source preflight.

    This deliberately reads only the snapshot record and the remote job saved
    alongside it.  The current generated testbench can have new probes for a
    later run; its source hash is irrelevant to proving that the saved snapshot
    restores and runs without recompiling or reloading weights.
    """

    replay = restore_inputs(run_dir)
    if replay.get("status") != "ready":
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_validation",
            "failure_class": "fast_replay_inputs_missing",
            "errors": replay.get("reasons", []),
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
        }

    tool = tool_profile(run_dir)
    host = str(tool.get("host") or "")
    port = int(tool.get("port") or 22)
    remote_dir = str(replay["remote_workdir"])
    simulator_path = str(replay["simulator_path"])
    if not host:
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_validation",
            "failure_class": "fast_replay_tool_missing",
            "errors": ["Layer-3 VCS remote host is missing"],
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
        }

    board_dir = run_dir / "verification" / "board_simulation"
    board_dir.mkdir(parents=True, exist_ok=True)
    out_dir = run_dir / "verification" / "vcs"
    out_dir.mkdir(parents=True, exist_ok=True)
    local_restore_tcl = board_dir / "fast_replay" / NATIVE_CHECKPOINT_RESTORE_TCL
    local_restore_tcl.parent.mkdir(parents=True, exist_ok=True)
    local_restore_tcl.write_text(native_checkpoint_restore_tcl(), encoding="utf-8")
    restore_upload = run_transfer_command(
        [
            "scp", "-q", "-P", str(port), "-o", "StrictHostKeyChecking=no",
            str(local_restore_tcl),
            f"{host}:{remote_dir}/{NATIVE_CHECKPOINT_RESTORE_TCL.as_posix()}",
        ],
        timeout_sec,
    )
    observation_upload = upload_current_observation_selection(
        run_dir,
        host=host,
        port=port,
        remote_dir=remote_dir,
        timeout_sec=timeout_sec,
    )
    job_path = board_dir / "fast_replay_saved_job.json"
    _prepare_fresh_transfer_target(job_path)
    job_download = run_transfer_command(
        [
            "scp", "-q", "-P", str(port), "-o", "StrictHostKeyChecking=no",
            f"{host}:{remote_dir}/.spatialacc_semantic_job.json", str(job_path),
        ],
        timeout_sec,
    )
    saved_job = read_json(job_path) if job_download.returncode == 0 else {}
    replay_live = {
        "verification_layer": "layer3_real_board_axi_ddr",
        "status": "running",
        "phase": "fast_replay_restore",
        "input_fingerprint_sha256": saved_job.get("input_fingerprint_sha256"),
        "remote_workdir": remote_dir,
        "simulator_path": simulator_path,
    }
    replay_binding = board_run_binding(replay_live)
    if replay_binding:
        try:
            activate_live_state_slot(
                run_dir,
                "board_run",
                board_run_status(replay_live),
                binding=replay_binding,
            )
        except OSError:
            pass
    command, outputs, command_errors = saved_replay_command(saved_job, replay)
    if command is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_validation",
            "failure_class": "fast_replay_saved_job_invalid",
            "errors": command_errors or ["saved replay command is unavailable"],
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
            "stderr_tail": job_download.stderr[-4000:],
        }

    native_snapshot = str(replay.get("native_snapshot_path") or "")
    native_snapshot_files = str(replay.get("native_snapshot_files_path") or "")
    required_files = [
        simulator_path,
        native_snapshot,
        f"{native_snapshot}.ucli",
        NATIVE_CHECKPOINT_RESTORE_TCL.as_posix(),
    ]
    availability = run_transfer_command(
        [
            "ssh", "-p", str(port), "-o", "StrictHostKeyChecking=no", host,
            "cd " + shlex.quote(remote_dir) + " && " + " && ".join(
                f"test -f {shlex.quote(str(path))}" for path in required_files
            ) + f" && test -d {shlex.quote(native_snapshot_files)}"
            + f" && test -x {shlex.quote(simulator_path)}",
        ],
        timeout_sec,
    )
    if (
        restore_upload.returncode != 0
        or observation_upload.returncode != 0
        or availability.returncode != 0
    ):
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_validation",
            "failure_class": "fast_replay_remote_artifact_missing",
            "errors": [
                "saved replay simulator, native snapshot, restore script, or current observation selection is missing on the remote host"
            ],
            "remote_workdir": remote_dir,
            "simulator_path": simulator_path,
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
            "stderr_tail": availability.stderr[-4000:],
        }

    execution_outputs = saved_job.get("execution_outputs", {})
    execution_outputs = (
        execution_outputs if isinstance(execution_outputs, dict) else {}
    )
    progress_row = execution_outputs.get("progress_event_log", {})
    progress_row = progress_row if isinstance(progress_row, dict) else {}
    progress_path = safe_relative_path(progress_row.get("path"))
    boundary_row = execution_outputs.get("boundary_trace", {})
    boundary_row = boundary_row if isinstance(boundary_row, dict) else {}
    boundary_path = safe_relative_path(boundary_row.get("path"))
    simulation_row = execution_outputs.get("simulation_log", {})
    simulation_row = simulation_row if isinstance(simulation_row, dict) else {}
    simulation_path = safe_relative_path(simulation_row.get("path"))
    checkpoint_id = str(replay["checkpoint_manifest"].get("checkpoint_id") or "replay")
    live_progress_observer = (
        LiveProgressObserver(
            host=host,
            port=port,
            run_dir=run_dir,
            remote_path=progress_path,
            fingerprint=(
                f"{saved_job.get('input_fingerprint_sha256')}:"
                f"native_fast_replay:{checkpoint_id}"
            ),
            progress_contract=cctg_progress_contract(run_dir, {}),
            native_loop_report_path=outputs["restore_log"],
            live_namespace=f"native_fast_replay_{checkpoint_id[:12]}",
        )
        if progress_path is not None
        else None
    )

    replay_job_state = remote_background_job_state(
        host,
        port,
        remote_dir,
        out_dir,
        "vcs_fast_replay_restore",
    )
    if replay_job_state.get("certainty") != "determinate":
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "fail",
            "phase": "fast_replay_observation_epoch",
            "failure_class": "fast_replay_remote_state_indeterminate",
            "errors": ["cannot safely bind the current fast replay job state"],
            "remote_workdir": remote_dir,
            "remote_tool_was_not_started": True,
            "second_vcs_compile_was_not_launched": True,
        }

    signal_paths = {
        name: relative
        for name, relative in (
            ("progress_event_log", progress_path),
            ("boundary_trace", boundary_path),
        )
        if relative is not None
    }
    current_signal_outputs: dict[str, dict[str, Any]] = {}
    if replay_job_state.get("state") == "running":
        if live_progress_observer is not None:
            live_progress_observer.bind_or_begin_epoch(remote_dir)
    else:
        # A completed detached restore has a terminal marker with the fixed
        # label.  It must not be mistaken for the next replay attempt.
        if replay_job_state.get("state") == "done":
            clear_job = run_transfer_command(
                [
                    "ssh",
                    "-p",
                    str(port),
                    "-o",
                    "StrictHostKeyChecking=no",
                    host,
                    (
                        f"cd {shlex.quote(remote_dir)} && rm -f -- "
                        ".spatialacc_vcs_fast_replay_restore.pid "
                        ".spatialacc_vcs_fast_replay_restore.exit "
                        ".spatialacc_vcs_fast_replay_restore.stdout.log "
                        ".spatialacc_vcs_fast_replay_restore.stderr.log"
                    ),
                ],
                timeout_sec,
            )
            if clear_job.returncode != 0:
                return {
                    "schema_version": SCHEMA_VERSION,
                    "verification_layer": "layer3_real_board_axi_ddr",
                    "status": "fail",
                    "phase": "fast_replay_observation_epoch",
                    "failure_class": "fast_replay_stale_job_marker_cleanup_failed",
                    "errors": ["could not clear the completed replay job marker"],
                    "remote_workdir": remote_dir,
                    "remote_tool_was_not_started": True,
                    "second_vcs_compile_was_not_launched": True,
                }
        signal_start_bytes: dict[Path, int] = {}
        signal_start_metadata: dict[Path, dict[str, int]] = {}
        for name, relative in signal_paths.items():
            metadata = remote_file_metadata(
                host=host,
                port=port,
                remote_dir=remote_dir,
                relative=relative,
                timeout_sec=timeout_sec,
            )
            if metadata is None:
                return {
                    "schema_version": SCHEMA_VERSION,
                    "verification_layer": "layer3_real_board_axi_ddr",
                    "status": "fail",
                    "phase": "fast_replay_observation_epoch",
                    "failure_class": "fast_replay_signal_epoch_start_unavailable",
                    "errors": [f"cannot bind the current {name} start position"],
                    "remote_workdir": remote_dir,
                    "remote_tool_was_not_started": True,
                    "second_vcs_compile_was_not_launched": True,
                }
            byte_count = metadata["byte_count"]
            signal_start_bytes[relative] = byte_count
            signal_start_metadata[relative] = metadata
            local_path = board_dir / relative
            _prepare_fresh_transfer_target(local_path)
            current_signal_outputs[name] = {
                "path": str(local_path),
                "epoch_start_byte": byte_count,
                "copied": False,
            }
        if live_progress_observer is not None:
            live_progress_observer.begin_epoch(
                remote_dir,
                remote_start_byte=signal_start_bytes.get(progress_path, 0),
                signal_start_bytes=signal_start_bytes,
                signal_start_metadata=signal_start_metadata,
            )
        if simulation_path is not None:
            _prepare_fresh_transfer_target(board_dir / simulation_path)
        _prepare_fresh_transfer_target(
            board_dir / Path(str(saved_job.get("rtl_output_file") or "rtl_output.memh"))
        )

    # The simulator is detached on the remote host.  A local controller may
    # restart while that simulator is still running, so reattach by the stable
    # replay label before considering a new launch.  This preserves one real
    # Layer-3 run and prevents duplicate token streams.
    simulate_result = run_or_recover_remote_command(
        host=host,
        port=port,
        command=command,
        remote_dir=remote_dir,
        cwd=out_dir,
        timeout_sec=timeout_sec,
        label="vcs_fast_replay_restore",
        progress_callback=live_progress_observer,
    )

    copied: dict[str, Path] = {}
    copies: dict[str, bool] = {}
    for name, relative in outputs.items():
        local_path = board_dir / "fast_replay" / relative
        _prepare_fresh_transfer_target(local_path)
        copied[name] = local_path
        transfer = run_transfer_command(
            [
                "scp", "-q", "-P", str(port), "-o", "StrictHostKeyChecking=no",
                f"{host}:{remote_dir}/{relative.as_posix()}", str(local_path),
            ],
            timeout_sec,
        )
        copies[name] = transfer.returncode == 0 and local_path.is_file()

    observation_epoch = (
        live_progress_observer.epoch()
        if live_progress_observer is not None
        else {}
    )
    if progress_path is not None and live_progress_observer is not None:
        progress_local = board_dir / progress_path
        _prepare_fresh_transfer_target(progress_local)
        if live_progress_observer.raw_path.is_file():
            shutil.copy2(live_progress_observer.raw_path, progress_local)
        current_signal_outputs["progress_event_log"] = {
            "path": str(progress_local),
            "copied": progress_local.is_file(),
            "epoch_start_byte": observation_epoch.get("signal_start_bytes", {}).get(
                progress_path.as_posix()
            ),
        }
    if boundary_path is not None:
        boundary_local = board_dir / boundary_path
        start_bytes = observation_epoch.get("signal_start_bytes", {})
        start_byte = start_bytes.get(boundary_path.as_posix())
        start_metadata = observation_epoch.get("signal_start_metadata", {})
        start_metadata = (
            start_metadata.get(boundary_path.as_posix(), {})
            if isinstance(start_metadata, dict)
            else {}
        )
        if isinstance(start_byte, int) and start_byte >= 0:
            current_metadata = remote_file_metadata(
                host=host,
                port=port,
                remote_dir=remote_dir,
                relative=boundary_path,
                timeout_sec=timeout_sec,
            )
            if (
                isinstance(current_metadata, dict)
                and isinstance(start_metadata, dict)
                and isinstance(start_metadata.get("device"), int)
                and isinstance(start_metadata.get("inode"), int)
                and (
                    current_metadata.get("device") != start_metadata.get("device")
                    or current_metadata.get("inode") != start_metadata.get("inode")
                    or int(current_metadata.get("byte_count") or 0) < start_byte
                )
            ):
                start_byte = 0
            transfer = copy_remote_file_suffix(
                host=host,
                port=port,
                remote_dir=remote_dir,
                relative=boundary_path,
                start_byte=start_byte,
                destination=boundary_local,
                timeout_sec=timeout_sec,
            )
            current_signal_outputs["boundary_trace"] = {
                "path": str(boundary_local),
                "copied": transfer.returncode == 0 and boundary_local.is_file(),
                "epoch_start_byte": start_byte,
            }
    if simulation_path is not None and copies.get("restore_log"):
        current_simulation_log = board_dir / simulation_path
        _prepare_fresh_transfer_target(current_simulation_log)
        shutil.copy2(copied["restore_log"], current_simulation_log)

    simulation_log = copied.get("restore_log", Path())
    runtime_signal_trace_path = (
        board_dir / "fast_replay" / "reports" / "runtime_signal_trace.json"
    )
    runtime_signal_trace = summarize_runtime_stage_trace_log(
        simulation_log,
        boundary_trace_path=(
            Path(
                str(
                    current_signal_outputs.get("boundary_trace", {}).get("path")
                    or ""
                )
            )
            if isinstance(current_signal_outputs.get("boundary_trace"), dict)
            else None
        ),
        selection_path=(
            run_dir
            / "verification"
            / "adaptive_observation"
            / "current_selection.json"
        ),
    )
    runtime_signal_trace_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(runtime_signal_trace_path, runtime_signal_trace)
    current_signal_outputs["runtime_signal_trace"] = {
        "path": str(runtime_signal_trace_path),
        "copied": runtime_signal_trace.get("status") == "ready",
        "current_epoch_only": True,
    }
    simulate_result = apply_simulation_terminal_log_result(
        simulate_result, simulation_log
    )
    restore_text = (
        simulation_log.read_text(encoding="utf-8", errors="ignore")
        if simulation_log.is_file()
        else ""
    )
    restore_marker = "SPATIALACC_NATIVE_CHECKPOINT_RESTORE_PASS"
    restore_index = restore_text.find(restore_marker)
    observation_rebind_marker = "SPATIALACC_NATIVE_CHECKPOINT_OBSERVATION_REBIND"
    observation_rebind_index = restore_text.find(observation_rebind_marker)
    observation_logs_rebound = (
        restore_index >= 0 and observation_rebind_index > restore_index
    )
    board_progress_after_restore = (
        restore_index >= 0
        and "SPATIALACC_BOARD_PROGRESS" in restore_text[
            restore_index + len(restore_marker) :
        ]
    )
    restore_errors: list[str] = []
    if restore_index < 0:
        restore_errors.append("VCS did not report a completed native restore")

    checkpoint = replay["checkpoint_manifest"]
    # Native VCS owns snapshot validity.  The single hard condition is its
    # successful restore marker; observation rebinding and later board progress
    # remain visible diagnostics and never invalidate an otherwise usable state.
    restored = restore_index >= 0
    hardware_validation_status = str(simulate_result.get("status") or "fail")
    hardware_validation_passed = hardware_validation_status == "pass"
    return {
        "schema_version": SCHEMA_VERSION,
        "verification_layer": "layer3_real_board_axi_ddr",
        # A native restore is confirmed by its marker followed by real board
        # progress.  Later DUT or AXI failures belong to this Layer-3 run;
        # they must reach the Agent without invalidating the reusable state.
        "status": (
            "checkpoint_restore_complete"
            if restored and hardware_validation_passed
            else "fail"
        ),
        "hardware_validation_status": hardware_validation_status,
        "stage_pass_eligible": False,
        "phase": "fast_replay_restore_check",
        "summary": (
            "saved Layer-3 simulator restored and ran without a VCS compile or weight load"
            if restored and hardware_validation_passed
            else (
                "saved Layer-3 simulator restored, then the board run reported a hardware failure"
                if restored
                else "saved Layer-3 simulator restore did not complete"
            )
        ),
        "simulation_execution_identity": checkpoint.get("execution_identity", {}),
        "checkpoint_execution": {
            "status": "pass" if restored else "fail",
            "mode": "native_exact_model",
            "enabled": True,
            "restore_check": str(os.environ.get("SPATIALACC_FAST_REPLAY_RESTORE_CHECK") or "") == "1",
        },
        "checkpoint_artifacts": {
            "status": "pass" if restored else "fail",
            "mode": "native_exact_model",
            "restore_check": str(os.environ.get("SPATIALACC_FAST_REPLAY_RESTORE_CHECK") or "") == "1",
            "restore_log": str(simulation_log),
            "native_restore_marker_seen": restore_index >= 0,
            "observation_logs_rebound": observation_logs_rebound,
            "board_progress_after_restore": board_progress_after_restore,
            "errors": restore_errors,
            "restored_simulator_status": hardware_validation_status,
        },
        "fast_replay_used": True,
        "compile_reused": True,
        "weight_load_skipped": True,
        "second_vcs_compile_was_not_launched": True,
        "remote_workdir": remote_dir,
        "simulator_path": simulator_path,
        "compile": {
            "status": "pass",
            "reused": True,
            "summary": "reused saved remote VCS simulator; no VCS compile was launched",
        },
        "run": simulate_result,
        "live_progress": (
            live_progress_observer.report()
            if live_progress_observer is not None
            else {}
        ),
        "observation_epoch": observation_epoch,
        "current_signal_outputs": current_signal_outputs,
        "runtime_signal_trace": runtime_signal_trace,
        "outputs": {
            name: {"path": str(path), "copied": copies.get(name, False)}
            for name, path in copied.items()
        }
        | {
            "runtime_signal_trace": {
                "path": str(runtime_signal_trace_path),
                "copied": runtime_signal_trace.get("status") == "ready",
            }
        },
        "checkpoint_restore_marker_seen": restore_index >= 0,
        "checkpoint_observation_logs_rebound": observation_logs_rebound,
        "board_progress_after_restore": board_progress_after_restore,
    }


def _execute_board_vcs(run_dir: Path, timeout_sec: int) -> dict[str, Any]:
    if str(os.environ.get("SPATIALACC_FAST_REPLAY_RECAPTURE") or "") == "1":
        return execute_saved_fast_recapture(run_dir, timeout_sec)
    fast_replay_requested = (
        str(os.environ.get("SPATIALACC_FAST_REPLAY") or "") == "1"
    )
    if fast_replay_requested:
        return execute_saved_fast_replay(run_dir, timeout_sec)
    # A completed or abandoned cold job can leave a fixed job-contract path
    # behind.  A confirmed replay deliberately starts a new simulation in its
    # saved remote directory, so it must never attach that stale pending job.
    pending_job = None if fast_replay_requested else pending_exact_board_job(run_dir)
    if pending_job is not None:
        prior_report = read_json(
            run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
        )
        needs_full_collection = (
            prior_report.get("input_fingerprint_sha256")
            == pending_job["job"].get("input_fingerprint_sha256")
            and prior_report.get("phase") == "active_exact_job_collection"
            and prior_report.get("failure_class")
            == "active_exact_job_terminal_acceptance_required"
        )
        if not needs_full_collection:
            # Replace any older fixed-path report before attaching to the
            # current contract.  Do not overwrite the completion handoff for
            # this exact job before its captured checkpoint is collected.
            write_pending_exact_board_job_report(run_dir, pending_job)
        # A completed job keeps its terminal handoff report, but it still must
        # be attached once to collect artifacts and persist its checkpoint.
        # Skipping this call stranded a valid native snapshot and incorrectly
        # sent the next loop toward a new cold capture.
        attached = execute_pending_exact_board_job(
            run_dir, timeout_sec, pending_job
        )
        if attached is not None:
            return attached
    manifest, resolved, errors = validate_manifest(run_dir)
    out_dir = run_dir / "verification" / "vcs"
    out_dir.mkdir(parents=True, exist_ok=True)
    if errors:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "phase": "manifest_validation",
            "errors": errors,
            "exact_board_preflight": resolved["exact_board_preflight"],
            "validation_evidence": resolved["evidence"],
            "weight_binding_evidence": resolved["weight_binding_evidence"],
        }
    checkpoint_plan = checkpoint_execution_plan(run_dir, manifest)
    if checkpoint_plan.get("status") != "pass":
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "phase": "checkpoint_contract_validation",
            "failure_class": "simulation_checkpoint_capability_missing_or_invalid",
            "errors": checkpoint_plan.get("errors", []),
            "checkpoint_execution": checkpoint_plan,
            "remote_tool_was_not_started": True,
        }
    tool = tool_profile(run_dir)
    host = str(tool.get("host") or "")
    port = int(tool.get("port") or 22)
    executable = str(tool.get("executable") or "")
    if not host or not executable:
        return {"schema_version": SCHEMA_VERSION, "status": "fail", "phase": "tool_resolution", "errors": ["Stage0 VCS host/executable is missing"]}

    stage_dir = run_dir / "verification" / "board_simulation" / "vcs_stage"
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    sources_dir = stage_dir / "sources"
    artifacts_dir = stage_dir / "artifacts"
    sources_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)
    stage_current_observation_selection(run_dir, stage_dir)
    staged_checkpoint_inputs = stage_checkpoint_inputs(checkpoint_plan, stage_dir)
    fast_replay = checkpoint_plan.get("fast_replay", {})
    fast_replay = fast_replay if isinstance(fast_replay, dict) else {}
    staged_source_paths: dict[str, Path] = {}
    staged_targets: dict[str, str] = {}
    for entry in resolved["source_entries"]:
        source = entry["path"]
        relative = Path(str(entry.get("staged_path") or source.name))
        if relative.is_absolute() or ".." in relative.parts:
            return {"schema_version": SCHEMA_VERSION, "status": "fail", "phase": "manifest_validation", "errors": [f"unsafe staged source path: {relative}"]}
        target_relative = Path("sources") / relative
        target = stage_dir / target_relative
        if target_relative.as_posix() in staged_targets:
            return {"schema_version": SCHEMA_VERSION, "status": "fail", "phase": "manifest_validation", "errors": [f"duplicate staged source path: {relative}"]}
        staged_targets[target_relative.as_posix()] = entry["sha256"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        staged_source_paths[str(entry["source_id"])] = target_relative
    staged_artifacts = {}
    for name, source in resolved["artifact_paths"].items():
        target_relative = Path("artifacts") / f"{name}{source.suffix}"
        target = stage_dir / target_relative
        if target_relative.as_posix() in staged_targets:
            return {"schema_version": SCHEMA_VERSION, "status": "fail", "phase": "manifest_validation", "errors": [f"duplicate staged artifact path: {target_relative}"]}
        staged_targets[target_relative.as_posix()] = sha256_file(source)
        shutil.copy2(source, target)
        staged_artifacts[name] = target
    vcs = manifest.get("vcs", {})
    compile_plan = resolved["vcs_compile_plan"]
    fixture_staging = resolved["external_fixture_staging"]
    for entry in fixture_staging["files"]:
        target_relative = entry["staged_path"]
        target_key = target_relative.as_posix()
        existing_hash = staged_targets.get(target_key)
        if existing_hash is not None:
            if existing_hash != entry["sha256"]:
                return {"schema_version": SCHEMA_VERSION, "status": "fail", "phase": "manifest_validation", "errors": [f"external fixture staged path has conflicting payload: {target_key}"]}
            continue
        target = stage_dir / target_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry["path"], target)
        staged_targets[target_key] = entry["sha256"]
    command_cwds = sorted(
        {command["cwd"] for command in compile_plan["commands"]},
        key=lambda path: path.as_posix(),
    )
    for entry in [
        *fixture_staging["runtime_files"],
        *resolved["sample_runtime_auxiliary"],
    ]:
        for cwd in command_cwds:
            target_relative = cwd / entry["runtime_staged_path"]
            target_key = target_relative.as_posix()
            existing_hash = staged_targets.get(target_key)
            if existing_hash is not None:
                if existing_hash != entry["sha256"]:
                    return {"schema_version": SCHEMA_VERSION, "status": "fail", "phase": "manifest_validation", "errors": [f"runtime fixture path has conflicting payload in command cwd: {target_key}"]}
                continue
            target = stage_dir / target_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry["path"], target)
            staged_targets[target_key] = entry["sha256"]
    library_setup_error = materialize_vcs_library_setup(
        stage_dir,
        compile_plan["commands"],
        fixture_staging["synopsys_sim_setup"],
        staged_targets,
    )
    if library_setup_error:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "phase": "manifest_validation",
            "errors": [library_setup_error],
        }
    fpga_ip_runtime: dict[str, Any] = {"status": "not_used"}
    if fast_replay.get("used") is not True:
        try:
            fpga_ip_runtime = stage_fpga_ip_runtime(
                run_dir,
                stage_dir,
                read_json(run_dir / "input" / "tool_profile.json"),
            )
        except (OSError, ValueError, KeyError) as exc:
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "fail",
                "phase": "fpga_ip_runtime_staging",
                "failure_class": "fpga_ip_runtime_contract_failure",
                "errors": [str(exc)],
                "remote_tool_was_not_started": True,
            }
    command_shells: list[str] = []
    vcs_compile_jobs = semantic_vcs_compile_jobs()
    vcs_loop_report_enabled = environment_flag("SPATIALACC_VCS_LOOP_REPORT")
    vcs_parallel_args_applied: list[str] = []
    for command in compile_plan["commands"]:
        cwd = command["cwd"]
        (stage_dir / cwd).mkdir(parents=True, exist_ok=True)
        argv: list[str] = []
        for token in command["argv"]:
            if isinstance(token, str):
                argv.append(token)
            elif "source_id" in token:
                source_path = staged_source_paths[token["source_id"]]
                argv.append(os.path.relpath(source_path, start=cwd).replace(os.sep, "/"))
            else:
                include_path = fixture_staging["include_directories"][
                    token["include_dir_id"]
                ]
                relative_include = os.path.relpath(include_path, start=cwd).replace(
                    os.sep, "/"
                )
                argv.append(f"+incdir+{relative_include}")
        if (
            str(command.get("phase") or "") == "elaborate"
            and Path(str(command.get("executable") or "")).name == "vcs"
            and vcs_compile_jobs > 1
            and not any(re.fullmatch(r"-j\d+", value) for value in argv)
        ):
            parallel_arg = f"-j{vcs_compile_jobs}"
            argv.insert(0, parallel_arg)
            vcs_parallel_args_applied.append(parallel_arg)
        if (
            vcs_loop_report_enabled
            and str(command.get("phase") or "") == "elaborate"
            and Path(str(command.get("executable") or "")).name == "vcs"
            and "+vcs+loopreport" not in argv
        ):
            argv.append("+vcs+loopreport")
        if (
            str(command.get("phase") or "") == "compile"
            and Path(str(command.get("executable") or "")).name == "vlogan"
            and "+incdir+../sources" in argv
        ):
            # The framework-owned generated-source compile is the one place
            # where the current Vivado IP/XPM model filelist is added.  Other
            # sample-project compile groups must not see it, or the same IP
            # modules would be defined more than once.
            argv.extend(shlex.split(ip_vcs_filelist_argument()))
        checkpoint_compile_defines = checkpoint_adapter_compile_define_args(
            checkpoint_plan,
            str(command.get("executable") or ""),
        )
        for define in reversed(checkpoint_compile_defines):
            if define not in argv:
                argv.insert(0, define)
        env_argv = [
            "env",
            *(f"{key}={value}" for key, value in sorted(command["env"].items())),
        ] if command["env"] else []
        command_argv = [*env_argv, str(command["executable"]), *argv]
        if (
            checkpoint_plan.get("adapter_enabled") is True
            and str(command.get("phase") or "") == "elaborate"
        ):
            command_argv.extend(
                checkpoint_adapter_elaboration_args(
                    checkpoint_plan,
                    stage_dir,
                    cwd,
                )
            )
        command_shells.append(
            f"(cd {shlex.quote(cwd.as_posix())} && "
            f"{' '.join(shlex.quote(value) for value in command_argv)})"
        )
    plusargs = []
    for key, artifact_name in vcs.get("runtime_plusargs", {}).items():
        if str(artifact_name) not in staged_artifacts:
            return {"schema_version": SCHEMA_VERSION, "status": "fail", "phase": "manifest_validation", "errors": [f"runtime plusarg {key} references unknown artifact {artifact_name}"]}
        plusargs.append(f"+{key}=artifacts/{staged_artifacts[str(artifact_name)].name}")
    plusargs.append(
        "+SPATIALACC_OBSERVATION_SELECTION=observation/current_selection.json"
    )
    workload_plusargs = list(plusargs)
    plusargs.extend(checkpoint_runtime_plusargs(checkpoint_plan))
    if checkpoint_plan.get("mode") == "cold_capture":
        capture_tcl = stage_dir / NATIVE_CHECKPOINT_CAPTURE_TCL
        restore_tcl = stage_dir / NATIVE_CHECKPOINT_RESTORE_TCL
        capture_tcl.parent.mkdir(parents=True, exist_ok=True)
        capture_tcl.write_text(native_checkpoint_capture_tcl(), encoding="utf-8")
        restore_tcl.write_text(native_checkpoint_restore_tcl(), encoding="utf-8")
    if vcs_loop_report_enabled:
        plusargs.append("+vcs+loopreport")
        workload_plusargs.append("+vcs+loopreport")
    output_plan = resolved["execution_output_plan"]
    compile_log_relative = output_plan["compile_log"]["path"]
    simulation_log_relative = output_plan["simulation_log"]["path"]
    planned_jsonl_paths = {
        output_plan["progress_event_log"]["path"],
        Path(str(manifest["boundary_trace_file"])),
    }
    supplemental_jsonl_paths = supplemental_jsonl_output_paths(
        resolved.get("testbench_path"),
        planned_jsonl_paths,
    )
    supplemental_vcd_paths = supplemental_vcd_output_paths(
        resolved.get("testbench_path")
    )
    runtime_loader_spec = output_plan.get("runtime_loader_report")
    runtime_loader_paths = (
        [runtime_loader_spec["path"]]
        if isinstance(runtime_loader_spec, dict)
        else []
    )
    performance_counter_spec = output_plan.get("performance_counter_report")
    performance_counter_paths = (
        [performance_counter_spec["path"]]
        if isinstance(performance_counter_spec, dict)
        else []
    )
    output_parents = {
        path.parent.as_posix()
        for path in (
            compile_log_relative,
            simulation_log_relative,
            output_plan["progress_event_log"]["path"],
            output_plan["elaborated_hierarchy_report"]["path"],
            output_plan["pipeline_overlap_report"]["path"],
            *runtime_loader_paths,
            *performance_counter_paths,
            *(row["path"] for row in output_plan["protocol_monitor_reports"]),
            *supplemental_jsonl_paths,
            *supplemental_vcd_paths,
        )
        if path.parent != Path(".")
    }
    checkpoint_outputs = checkpoint_plan.get("contract", {}).get("outputs", {})
    if checkpoint_plan.get("enabled") is True and isinstance(checkpoint_outputs, dict):
        for row in checkpoint_outputs.values():
            relative = safe_relative_path(row.get("path")) if isinstance(row, dict) else None
            if relative is not None and relative.parent != Path("."):
                output_parents.add(relative.parent.as_posix())
        output_parents.add("checkpoint/state")
        output_parents.add("checkpoint")
    prepare_output_dirs = (
        "mkdir -p " + " ".join(shlex.quote(value) for value in sorted(output_parents)) + "; "
        if output_parents
        else ""
    )
    simulator_path = (
        compile_plan["commands"][-1]["cwd"] / compile_plan["output"]
    )
    remote_output_paths = [
        compile_log_relative,
        simulation_log_relative,
        output_plan["progress_event_log"]["path"],
        output_plan["elaborated_hierarchy_report"]["path"],
        output_plan["pipeline_overlap_report"]["path"],
        *runtime_loader_paths,
        *performance_counter_paths,
        *(row["path"] for row in output_plan["protocol_monitor_reports"]),
        *supplemental_jsonl_paths,
        *supplemental_vcd_paths,
        Path(str(manifest["rtl_output_file"])),
        Path(str(manifest["boundary_trace_file"])),
        simulator_path,
    ]
    if checkpoint_plan.get("enabled") is True and isinstance(checkpoint_outputs, dict):
        remote_output_paths.extend(
            relative
            for row in checkpoint_outputs.values()
            if isinstance(row, dict)
            and (relative := safe_relative_path(row.get("path"))) is not None
        )
    if checkpoint_plan.get("mode") == "cold_capture":
        remote_output_paths.append(NATIVE_CHECKPOINT_SNAPSHOT)
    remove_stale_outputs = "rm -f -- " + " ".join(
        shlex.quote(path.as_posix()) for path in remote_output_paths
    ) + "; "
    if checkpoint_plan.get("mode") == "cold_capture":
        remove_stale_outputs += (
            f"rm -rf -- {shlex.quote(NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix())}; "
        )
    compile_command = (
        prepare_output_dirs
        + remove_stale_outputs
        + f": > {shlex.quote(compile_log_relative.as_posix())}; set -e; "
        + (
            fpga_ip_runtime.get("provision_command", "")
            + " >> "
            + shlex.quote(compile_log_relative.as_posix())
            + " 2>&1; "
            if fpga_ip_runtime.get("status") == "ready"
            else ""
        )
        + "; ".join(
            f"{command} >> {shlex.quote(compile_log_relative.as_posix())} 2>&1"
            for command in command_shells
        )
    )
    simulator_path_text = simulator_path.as_posix()
    simulator_invocation = (
        f"./{shlex.quote(simulator_path_text)} "
        + " ".join(shlex.quote(value) for value in plusargs)
    )
    if checkpoint_plan.get("mode") == "cold_capture":
        simulator_invocation = (
            f"./{shlex.quote(simulator_path_text)} -ucli "
            f"-do {shlex.quote(NATIVE_CHECKPOINT_CAPTURE_TCL.as_posix())} "
            + " ".join(shlex.quote(value) for value in plusargs)
        )
    simulate_command = (
        prepare_output_dirs
        + simulator_invocation
        + f" > {shlex.quote(simulation_log_relative.as_posix())} 2>&1"
    )
    if fast_replay.get("used") is True:
        # Keep the compiled simulator and captured state intact.  Only outputs
        # produced by this replay are cleared before restoring the snapshot.
        replay_outputs = [
            simulation_log_relative,
            output_plan["progress_event_log"]["path"],
            output_plan["elaborated_hierarchy_report"]["path"],
            output_plan["pipeline_overlap_report"]["path"],
            *runtime_loader_paths,
            *(row["path"] for row in output_plan["protocol_monitor_reports"]),
            *supplemental_jsonl_paths,
            *supplemental_vcd_paths,
            Path(str(manifest["rtl_output_file"])),
            Path(str(manifest["boundary_trace_file"])),
        ]
        checkpoint_outputs_for_replay = checkpoint_plan.get("contract", {}).get(
            "outputs", {}
        )
        if isinstance(checkpoint_outputs_for_replay, dict):
            restore_row = checkpoint_outputs_for_replay.get("restore_report", {})
            restore_path = (
                safe_relative_path(restore_row.get("path"))
                if isinstance(restore_row, dict)
                else None
            )
            if restore_path is not None:
                replay_outputs.append(restore_path)
        replay_cleanup = "rm -f -- " + " ".join(
            shlex.quote(path.as_posix()) for path in replay_outputs
        ) + "; "
        simulate_command = (
            prepare_output_dirs
            + replay_cleanup
            + f"./{shlex.quote(simulator_path_text)} "
            + " ".join(shlex.quote(value) for value in plusargs)
            + f" > {shlex.quote(simulation_log_relative.as_posix())} 2>&1"
        )
    payload = [
        {"path": path.relative_to(stage_dir).as_posix(), "sha256": sha256_file(path)}
        for path in sorted(stage_dir.rglob("*"))
        if path.is_file() and path.name != REMOTE_SEMANTIC_JOB_CONTRACT
    ]
    try:
        remote_stage_root = board_remote_stage_root(manifest, run_dir, host)
    except ValueError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "phase": "manifest_validation",
            "errors": [str(exc)],
        }
    fingerprint_material = {
        "schema_version": "spatialaccagent.board_remote_job_identity.v1",
        "preflight_manifest_projection_sha256": preflight_manifest_projection_sha256(manifest),
        "source_identity_sha256": sha256_file(Path(resolved["identity_path"])),
        "source_closure_sha256": manifest.get("source_closure_sha256"),
        "compile_source_set_sha256": manifest.get("compile_source_set_sha256"),
        "vcs_compile_plan_sha256": compile_plan["sha256"],
        "vcs_compile_plan": compile_plan["plan"],
        "verified_compile_source_ids": sorted(
            resolved["exact_board_preflight"].get("verified_compile_source_ids", [])
        ),
        "tool_profile": {
            "name": tool.get("name"),
            "role": tool.get("role"),
            "scope": tool.get("scope"),
            "host": host,
            "port": port,
            "executable": executable,
        },
        "top_module": manifest.get("top_module"),
        "compile_command": compile_command,
        "simulate_command": simulate_command,
        "execution_outputs": manifest.get("execution_outputs"),
        "supplemental_observation_outputs": [
            path.as_posix()
            for path in (*supplemental_jsonl_paths, *supplemental_vcd_paths)
        ],
        "vcs_native_loop_report_enabled": vcs_loop_report_enabled,
        "checkpoint_execution": {
            key: checkpoint_plan.get(key)
            for key in (
                "mode",
                "enabled",
                "candidate_screening",
                "acceptance_eligible",
                "request_sha256",
            )
        },
        "staged_checkpoint_inputs": staged_checkpoint_inputs,
        "fpga_ip_runtime": {
            key: value
            for key, value in fpga_ip_runtime.items()
            if key not in {"provision_command"}
        },
        "payload": payload,
        "remote_stage_root": remote_stage_root,
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            fingerprint_material,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    replay_generation_sha256 = os.environ.get(
        FRESH_EXACT_BOARD_REPLAY_GENERATION_ENV, ""
    ).strip()
    try:
        remote_dir = exact_board_remote_workdir(
            remote_stage_root,
            fingerprint,
            replay_generation_sha256,
        )
    except ValueError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "phase": "runner_configuration",
            "errors": [str(exc)],
        }
    if fast_replay.get("used") is True:
        remote_dir = str(fast_replay.get("remote_workdir") or "")
        if not remote_dir:
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "fail",
                "phase": "fast_replay_validation",
                "failure_class": "fast_replay_remote_workdir_missing",
                "errors": ["confirmed fast replay has no remote work directory"],
                "remote_tool_was_not_started": True,
            }
    job_contract = {
        **fingerprint_material,
        "input_fingerprint_sha256": fingerprint,
        "remote_workdir": remote_dir,
    }
    if replay_generation_sha256:
        job_contract[
            "fresh_exact_source_replay_generation_sha256"
        ] = replay_generation_sha256
    job_contract_path = stage_dir / REMOTE_SEMANTIC_JOB_CONTRACT
    write_json(job_contract_path, job_contract)
    if fast_replay.get("used") is not True:
        write_pending_exact_board_job_report(
            run_dir,
            {
                "job": job_contract,
                "job_path": job_contract_path,
                "manifest_path": resolved["manifest_path"],
            },
        )
    live_progress_observer = LiveProgressObserver(
        host=host,
        port=port,
        run_dir=run_dir,
        remote_path=output_plan["progress_event_log"]["path"],
        fingerprint=fingerprint,
        progress_contract=cctg_progress_contract(run_dir, manifest),
        remote_time_probe_paths=supplemental_vcd_paths,
        native_loop_report_path=(
            simulation_log_relative if vcs_loop_report_enabled else None
        ),
    )

    recovered = None
    if fast_replay.get("used") is not True:
        recovered = recover_exact_remote_semantic_job(
            host,
            port,
            remote_stage_root,
            fingerprint,
            out_dir,
            job_contract_path,
            payload,
            timeout_sec,
            simulate_command,
            progress_callback=live_progress_observer,
        )
    if recovered is not None and recovered.get("recovery_state") == "indeterminate":
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "phase": "remote_recovery_indeterminate",
            "failure_class": recovered.get("failure_class"),
            "input_fingerprint_sha256": fingerprint,
            "remote_stage_root": remote_stage_root,
            "remote_job_reuse": recovered,
            "errors": [str(recovered.get("summary") or "remote board job recovery is indeterminate")],
        }

    ssh_base = ["ssh", "-p", str(port), "-o", "StrictHostKeyChecking=no", host]
    if fast_replay.get("used") is True:
        saved_simulator = str(fast_replay.get("simulator_path") or "")
        required_remote_files = [saved_simulator]
        required_remote_files.extend(
            row["staged_path"]
            for row in checkpoint_plan.get("staged_state_artifacts", [])
            if isinstance(row, dict) and row.get("staged_path")
        )
        availability = run_transfer_command(
            [
                *ssh_base,
                (
                    f"cd {shlex.quote(remote_dir)} && "
                    + " && ".join(
                        f"test -f {shlex.quote(str(path))}"
                        for path in required_remote_files
                    )
                    + f" && test -x {shlex.quote(saved_simulator)}"
                ),
            ],
            timeout_sec,
        )
        if availability.returncode != 0:
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "fail",
                "phase": "fast_replay_validation",
                "failure_class": "fast_replay_remote_artifact_missing",
                "errors": [
                    "saved fast replay simulator or checkpoint state is missing on the remote host"
                ],
                "remote_workdir": remote_dir,
                "simulator_path": saved_simulator,
                "fast_replay_used": False,
                "compile_reused": False,
                "weight_load_skipped": False,
                "second_vcs_compile_was_not_launched": True,
                "remote_tool_was_not_started": True,
                "stderr_tail": availability.stderr[-4000:],
            }
        compile_result = {
            "status": "pass",
            "returncode": 0,
            "reused": True,
            "summary": "reused the saved remote VCS simulator; no VCS compile was launched",
        }
        simulate_result = run_remote_background_command(
            host,
            port,
            simulate_command,
            remote_dir,
            out_dir,
            timeout_sec,
            "vcs_fast_replay_simulate",
            progress_callback=live_progress_observer,
        )
        remote_job_reuse = {
            "status": "pass",
            "fast_replay_used": True,
            "remote_workdir": remote_dir,
            "simulator_path": saved_simulator,
            "real_tool_was_not_relaunched": False,
            "second_vcs_compile_was_not_launched": True,
        }
    elif recovered is not None:
        remote_dir = str(recovered["remote_dir"])
        compile_result = recovered["compile"]
        simulate_result = recovered["simulate"]
        remote_job_reuse = {
            "status": "pass",
            "real_tool_was_not_relaunched": True,
            "remote_workdir": remote_dir,
            **dict(recovered.get("identity") or {}),
        }
    else:
        archive = (
            run_dir
            / "verification"
            / "board_simulation"
            / "vcs_stage.tar.gz"
        )
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(stage_dir, arcname="stage")
        prep = run_transfer_command([*ssh_base, f"mkdir -p {shlex.quote(remote_dir)}"], timeout_sec)
        if prep.returncode != 0:
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "fail",
                "phase": "remote_prepare",
                "input_fingerprint_sha256": fingerprint,
                "remote_job_preserved": True,
                "stderr_tail": prep.stderr[-4000:],
            }
        scp = run_transfer_command(
            [
                "scp",
                "-q",
                "-P",
                str(port),
                "-o",
                "StrictHostKeyChecking=no",
                str(archive),
                f"{host}:{remote_dir}/stage.tar.gz",
            ],
            timeout_sec,
        )
        if scp.returncode != 0:
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "fail",
                "phase": "remote_sync",
                "input_fingerprint_sha256": fingerprint,
                "remote_job_preserved": True,
                "stderr_tail": scp.stderr[-4000:],
            }
        extract = run_transfer_command(
            [
                *ssh_base,
                f"cd {shlex.quote(remote_dir)} && tar -xzf stage.tar.gz --strip-components=1",
            ],
            timeout_sec,
        )
        if extract.returncode != 0:
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "fail",
                "phase": "remote_extract",
                "input_fingerprint_sha256": fingerprint,
                "remote_job_preserved": True,
                "stderr_tail": extract.stderr[-4000:],
            }
        compile_result = run_remote_background_command(
            host,
            port,
            compile_command,
            remote_dir,
            out_dir,
            timeout_sec,
            "vcs_compile",
        )
        simulate_result = (
            run_remote_background_command(
                host,
                port,
                simulate_command,
                remote_dir,
                out_dir,
                timeout_sec,
                "vcs_simulate",
                progress_callback=live_progress_observer,
            )
            if compile_result.get("status") == "pass"
            else {"status": "not_run", "summary": "remote VCS compile failed"}
        )
        remote_job_reuse = {
            "status": "not_run",
            "real_tool_was_not_relaunched": False,
            "summary": "no exact completed or running remote board job matched the full payload",
        }
    persist_zero_time_livelock_recovery(
        run_dir,
        simulate_result,
        remote_workdir=remote_dir,
        input_fingerprint_sha256=fingerprint,
    )
    simulate_result = bind_zero_time_livelock_recovery(
        run_dir,
        simulate_result,
        remote_workdir=remote_dir,
        input_fingerprint_sha256=fingerprint,
    )
    board_dir = run_dir / "verification" / "board_simulation"

    def download_planned(relative: Path) -> tuple[Path, subprocess.CompletedProcess[str]]:
        local_path = board_dir / relative
        _prepare_fresh_transfer_target(local_path)
        result = run_transfer_command(
            [
                "scp",
                "-q",
                "-P",
                str(port),
                "-o",
                "StrictHostKeyChecking=no",
                f"{host}:{remote_dir}/{relative.as_posix()}",
                str(local_path),
            ],
            timeout_sec,
        )
        if result.returncode != 0:
            local_path.unlink(missing_ok=True)
        return local_path, result

    compile_log_path, compile_log_download = download_planned(compile_log_relative)
    simulation_log_path, simulation_log_download = download_planned(simulation_log_relative)
    progress_spec = output_plan["progress_event_log"]
    progress_event_path, progress_event_download = download_planned(
        progress_spec["path"]
    )
    progress_parsed = (
        read_complete_jsonl(progress_event_path)
        if progress_event_download.returncode == 0
        else {"records": [], "invalid_records": []}
    )
    progress_records = progress_parsed.get("records", [])
    progress_summary = summarize_progress_events(
        progress_records if isinstance(progress_records, list) else [],
        cctg_progress_contract(run_dir, manifest),
    )
    real_restore_progress_count = checkpoint_restore_real_progress_count(
        progress_records if isinstance(progress_records, list) else []
    )
    if (
        isinstance(progress_records, list)
        and progress_records
        and isinstance(progress_records[-1], dict)
    ):
        progress_summary["last_committed_progress_event"] = dict(
            progress_records[-1]
        )
    progress_event_log_valid = (
        progress_event_download.returncode == 0
        and progress_event_path.is_file()
        and progress_summary.get("record_count", 0) > 0
        and progress_summary.get("semantic_progress_event_count", 0) > 0
        and progress_summary.get("terminal_event_seen") is True
        and not progress_summary.get("validation_errors")
        and not progress_parsed.get("invalid_records")
    )
    simulate_result = apply_simulation_terminal_log_result(
        simulate_result, simulation_log_path
    )
    simulate_result["termination_provenance"] = simulation_termination_provenance(
        simulate_result,
        simulation_log_path,
        timeout_sec=timeout_sec,
        progress_summary=progress_summary,
        input_fingerprint_sha256=fingerprint,
        live_progress=live_progress_observer.report(),
    )
    supplemental_observation_artifacts: list[dict[str, Any]] = []
    for relative in supplemental_jsonl_paths:
        local_path, copy_result = download_planned(relative)
        copied = copy_result.returncode == 0 and local_path.is_file()
        supplemental_observation_artifacts.append(
            {
                "status": "ready" if copied else "missing",
                "artifact_kind": "jsonl_observation",
                "path": str(local_path),
                "relative_path": relative.as_posix(),
                "copied": copied,
                "sha256": sha256_file(local_path) if copied else None,
                "byte_count": local_path.stat().st_size if copied else 0,
                "summary": (
                    summarize_supplemental_jsonl(local_path) if copied else {}
                ),
            }
        )
    for relative in supplemental_vcd_paths:
        local_path, copy_result = download_planned(relative)
        copied = copy_result.returncode == 0 and local_path.is_file()
        summary = summarize_supplemental_vcd(local_path) if copied else {}
        supplemental_observation_artifacts.append(
            {
                "status": "ready" if copied else "missing",
                "artifact_kind": "vcd_simulation_time_probe",
                "path": str(local_path),
                "relative_path": relative.as_posix(),
                "copied": copied,
                "sha256": sha256_file(local_path) if copied else None,
                "byte_count": local_path.stat().st_size if copied else 0,
                "summary": summary,
            }
        )
    vcs_loop_report = {
        "enabled": vcs_loop_report_enabled,
        "native_loop_detected": False,
        "loop_detection_enabled_observed": False,
        "matched_simulation_log_markers": [],
        "artifact_count": 0,
    }
    if vcs_loop_report_enabled:
        simulation_text = (
            simulation_log_path.read_text(encoding="utf-8", errors="replace")
            if simulation_log_path.is_file()
            else ""
        )
        simulation_lower = simulation_text.lower()
        simulation_markers = [
            marker
            for marker in VCS_ZERO_DELAY_LOOP_MARKERS
            if marker in simulation_lower
        ]
        discovered = run_transfer_command(
            [
                *ssh_base,
                (
                    f"cd {shlex.quote(remote_dir)} && "
                    "find . -maxdepth 6 -type f -name 'loop-info-*.log' -print"
                ),
            ],
            timeout_sec,
        )
        loop_paths: list[Path] = []
        if discovered.returncode == 0:
            for value in discovered.stdout.splitlines():
                relative = safe_relative_path(value.strip().removeprefix("./"))
                if relative is not None and relative not in loop_paths:
                    loop_paths.append(relative)
                if len(loop_paths) >= 8:
                    break
        for relative in loop_paths:
            local_path, copy_result = download_planned(relative)
            copied = copy_result.returncode == 0 and local_path.is_file()
            summary = summarize_vcs_loop_report(local_path) if copied else {}
            supplemental_observation_artifacts.append(
                {
                    "status": "ready" if copied else "missing",
                    "artifact_kind": "vcs_native_zero_delay_loop_report",
                    "path": str(local_path),
                    "relative_path": relative.as_posix(),
                    "copied": copied,
                    "sha256": sha256_file(local_path) if copied else None,
                    "byte_count": local_path.stat().st_size if copied else 0,
                    "summary": summary,
                }
            )
        vcs_loop_report = {
            "enabled": True,
            "native_loop_detected": bool(simulation_markers or loop_paths),
            "loop_detection_enabled_observed": (
                "vcs loop detection: switching loop detection algorithm on"
                in simulation_lower
            ),
            "matched_simulation_log_markers": simulation_markers,
            "artifact_count": len(loop_paths),
            "discovery_status": "pass" if discovered.returncode == 0 else "fail",
            "discovery_stderr_tail": discovered.stderr[-2000:],
        }
        if not loop_paths:
            supplemental_observation_artifacts.append(
                {
                    "status": "not_observed",
                    "artifact_kind": "vcs_native_zero_delay_loop_report",
                    "relative_path": "loop-info-*.log",
                    "copied": False,
                    "byte_count": 0,
                    "summary": vcs_loop_report,
                }
            )
    copied_outputs = {}
    boundary_suffix = Path(str(manifest.get("boundary_trace_file") or "")).suffix
    for key, local_name in (
        ("rtl_output_file", "rtl_output.memh"),
        (
            "boundary_trace_file",
            "boundary_trace.jsonl" if boundary_suffix == ".jsonl" else "boundary_trace.json",
        ),
    ):
        remote_name = str(manifest[key])
        local_path = board_dir / local_name
        copy_result = run_transfer_command(
            ["scp", "-q", "-P", str(port), "-o", "StrictHostKeyChecking=no", f"{host}:{remote_dir}/{remote_name}", str(local_path)],
            timeout_sec,
        )
        copied_outputs[key] = {
            "path": str(local_path),
            "copied": copy_result.returncode == 0 and local_path.is_file(),
            "sha256": sha256_file(local_path) if copy_result.returncode == 0 and local_path.is_file() else None,
        }
    boundary_trace_local_path = Path(
        str(copied_outputs["boundary_trace_file"]["path"])
    )
    semantic_manifest_reference = manifest.get("semantic_testbench_manifest", {})
    boundary_observation_summary = summarize_boundary_trace_observations(
        boundary_trace_local_path,
        semantic_manifest_reference
        if isinstance(semantic_manifest_reference, dict)
        else {},
        manifest.get("testbench", {})
        if isinstance(manifest.get("testbench"), dict)
        else {},
        simulation_log_path,
    )
    boundary_observation_summary_path = (
        board_dir / "pipeline_boundary_observation_summary.json"
    )
    write_json(boundary_observation_summary_path, boundary_observation_summary)
    boundary_observation_passed = (
        boundary_observation_summary.get("status")
        in {"complete", "not_applicable"}
    )
    monitor_results: dict[str, dict[str, Any]] = {}
    monitor_payloads: dict[str, dict[str, Any]] = {}
    for spec in resolved["structured_monitor_specs"]:
        local_path, copy_result = download_planned(spec["remote_path"])
        report = read_json(local_path) if copy_result.returncode == 0 else {}
        missing_fields = sorted(set(spec["required_fields"]) - set(report))
        violations = report.get("violations")
        transaction_counts = report.get("transaction_counts")
        validated = (
            copy_result.returncode == 0
            and local_path.is_file()
            and report.get("schema_version") == spec["schema_version"]
            and report.get("status") == "pass"
            and isinstance(violations, list)
            and not violations
            and isinstance(transaction_counts, dict)
            and all(
                isinstance(transaction_counts.get(channel), int)
                and transaction_counts.get(channel, 0) > 0
                for channel in ("aw", "w", "b", "ar", "r")
            )
            and not missing_fields
        )
        monitor_payloads[spec["interface"]] = report
        monitor_results[spec["monitor_id"]] = {
            "status": "pass" if validated else "fail",
            "interface": spec["interface"],
            "path": str(local_path),
            "copied": copy_result.returncode == 0 and local_path.is_file(),
            "sha256": sha256_file(local_path) if copy_result.returncode == 0 and local_path.is_file() else None,
            "schema_version": report.get("schema_version"),
            "reported_status": report.get("status"),
            "violation_count": len(violations) if isinstance(violations, list) else None,
            "transaction_counts": transaction_counts if isinstance(transaction_counts, dict) else None,
            "missing_required_fields": missing_fields,
        }

    hierarchy_spec = output_plan["elaborated_hierarchy_report"]
    hierarchy_path, hierarchy_download = download_planned(hierarchy_spec["path"])
    hierarchy_payload = read_json(hierarchy_path) if hierarchy_download.returncode == 0 else {}
    hierarchy_report_valid = (
        hierarchy_download.returncode == 0
        and hierarchy_path.is_file()
        and hierarchy_payload.get("schema_version") == hierarchy_spec["schema_version"]
        and hierarchy_payload.get("status") == "pass"
        and isinstance(hierarchy_payload.get("evidence_refs"), list)
        and bool(hierarchy_payload.get("evidence_refs"))
    )
    pipeline_spec = output_plan["pipeline_overlap_report"]
    pipeline_path, pipeline_download = download_planned(pipeline_spec["path"])
    pipeline_payload = read_json(pipeline_path) if pipeline_download.returncode == 0 else {}
    pipeline_overlap_passed = (
        pipeline_download.returncode == 0
        and pipeline_path.is_file()
        and pipeline_payload.get("schema_version") == pipeline_spec["schema_version"]
        and pipeline_payload.get("status") == "pass"
        and pipeline_payload.get("pipeline_semantics")
        == "elastic_rate_insensitive_token_pipeline"
        and pipeline_payload.get("required_dependency_overlap_complete") is True
        and pipeline_payload.get(
            "all_planned_stages_participate_in_required_overlap"
        )
        is True
        and pipeline_payload.get("token_order_preserved") is True
        and pipeline_payload.get("serial_leaf_execution_observed") is False
        and pipeline_payload.get("stage_turnover_gaps_are_diagnostic") is True
        and pipeline_payload.get(
            "all_stages_same_cycle_concurrency_required"
        )
        is False
        and pipeline_payload.get("whole_sequence_barrier_observed") is False
        and isinstance(pipeline_payload.get("expected_stage_count"), int)
        and pipeline_payload.get("expected_stage_count", 0) > 0
        and pipeline_payload.get("observed_stage_count")
        == pipeline_payload.get("expected_stage_count")
        and isinstance(
            pipeline_payload.get("observed_different_token_overlap_count"), int
        )
        and pipeline_payload.get("observed_different_token_overlap_count", 0) > 0
    )
    if isinstance(runtime_loader_spec, dict):
        runtime_loader_path, runtime_loader_download = download_planned(
            runtime_loader_spec["path"]
        )
        runtime_loader_payload = (
            read_json(runtime_loader_path)
            if runtime_loader_download.returncode == 0
            else {}
        )
        runtime_loader_report_passed = (
            runtime_loader_download.returncode == 0
            and runtime_loader_path.is_file()
            and runtime_loader_payload.get("schema_version")
            == runtime_loader_spec["schema_version"]
            and runtime_loader_payload.get("status") == "pass"
        )
    else:
        runtime_loader_path = Path()
        runtime_loader_payload = {}
        runtime_loader_report_passed = True
    if isinstance(performance_counter_spec, dict):
        performance_counter_path, performance_counter_download = download_planned(
            performance_counter_spec["path"]
        )
        performance_counter_payload = (
            read_json(performance_counter_path)
            if performance_counter_download.returncode == 0
            else {}
        )
    else:
        performance_counter_path = Path()
        performance_counter_payload = {}

    checkpoint_artifact_result: dict[str, Any] = {
        "status": "not_run",
        "mode": checkpoint_plan.get("mode"),
        "summary": "checkpoint execution was not requested",
    }
    if checkpoint_plan.get("enabled") is True:
        checkpoint_artifact_result = {
            "status": "fail",
            "mode": checkpoint_plan.get("mode"),
            "errors": [],
        }
        if checkpoint_plan.get("mode") == "cold_capture":
            ready_match = re.search(
                r"SPATIALACC_NATIVE_CHECKPOINT_READY\s+sequence=(\d+)\s+cycle=(\d+)",
                simulation_log_path.read_text(encoding="utf-8", errors="ignore")
                if simulation_log_path.is_file()
                else "",
            )
            save_marker_seen = bool(
                simulation_log_path.is_file()
                and "SPATIALACC_NATIVE_CHECKPOINT_SAVE_PASS"
                in simulation_log_path.read_text(encoding="utf-8", errors="ignore")
            )
            native_availability = run_transfer_command(
                [
                    "ssh",
                    "-p",
                    str(port),
                    "-o",
                    "StrictHostKeyChecking=no",
                    host,
                    "cd "
                    + shlex.quote(remote_dir)
                    + " && test -f "
                    + shlex.quote(NATIVE_CHECKPOINT_SNAPSHOT.as_posix())
                    + " && test -f "
                    + shlex.quote(f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli")
                    + " && test -d "
                    + shlex.quote(NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix()),
                ],
                timeout_sec,
            )
            capture_report = {
                "schema_version": CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION,
                "status": "pass" if ready_match and save_marker_seen and native_availability.returncode == 0 else "fail",
                "mode": "cold_capture",
                "captured_sequence": int(ready_match.group(1)) if ready_match else None,
                "captured_cycle": int(ready_match.group(2)) if ready_match else None,
                "state_artifacts": [
                    {
                        "kind": "native_vcs_snapshot",
                        "path": NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
                        "remote_path": NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
                        "remote_ucli_path": f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli",
                        "remote_files_path": NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix(),
                    }
                ],
                "native_ready_marker_seen": bool(ready_match),
                "native_save_marker_seen": save_marker_seen,
                "native_snapshot_available": native_availability.returncode == 0,
            }
            checkpoint_errors = checkpoint_capture_report_errors(checkpoint_plan, capture_report)
            incoming_dir = checkpoint_root(run_dir) / ".incoming_fast_replay"
            if incoming_dir.exists():
                shutil.rmtree(incoming_dir)
            incoming_dir.mkdir(parents=True, exist_ok=True)
            write_json(incoming_dir / "capture_report.json", capture_report)
            local_state_rows: list[dict[str, Any]] = [
                {
                    "path": "native_state",
                    "kind": "native_vcs_snapshot",
                    "remote_path": NATIVE_CHECKPOINT_SNAPSHOT.as_posix(),
                    "remote_ucli_path": f"{NATIVE_CHECKPOINT_SNAPSHOT.as_posix()}.ucli",
                    "remote_files_path": NATIVE_CHECKPOINT_SNAPSHOT_FILES.as_posix(),
                    "byte_count": 0,
                }
            ]
            if not checkpoint_errors:
                checkpoint_manifest = framework_checkpoint_manifest(
                    checkpoint_plan,
                    capture_report,
                    local_state_rows,
                    remote_workdir=remote_dir,
                )
                checkpoint_id = str(checkpoint_manifest["checkpoint_id"])
                final_dir = checkpoint_root(run_dir) / checkpoint_id
                write_json(incoming_dir / "manifest.json", checkpoint_manifest)
                if final_dir.exists():
                    shutil.rmtree(final_dir)
                incoming_dir.rename(final_dir)
                checkpoint_artifact_result = {
                    "status": "pass",
                    "mode": "cold_capture",
                    "checkpoint_id": checkpoint_id,
                    "manifest": str(final_dir / "manifest.json"),
                    "total_state_bytes": checkpoint_manifest.get("total_state_bytes", 0),
                    "errors": [],
                    "remote_acknowledgment_status": "pending",
                }
            else:
                checkpoint_artifact_result = {
                    "status": "fail",
                    "mode": "cold_capture",
                    "capture_report": str(incoming_dir / "capture_report.json"),
                    "errors": list(dict.fromkeys(checkpoint_errors)),
                }
        else:
            # Native restore runs use execute_saved_fast_replay(), before the
            # current-source VCS path.  Keeping this branch explicit prevents
            # retired VPI report parsing from becoming an accidental fallback.
            checkpoint_artifact_result = {
                "status": "fail",
                "mode": checkpoint_plan.get("mode"),
                "errors": [
                    "native checkpoint restore must use the saved simulator path"
                ],
            }

    sim_log = simulation_log_path.read_text(encoding="utf-8", errors="ignore") if simulation_log_path.is_file() else ""
    compile_log = compile_log_path.read_text(encoding="utf-8", errors="ignore") if compile_log_path.is_file() else ""
    capture_only_complete = (
        checkpoint_plan.get("mode") == "cold_capture"
        and checkpoint_artifact_result.get("status") == "pass"
        and simulate_result.get("status") == "pass"
    )
    if capture_only_complete:
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_layer": "layer3_real_board_axi_ddr",
            "status": "checkpoint_capture_complete",
            "hardware_validation_status": "checkpoint_capture_complete",
            "stage_pass_eligible": False,
            "phase": "remote_vcs",
            "returncode": simulate_result.get("returncode"),
            "manifest": resolved["manifest_path"],
            "simulation_execution_identity": simulation_execution_identity(manifest),
            "compile_log": str(compile_log_path),
            "sim_log": str(simulation_log_path),
            "checkpoint_execution": {
                key: checkpoint_plan.get(key)
                for key in (
                    "status",
                    "mode",
                    "enabled",
                    "candidate_screening",
                    "acceptance_eligible",
                    "request_path",
                    "request_sha256",
                    "policy",
                )
            },
            "checkpoint_artifacts": checkpoint_artifact_result,
            "fast_replay_used": False,
            "compile_reused": False,
            "weight_load_skipped": False,
            "second_vcs_compile_was_not_launched": False,
            "simulator_path": simulator_path.as_posix(),
            "compile": compile_result,
            "run": simulate_result,
            "remote_workdir": remote_dir,
            "input_fingerprint_sha256": fingerprint,
            "summary": (
                "Layer-3 checkpoint capture completed; native restore "
                "confirmation is required before replay reuse"
            ),
        }
    regex_matched = re.search(str(manifest["pass_regex"]), sim_log) is not None
    outputs_copied = all(row.get("copied") is True for row in copied_outputs.values())
    structured_monitors_passed = bool(monitor_results) and all(
        row.get("status") == "pass" for row in monitor_results.values()
    )
    version_match = re.search(r"(?m)^\s*Version\s+([^\n]+?)\s*$", compile_log)
    tool_version = version_match.group(1).strip() if version_match else str(tool.get("version") or "")
    basic_execution_passed = (
        compile_result.get("status") == "pass"
        and simulate_result.get("status") == "pass"
        and compile_log_download.returncode == 0
        and simulation_log_download.returncode == 0
        and progress_event_log_valid
        and bool(tool_version)
        and regex_matched
        and outputs_copied
        and structured_monitors_passed
        and hierarchy_report_valid
        and pipeline_overlap_passed
        and runtime_loader_report_passed
        and boundary_observation_passed
        and checkpoint_artifact_result.get("status") in {"pass", "not_run"}
    )
    evidence = resolved["evidence"]
    returncode = (
        simulate_result.get("returncode")
        if simulate_result.get("status") != "not_run"
        else compile_result.get("returncode")
    )
    def artifact(path: Path, relative: Path) -> dict[str, Any]:
        return {
            "path": str(path),
            "relative_path": relative.as_posix(),
            "sha256": sha256_file(path) if path.is_file() else None,
        }

    def runtime_evidence_id(kind: str, path: Path) -> str:
        digest = sha256_file(path) if path.is_file() else "missing"
        return f"runtime.{kind}.{digest[:16]}"

    compile_evidence_id = runtime_evidence_id("compile_log", compile_log_path)
    simulation_evidence_id = runtime_evidence_id("simulation_log", simulation_log_path)
    pipeline_evidence_id = runtime_evidence_id("pipeline_overlap", pipeline_path)
    progress_evidence_id = runtime_evidence_id(
        "progress_event_log", progress_event_path
    )
    boundary_observation_evidence_id = runtime_evidence_id(
        "pipeline_boundary_observation_summary",
        boundary_observation_summary_path,
    )
    runtime_loader_evidence_id = (
        runtime_evidence_id("runtime_loader", runtime_loader_path)
        if isinstance(runtime_loader_spec, dict)
        else ""
    )
    hierarchy_evidence_refs = [
        str(value)
        for value in hierarchy_payload.get("evidence_refs", [])
        if str(value)
    ]
    dynamic_evidence_records = [
        {
            "evidence_id": compile_evidence_id,
            "evidence_kind": "compile_log",
            "schema_version": "spatialaccagent.tool_log.v1",
            **artifact(compile_log_path, compile_log_relative),
        },
        {
            "evidence_id": simulation_evidence_id,
            "evidence_kind": "simulation_log",
            "schema_version": "spatialaccagent.tool_log.v1",
            **artifact(simulation_log_path, simulation_log_relative),
        },
        {
            "evidence_id": progress_evidence_id,
            "evidence_kind": "progress_event_log",
            "schema_version": progress_spec["schema_version"],
            **artifact(progress_event_path, progress_spec["path"]),
        },
        {
            "evidence_id": pipeline_evidence_id,
            "evidence_kind": "pipeline_overlap_report",
            "schema_version": pipeline_spec["schema_version"],
            **artifact(pipeline_path, pipeline_spec["path"]),
        },
        {
            "evidence_id": boundary_observation_evidence_id,
            "evidence_kind": "pipeline_boundary_observation_summary",
            "schema_version": boundary_observation_summary.get(
                "schema_version",
                "spatialaccagent.pipeline_boundary_observation.v1",
            ),
            **artifact(
                boundary_observation_summary_path,
                Path("pipeline_boundary_observation_summary.json"),
            ),
        },
    ]
    for row in supplemental_observation_artifacts:
        path = Path(str(row.get("path") or ""))
        relative = safe_relative_path(row.get("relative_path"))
        if row.get("copied") is not True or relative is None or not path.is_file():
            continue
        evidence_id = runtime_evidence_id(
            f"supplemental_observation.{safe_id(relative.stem)}",
            path,
        )
        row["evidence_id"] = evidence_id
        dynamic_evidence_records.append(
            {
                "evidence_id": evidence_id,
                "evidence_kind": "supplemental_debug_observation",
                "schema_versions": row.get("summary", {}).get(
                    "schema_versions", []
                ),
                **artifact(path, relative),
            }
        )
    if isinstance(runtime_loader_spec, dict):
        dynamic_evidence_records.append(
            {
                "evidence_id": runtime_loader_evidence_id,
                "evidence_kind": "runtime_loader_report",
                "schema_version": runtime_loader_spec["schema_version"],
                **artifact(runtime_loader_path, runtime_loader_spec["path"]),
            }
        )
    dynamic_evidence_records.extend(
        {
            "evidence_id": evidence_id,
            "evidence_kind": "elaborated_hierarchy",
            "schema_version": hierarchy_spec["schema_version"],
            **artifact(hierarchy_path, hierarchy_spec["path"]),
        }
        for evidence_id in hierarchy_evidence_refs
    )

    command_sha256 = hashlib.sha256(
        json.dumps(
            {"compile": compile_command, "simulate": simulate_command},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    protocol_interfaces = []
    for spec in resolved["structured_monitor_specs"]:
        payload = monitor_payloads.get(spec["interface"], {})
        path = board_dir / spec["remote_path"]
        protocol_evidence_id = runtime_evidence_id(
            f"protocol_monitor.{safe_id(spec['interface'])}", path
        )
        dynamic_evidence_records.append(
            {
                "evidence_id": protocol_evidence_id,
                "evidence_kind": "protocol_monitor_report",
                "schema_version": spec["schema_version"],
                **artifact(path, spec["remote_path"]),
            }
        )
        protocol_interfaces.append(
            {
                "interface": spec["interface"],
                "evidence_refs": [protocol_evidence_id],
                "status": payload.get("status"),
                "violations": payload.get("violations"),
                "transaction_counts": payload.get("transaction_counts"),
                "structured_report": artifact(path, spec["remote_path"]),
            }
        )
    executed_manifest = json.loads(json.dumps(manifest))
    executed_manifest["status"] = "pass" if basic_execution_passed else "fail"
    executed_manifest["execution_evidence"] = {
        "status": "pass" if basic_execution_passed else "fail",
        "tool": str(tool.get("name") or Path(executable).name),
        "tool_version": tool_version,
        "job_id": remote_dir,
        "command_sha256": command_sha256,
        "source_identity_sha256": manifest.get("source_identity_sha256"),
        "source_closure_sha256": manifest.get("source_closure_sha256"),
        "compile_source_set_sha256": manifest.get("compile_source_set_sha256"),
        "vcs_compile_plan_sha256": compile_plan["sha256"],
        "compute_slot_abi_sha256": manifest.get("compute_slot_abi_sha256"),
        "timing_contract_sha256": manifest.get("timing_contract_sha256"),
        "axi_interfaces_sha256": manifest.get("axi_interfaces_sha256"),
        "compile": {
            "exit_code": compile_result.get("returncode"),
            "log": {
                **artifact(compile_log_path, compile_log_relative),
                "evidence_refs": [compile_evidence_id],
            },
        },
        "simulation": {
            "exit_code": simulate_result.get("returncode"),
            "completed": simulate_result.get("status") == "pass",
            "pass_marker_seen": regex_matched,
            "termination_provenance": simulate_result.get(
                "termination_provenance", {}
            ),
            "log": {
                **artifact(simulation_log_path, simulation_log_relative),
                "evidence_refs": [simulation_evidence_id],
            },
        },
        "elaborated_hierarchy_report": {
            **artifact(hierarchy_path, hierarchy_spec["path"]),
            "schema_version": hierarchy_spec["schema_version"],
            "evidence_refs": hierarchy_evidence_refs,
        },
        "pipeline_boundary_observation": {
            "status": "pass" if boundary_observation_passed else "fail",
            "summary": artifact(
                boundary_observation_summary_path,
                Path("pipeline_boundary_observation_summary.json"),
            ),
            "evidence_refs": [boundary_observation_evidence_id],
        },
    }
    executed_manifest["dynamic_evidence_records"] = dynamic_evidence_records
    executed_manifest["elaborated_hierarchy"] = hierarchy_payload
    executed_manifest["protocol_monitor_results"] = {
        "status": "pass" if structured_monitors_passed else "fail",
        "all_axi_interfaces_covered": structured_monitors_passed,
        "protocol_monitor_contract_sha256": canonical_contract_sha256(
            manifest.get("protocol_monitor_contract", {})
        ),
        "interfaces": protocol_interfaces,
    }
    executed_manifest["pipeline_overlap_results"] = {
        "status": pipeline_payload.get("status"),
        "evidence_refs": [pipeline_evidence_id],
        "board_integration_contract_sha256": canonical_contract_sha256(
            manifest.get("board_integration_contract", {})
        ),
        "pipeline_semantics": pipeline_payload.get("pipeline_semantics"),
        "required_dependency_overlap_complete": pipeline_payload.get(
            "required_dependency_overlap_complete"
        ),
        "all_planned_stages_participate_in_required_overlap": pipeline_payload.get(
            "all_planned_stages_participate_in_required_overlap"
        ),
        "token_order_preserved": pipeline_payload.get("token_order_preserved"),
        "serial_leaf_execution_observed": pipeline_payload.get("serial_leaf_execution_observed"),
        "observed_different_token_overlap_count": pipeline_payload.get(
            "observed_different_token_overlap_count"
        ),
        "stage_turnover_gaps_are_diagnostic": pipeline_payload.get(
            "stage_turnover_gaps_are_diagnostic"
        ),
        "all_stages_same_cycle_concurrency_required": pipeline_payload.get(
            "all_stages_same_cycle_concurrency_required"
        ),
        "diagnostic_maximum_concurrent_stage_count": pipeline_payload.get(
            "diagnostic_maximum_concurrent_stage_count"
        ),
        "all_spatial_stages_concurrent_observed": pipeline_payload.get("all_spatial_stages_concurrent_observed"),
        "whole_sequence_barrier_observed": pipeline_payload.get("whole_sequence_barrier_observed"),
        "expected_stage_count": pipeline_payload.get("expected_stage_count"),
        "observed_stage_count": pipeline_payload.get("observed_stage_count"),
        "structured_trace_report": artifact(pipeline_path, pipeline_spec["path"]),
    }
    executed_manifest["debug_observability_results"] = {
        **progress_summary,
        "status": "pass" if progress_event_log_valid else "fail",
        "evidence_refs": [progress_evidence_id],
        "structured_event_log": artifact(
            progress_event_path, progress_spec["path"]
        ),
        "pipeline_boundary_observation": boundary_observation_summary,
        "pipeline_boundary_observation_artifact": artifact(
            boundary_observation_summary_path,
            Path("pipeline_boundary_observation_summary.json"),
        ),
        "supplemental_observation_artifacts": supplemental_observation_artifacts,
        "vcs_native_loop_report": vcs_loop_report,
    }
    executed_manifest["simulation_checkpoint_results"] = {
        **checkpoint_artifact_result,
        "candidate_screening": checkpoint_plan.get("candidate_screening"),
        "acceptance_eligible": checkpoint_plan.get("acceptance_eligible"),
        "request_sha256": checkpoint_plan.get("request_sha256"),
    }
    if isinstance(runtime_loader_spec, dict):
        executed_manifest["runtime_loader_results"] = {
            **runtime_loader_payload,
            "evidence_refs": [runtime_loader_evidence_id],
            "structured_report": artifact(
                runtime_loader_path, runtime_loader_spec["path"]
            ),
        }
    if isinstance(performance_counter_spec, dict):
        executed_manifest["performance_counter_results"] = {
            **performance_counter_payload,
            "structured_report": artifact(
                performance_counter_path, performance_counter_spec["path"]
            ),
        }
    executed_manifest_path = board_dir / "board_simulation_executed_manifest.json"
    write_json(executed_manifest_path, executed_manifest)
    exact_board_acceptance = validate_exact_board_acceptance(
        Path(resolved["identity_path"]), executed_manifest_path
    )
    exact_board_acceptance_passed = exact_board_acceptance.get("status") == "pass"
    if (
        basic_execution_passed
        and exact_board_acceptance_passed
        and checkpoint_plan.get("acceptance_eligible") is True
    ):
        write_json(Path(resolved["manifest_path"]), executed_manifest)
    elaborated_binding_verified = any(
        row.get("name") == "elaborated_exact_top_and_accelerator_binding"
        and row.get("status") == "pass"
        for row in exact_board_acceptance.get("checks", [])
        if isinstance(row, dict)
    )
    passed = basic_execution_passed and exact_board_acceptance_passed
    reported_status = (
        "candidate_pass"
        if passed and checkpoint_plan.get("candidate_screening") is True
        else "pass"
        if passed
        else "fail"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "verification_layer": "layer3_real_board_axi_ddr",
        "status": reported_status,
        "hardware_validation_status": (
            "screening_pass"
            if reported_status == "candidate_pass"
            else reported_status
        ),
        "stage_pass_eligible": bool(
            passed and checkpoint_plan.get("acceptance_eligible") is True
        ),
        "phase": "remote_vcs",
        "returncode": returncode,
        "manifest": resolved["manifest_path"],
        "source_identity": resolved["identity_path"],
        "exact_sample_wrapper_unmodified": (
            evidence["exact_sample_wrapper_unmodified"] and exact_board_acceptance_passed
        ),
        "accelerator_scope": evidence["accelerator_scope"],
        "all_target_layers": evidence["all_target_layers"],
        "real_model_weights_consumed": (
            evidence["real_model_weights_consumed"] and exact_board_acceptance_passed
        ),
        "complete_scope_weight_image": evidence["complete_scope_weight_image"],
        "required_transformer_block_tensor_count": evidence["required_transformer_block_tensor_count"],
        "random_input_stimulus": evidence["random_input_stimulus"],
        "source_identity_bound": evidence["source_identity_bound"],
        "selected_simulation_source_count": evidence["selected_simulation_source_count"],
        "verified_compile_source_count": evidence["verified_compile_source_count"],
        "vcs_compile_plan_sha256": compile_plan["sha256"],
        "exact_board_preflight_passed": evidence["exact_board_preflight_passed"],
        "exact_board_preflight": resolved["exact_board_preflight"],
        "elaborated_binding_verified": elaborated_binding_verified,
        "exact_board_acceptance_passed": exact_board_acceptance_passed,
        "exact_board_acceptance": exact_board_acceptance,
        "executed_manifest": str(executed_manifest_path),
        "simulation_execution_identity": simulation_execution_identity(
            executed_manifest
        ),
        "weight_binding_evidence": resolved["weight_binding_evidence"],
        "compile_log": str(compile_log_path),
        "sim_log": str(simulation_log_path),
        "outputs": copied_outputs,
        "pass_regex_matched": regex_matched,
        "required_outputs_copied": outputs_copied,
        "structured_monitors_passed": structured_monitors_passed,
        "structured_monitor_results": monitor_results,
        "pipeline_overlap_passed": pipeline_overlap_passed,
        "progress_event_log_valid": progress_event_log_valid,
        "pipeline_boundary_observation_passed": boundary_observation_passed,
        "pipeline_boundary_observation_summary": boundary_observation_summary,
        "progress_event_summary": progress_summary,
        "supplemental_observation_artifacts": supplemental_observation_artifacts,
        "performance_counter_report": (
            str(performance_counter_path)
            if isinstance(performance_counter_spec, dict)
            and performance_counter_path.is_file()
            else None
        ),
        "vcs_native_loop_report": vcs_loop_report,
        "checkpoint_execution": {
            key: checkpoint_plan.get(key)
            for key in (
                "status",
                "mode",
                "enabled",
                "candidate_screening",
                "acceptance_eligible",
                "request_path",
                "request_sha256",
                "policy",
            )
        },
        "checkpoint_artifacts": checkpoint_artifact_result,
        "fast_replay_used": fast_replay.get("used") is True,
        "compile_reused": fast_replay.get("used") is True,
        "weight_load_skipped": fast_replay.get("used") is True,
        "second_vcs_compile_was_not_launched": fast_replay.get("used") is True,
        "simulator_path": (
            str(fast_replay.get("simulator_path"))
            if fast_replay.get("used") is True
            else simulator_path.as_posix()
        ),
        "remote_resource_policy": {
            "vcs_parallel_compile_jobs": vcs_compile_jobs,
            "vcs_parallel_compile_args_applied": sorted(
                set(vcs_parallel_args_applied)
            ),
            "vcs_native_loop_report_enabled": vcs_loop_report_enabled,
            "simulation_runtime_threads": "tool_default",
            "local_heavy_process_limit": 1,
        },
        "live_progress": live_progress_observer.report(),
        "elaborated_hierarchy_report_valid": hierarchy_report_valid,
        "compile": compile_result,
        "run": simulate_result,
        "termination_provenance": simulate_result.get(
            "termination_provenance", {}
        ),
        "input_fingerprint_sha256": fingerprint,
        "fresh_exact_source_replay_generation_sha256": (
            replay_generation_sha256 or None
        ),
        "remote_workdir": remote_dir,
        "remote_job_reuse": remote_job_reuse,
        "remote_job_recovery_contract": {
            "status": "pass",
            "detached_compile_and_simulation": True,
            "exact_payload_identity_recovery_across_controller_restart": True,
            "tri_state_candidate_and_payload_probes": True,
            "indeterminate_transport_retries_unbounded_when_timeout_nonpositive": timeout_sec <= 0,
            "fresh_launch_requires_definite_no_match": True,
            "job_contract": str(job_contract_path),
            "job_contract_sha256": sha256_file(job_contract_path),
            "policy": "indeterminate remote state is preserved; running/done exact jobs are reattached and never relaunched",
        },
        "stderr_tail": str(
            simulate_result.get("stderr_tail") or compile_result.get("stderr_tail") or ""
        )[-4000:],
    }


def pending_same_source_checkpoint_calibration(
    run_dir: Path,
) -> dict[str, Any] | None:
    """Retired: native VCS restore does not use a calibration phase."""

    return None

    """Return a hash-current cold capture that still needs same-source replay."""

    report_path = (
        run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    )
    report = read_json(report_path)
    checkpoint = report.get("checkpoint_artifacts", {})
    if (
        not isinstance(checkpoint, dict)
        or checkpoint.get("mode") != "cold_capture"
        or checkpoint.get("status") != "pass"
        or checkpoint.get("equivalence_status") == "pass"
    ):
        return None
    manifest_path = Path(str(checkpoint.get("manifest") or ""))
    root = checkpoint_root(run_dir).resolve()
    if not manifest_path.is_absolute():
        manifest_path = (run_dir / manifest_path).resolve()
    else:
        manifest_path = manifest_path.resolve()
    if (
        not manifest_path.is_file()
        or not manifest_path.is_relative_to(root)
        or manifest_path.parent.name != str(checkpoint.get("checkpoint_id") or "")
    ):
        return None
    checkpoint_manifest = read_json(manifest_path)
    if checkpoint_manifest_errors(
        checkpoint_manifest,
        artifact_root=manifest_path.parent,
    ):
        return None
    certificate = checkpoint_manifest.get("equivalence_certificate", {})
    if isinstance(certificate, dict) and certificate.get("status") == "pass":
        return None
    prior_execution = checkpoint_manifest.get("same_source_calibration", {})
    if (
        isinstance(prior_execution, dict)
        and prior_execution.get("status") == "fail"
        and prior_execution.get("failure_class")
        not in {"remote_recovery_indeterminate", "remote_tool_transport_failure"}
    ):
        return None
    capture_report = checkpoint_manifest.get("capture_report", {})
    state_artifacts = checkpoint_manifest.get("state_artifacts", [])
    eligibility = same_source_checkpoint_calibration_eligibility(
        capture_report if isinstance(capture_report, dict) else {},
        state_artifacts if isinstance(state_artifacts, list) else [],
        artifact_root=manifest_path.parent,
    )
    if eligibility.get("status") != "ready":
        return None
    board_manifest_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "board_simulation_manifest.json"
    )
    board_manifest = read_json(board_manifest_path)
    current_identity = simulation_execution_identity(board_manifest)
    prior_identity = checkpoint_manifest.get("execution_identity", {})
    if (
        not isinstance(prior_identity, dict)
        or current_identity.get("compiled_model_sha256")
        != prior_identity.get("compiled_model_sha256")
        or current_identity.get("workload_sha256")
        != prior_identity.get("workload_sha256")
    ):
        return None
    job_contract_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "vcs_stage"
        / REMOTE_SEMANTIC_JOB_CONTRACT
    )
    job_contract = read_json(job_contract_path)
    if (
        not job_contract
        or job_contract.get("input_fingerprint_sha256")
        != report.get("input_fingerprint_sha256")
        or job_contract.get("remote_workdir") != report.get("remote_workdir")
        or checkpoint_manifest.get("remote_workdir") != report.get("remote_workdir")
        or checkpoint_manifest.get("remote_acknowledgment_status") != "pass"
    ):
        return None
    return {
        "schema_version": "spatialaccagent.pending_same_source_checkpoint_calibration.v1",
        "status": "ready",
        "summary": (
            "the current complete runtime-quiescent cold capture requires a serial "
            "same-compiled-model restore before hardware-Agent continuation"
        ),
        "runner_report_path": str(report_path),
        "runner_report_sha256": sha256_file(report_path),
        "runner_report": report,
        "checkpoint_manifest_path": str(manifest_path),
        "checkpoint_manifest_sha256": sha256_file(manifest_path),
        "checkpoint_manifest": checkpoint_manifest,
        "remote_job_contract_path": str(job_contract_path),
        "remote_job_contract_sha256": sha256_file(job_contract_path),
        "remote_job_contract": job_contract,
        "runtime_calibration_eligibility": eligibility,
        "policy": {
            "no_second_compile": True,
            "no_cold_prefix_replay": True,
            "one_serial_restore_process": True,
            "hardware_agent_deferred_until_calibration_terminal": True,
        },
    }


def same_source_checkpoint_calibration_failure_projection(
    report: dict[str, Any],
    checkpoint_manifest: dict[str, Any],
    *,
    runner_report_path: Path,
    checkpoint_manifest_path: Path,
    restored_simulation_log_path: Path | None = None,
    restored_progress_event_log_path: Path | None = None,
) -> dict[str, Any]:
    checkpoint = report.get("checkpoint_artifacts", {})
    calibration = report.get("checkpoint_same_source_calibration", {})
    if not isinstance(calibration, dict) or not calibration:
        calibration = checkpoint_manifest.get("same_source_calibration", {})
    if not isinstance(calibration, dict) or not calibration:
        execution = (
            checkpoint.get("equivalence_execution", {})
            if isinstance(checkpoint, dict)
            else {}
        )
        attempt = checkpoint_manifest.get("equivalence_attempt", {})
        cut = checkpoint_manifest.get("semantic_cut", {})
        cut = cut if isinstance(cut, dict) else {}
        if (
            isinstance(execution, dict)
            and execution.get("status") == "pass"
            and execution.get("same_compiled_simulator_reused") is True
            and execution.get("second_vcs_compile_was_not_launched") is True
            and execution.get("serial_execution") is True
            and isinstance(attempt, dict)
            and attempt.get("status") == "fail"
            and attempt.get("producer") == "framework"
        ):
            calibration = {
                "schema_version": (
                    "spatialaccagent.same_source_checkpoint_calibration.v1"
                ),
                "status": "fail",
                "source": "inline_cold_capture_serial_same_source_equivalence",
                "failure_class": (
                    "simulation_checkpoint_restore_equivalence_failed"
                ),
                "errors": [
                    str(value) for value in attempt.get("errors", []) if str(value)
                ],
                "equivalence_execution": json.loads(json.dumps(execution)),
                "equivalence_report": json.loads(json.dumps(attempt)),
                "same_compiled_simulator_reused": True,
                "second_vcs_compile_was_not_launched": True,
                "serial_execution": True,
            }
    equivalence_report = (
        calibration.get("equivalence_report", {})
        if isinstance(calibration, dict)
        else {}
    )
    if not isinstance(equivalence_report, dict) or not equivalence_report:
        attempt = checkpoint_manifest.get("equivalence_attempt", {})
        equivalence_report = attempt if isinstance(attempt, dict) else {}
    restore_runtime_failure_evidence = equivalence_report.get(
        "restore_runtime_failure_evidence", {}
    )
    restore_runtime_failure_evidence = (
        restore_runtime_failure_evidence
        if isinstance(restore_runtime_failure_evidence, dict)
        else {}
    )
    if (
        not isinstance(checkpoint, dict)
        or checkpoint.get("status") != "fail"
        or checkpoint.get("failure_class")
        != "simulation_checkpoint_restore_equivalence_failed"
        or not isinstance(calibration, dict)
        or calibration.get("status") != "fail"
    ):
        return {}
    capture = checkpoint_manifest.get("capture_report", {})
    cut = checkpoint_manifest.get("semantic_cut", {})
    if (
        not isinstance(capture, dict)
        or capture.get("status") != "pass"
        or capture.get("checkpoint_trigger_observed") is not True
        or not isinstance(cut, dict)
    ):
        return {}
    remote_workdir = str(report.get("remote_workdir") or "")
    execution = checkpoint.get("equivalence_execution", {})
    simulation = (
        execution.get("simulation", {})
        if isinstance(execution, dict)
        else {}
    )
    state_schema_row = next(
        (
            row
            for row in checkpoint_manifest.get("state_artifacts", [])
            if isinstance(row, dict) and row.get("kind") == "dut_vpi_schema"
        ),
        {},
    )
    schema_relative = safe_relative_path(state_schema_row.get("path"))
    checkpoint_dir = checkpoint_manifest_path.parent.resolve()
    schema_path = (
        (checkpoint_dir / schema_relative).resolve()
        if schema_relative is not None
        else None
    )
    restored_log = (
        restored_simulation_log_path.resolve()
        if restored_simulation_log_path is not None
        else None
    )
    schema_bound = bool(
        schema_relative is not None
        and isinstance(schema_path, Path)
        and schema_path.is_relative_to(checkpoint_dir)
        and schema_path.is_file()
    )
    adaptive_stall_evidence = (
        simulation.get("adaptive_semantic_stall_evidence", {})
        if isinstance(simulation.get("adaptive_semantic_stall_evidence"), dict)
        else {}
    )
    adaptive_stall_termination = (
        simulation.get("adaptive_semantic_stall_termination", {})
        if isinstance(simulation.get("adaptive_semantic_stall_termination"), dict)
        else {}
    )
    simulation_terminal_bound = bool(
        isinstance(simulation, dict)
        and (
            simulation.get("status") == "pass"
            or (
                simulation.get("status") == "fail"
                and simulation.get("failure_class") == "adaptive_semantic_stall"
                and simulation.get("remote_job_preserved") is False
                and adaptive_stall_evidence.get("status")
                == "proven_semantic_stall"
                and adaptive_stall_termination.get("status") == "pass"
            )
        )
    )
    execution_bound = (
        bool(remote_workdir)
        and checkpoint_manifest.get("remote_workdir") == remote_workdir
        and isinstance(execution, dict)
        and execution.get("status") == "pass"
        and execution.get("same_compiled_simulator_reused") is True
        and execution.get("second_vcs_compile_was_not_launched") is True
        and execution.get("serial_execution") is True
        and simulation_terminal_bound
        and simulation.get("remote_workdir") == remote_workdir
    )
    restore_schema_bound = bool(
        execution_bound
        and schema_bound
        and isinstance(restored_log, Path)
        and restored_log.is_file()
        and isinstance(schema_path, Path)
        and checkpoint_vpi_restore_schema_verified(restored_log, schema_path)
    )
    binding = {
        "checkpoint_id": checkpoint_manifest.get("checkpoint_id"),
        "request_sha256": checkpoint_manifest.get("request_sha256"),
        "semantic_cut_sha256": cut.get("cut_sha256"),
        "remote_workdir": remote_workdir,
        "state_schema_sha256": state_schema_row.get("sha256"),
        "same_compiled_simulator_reused": True,
        "serial_execution": True,
    }
    if restore_schema_bound and isinstance(restored_log, Path):
        recovered = simulation_runtime_failure_evidence(restored_log)
        if recovered.get("status") == "observed":
            archived_log = (
                checkpoint_dir
                / "equivalence_evidence"
                / "restored"
                / "simulation_log.log"
            )
            if restored_log != archived_log:
                archived_log.parent.mkdir(parents=True, exist_ok=True)
                temporary = archived_log.with_suffix(".log.tmp")
                shutil.copy2(restored_log, temporary)
                os.replace(temporary, archived_log)
            recovered["source_path"] = str(restored_log)
            recovered["path"] = str(archived_log)
        recovered["binding"] = binding
        restore_runtime_failure_evidence = recovered

    restored_suffix_materialization = equivalence_report.get(
        "restored_semantic_suffix_materialization", {}
    )
    restored_suffix_materialization = (
        restored_suffix_materialization
        if isinstance(restored_suffix_materialization, dict)
        else {}
    )
    restored_progress = (
        restored_progress_event_log_path.resolve()
        if restored_progress_event_log_path is not None
        else None
    )
    anchor_sequence = capture.get("captured_sequence")
    anchor_cycle = capture.get("captured_cycle")
    if (
        restore_schema_bound
        and isinstance(restored_progress, Path)
        and restored_progress.is_file()
        and isinstance(anchor_sequence, int)
        and not isinstance(anchor_sequence, bool)
        and isinstance(anchor_cycle, int)
        and not isinstance(anchor_cycle, bool)
    ):
        reanalysis_path = (
            runner_report_path.parent
            / "checkpoint_evidence_reanalysis"
            / str(checkpoint_manifest.get("checkpoint_id") or "unknown")
            / "restored_progress_suffix.jsonl"
        )
        restored_suffix_materialization = (
            materialize_checkpoint_semantic_suffix(
                restored_progress,
                reanalysis_path,
                anchor_sequence=anchor_sequence,
                anchor_cycle=anchor_cycle,
            )
        )
        restored_suffix_materialization["binding"] = binding
        equivalence_report = json.loads(json.dumps(equivalence_report))
        equivalence_report[
            "restored_semantic_suffix_materialization"
        ] = restored_suffix_materialization
        if restored_suffix_materialization.get("status") != "pass":
            materialization_errors = [
                f"restored semantic suffix materialization: {value}"
                for value in restored_suffix_materialization.get("errors", [])
                if str(value)
            ]
            equivalence_report["errors"] = list(
                dict.fromkeys(
                    materialization_errors
                    + [
                        str(value)
                        for value in equivalence_report.get("errors", [])
                        if str(value)
                    ]
                )
            )
        calibration = json.loads(json.dumps(calibration))
        calibration["equivalence_report"] = equivalence_report
    checkpoint_artifacts_projection = json.loads(json.dumps(checkpoint))
    checkpoint_artifacts_projection.pop("runtime_execution_failure", None)
    trigger = cut.get("trigger", {}) if isinstance(cut.get("trigger"), dict) else {}
    captured_execution_identity = checkpoint_manifest.get(
        "execution_identity", {}
    )
    captured_execution_identity = (
        captured_execution_identity
        if isinstance(captured_execution_identity, dict)
        else {}
    )
    equivalence_identity = {
        "schema_version": (
            "spatialaccagent.simulation_checkpoint_failure_identity.v1"
        ),
        "compiled_model_sha256": captured_execution_identity.get(
            "compiled_model_sha256"
        ),
        "workload_sha256": captured_execution_identity.get(
            "workload_sha256"
        ),
        "semantic_cut_sha256": cut.get("cut_sha256"),
        "errors": [
            str(value)
            for value in equivalence_report.get("errors", [])
            if str(value)
        ],
        "live_state_witness_diff": equivalence_report.get(
            "live_state_witness_diff", {}
        ),
        "semantic_record_diff": equivalence_report.get(
            "semantic_record_diff", {}
        ),
        "restore_runtime_failure": {
            "status": restore_runtime_failure_evidence.get("status"),
            "matched_lines": restore_runtime_failure_evidence.get(
                "matched_lines", []
            ),
        },
        "restored_semantic_suffix_materialization": {
            "status": restored_suffix_materialization.get("status"),
            "errors": restored_suffix_materialization.get("errors", []),
            "invalid_records": restored_suffix_materialization.get(
                "invalid_records", []
            ),
        },
    }
    return {
        "schema_version": (
            "spatialaccagent.simulation_checkpoint_runtime_capability_failure.v1"
        ),
        "status": "ready",
        "source": "factual_same_source_restore_equivalence_calibration",
        "failure_class": "simulation_checkpoint_capability_missing_or_invalid",
        "failure_identity_sha256": canonical_contract_sha256(
            equivalence_identity
        ),
        "executed_failure_class": (
            "simulation_checkpoint_restore_equivalence_failed"
        ),
        "summary": (
            "the current cold capture restored with the same compiled simulator, "
            "but the executed suffix failed framework equivalence"
        ),
        "mode": "cold_capture",
        "request_sha256": checkpoint_manifest.get("request_sha256"),
        "semantic_cut_sha256": cut.get("cut_sha256"),
        "runner_phase": report.get("phase"),
        "remote_tool_was_started": True,
        "input_fingerprint_sha256": report.get("input_fingerprint_sha256"),
        "remote_workdir": report.get("remote_workdir"),
        "runner_report": {
            "path": str(runner_report_path),
            "pre_projection_sha256": (
                sha256_file(runner_report_path)
                if runner_report_path.is_file()
                else None
            ),
        },
        "checkpoint_manifest": {
            "path": str(checkpoint_manifest_path),
            "sha256": (
                sha256_file(checkpoint_manifest_path)
                if checkpoint_manifest_path.is_file()
                else None
            ),
            "checkpoint_id": checkpoint_manifest.get("checkpoint_id"),
        },
        "trigger_observation": {
            "status": "observed",
            "expected_trigger": trigger,
            "observed_trigger": trigger,
            "captured_sequence": capture.get("captured_sequence"),
            "captured_cycle": capture.get("captured_cycle"),
            "evidence": "factual capture report checkpoint_trigger_observed=true",
        },
        "checkpoint_artifact_errors": [
            str(value) for value in checkpoint.get("errors", []) if str(value)
        ],
        "checkpoint_artifacts": checkpoint_artifacts_projection,
        "same_source_calibration": json.loads(json.dumps(calibration)),
        "restore_runtime_failure_evidence": json.loads(
            json.dumps(restore_runtime_failure_evidence)
        ),
        "restored_semantic_suffix_materialization": json.loads(
            json.dumps(restored_suffix_materialization)
        ),
        "policy": {
            "hardware_failure_evidence_remains_primary": True,
            "checkpoint_failure_disables_reuse_only": True,
            "same_compiled_simulator_restore_was_executed": True,
            "framework_equivalence_failure_is_not_a_hardware_verdict": True,
            "rerun_analyzer_without_rerunning_vcs": True,
        },
    }


def materialize_current_checkpoint_calibration_failure(
    run_dir: Path,
) -> dict[str, Any] | None:
    """Bind a current calibration failure into the runner for analyzer-only routing."""

    reaudit_current_checkpoint_live_state_equivalence(run_dir)

    runner_path = (
        run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    )
    report = read_json(runner_path)
    checkpoint = report.get("checkpoint_artifacts", {})
    if not isinstance(checkpoint, dict):
        return None
    manifest_path = Path(str(checkpoint.get("manifest") or ""))
    if not manifest_path.is_absolute():
        manifest_path = (run_dir / manifest_path).resolve()
    else:
        manifest_path = manifest_path.resolve()
    root = checkpoint_root(run_dir).resolve()
    if not manifest_path.is_file() or not manifest_path.is_relative_to(root):
        return None
    checkpoint_manifest = read_json(manifest_path)
    current_manifest = read_json(
        run_dir
        / "verification"
        / "board_simulation"
        / "board_simulation_manifest.json"
    )
    current_identity = simulation_execution_identity(current_manifest)
    captured_identity = checkpoint_manifest.get("execution_identity", {})
    if (
        not isinstance(captured_identity, dict)
        or current_identity.get("compiled_model_sha256")
        != captured_identity.get("compiled_model_sha256")
        or current_identity.get("workload_sha256")
        != captured_identity.get("workload_sha256")
    ):
        return None
    existing_projection = report.get("checkpoint_runtime_execution_failure")
    nested_projection = checkpoint.get("runtime_execution_failure")
    if (
        isinstance(existing_projection, dict)
        and existing_projection.get("schema_version")
        == "spatialaccagent.simulation_checkpoint_runtime_capability_failure.v1"
        and existing_projection.get("status") == "ready"
        and existing_projection.get("input_fingerprint_sha256")
        == report.get("input_fingerprint_sha256")
        and existing_projection.get("remote_workdir")
        == report.get("remote_workdir")
        and existing_projection.get("checkpoint_manifest", {}).get("checkpoint_id")
        == checkpoint_manifest.get("checkpoint_id")
        and nested_projection == existing_projection
    ):
        return existing_projection
    output_errors: list[str] = []
    output_plan = execution_output_plan(current_manifest, output_errors)
    simulation_log_row = output_plan.get("simulation_log", {})
    progress_event_log_row = output_plan.get("progress_event_log", {})
    restored_simulation_log_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "checkpoint"
        / "equivalence"
        / "restored_outputs"
        / simulation_log_row["path"]
        if not output_errors
        and isinstance(simulation_log_row, dict)
        and isinstance(simulation_log_row.get("path"), Path)
        else None
    )
    restored_progress_event_log_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "checkpoint"
        / "equivalence"
        / "restored_outputs"
        / progress_event_log_row["path"]
        if not output_errors
        and isinstance(progress_event_log_row, dict)
        and isinstance(progress_event_log_row.get("path"), Path)
        else None
    )
    projection = same_source_checkpoint_calibration_failure_projection(
        report,
        checkpoint_manifest,
        runner_report_path=runner_path,
        checkpoint_manifest_path=manifest_path,
        restored_simulation_log_path=restored_simulation_log_path,
        restored_progress_event_log_path=restored_progress_event_log_path,
    )
    if not projection:
        return None
    report["checkpoint_runtime_execution_failure"] = projection
    report["checkpoint_artifacts"]["runtime_execution_failure"] = projection
    write_json(runner_path, report)
    return projection


def reaudit_current_checkpoint_live_state_equivalence(
    run_dir: Path,
) -> dict[str, Any]:
    """Fail closed when a legacy certificate only matched a replayed barrier."""

    runner_path = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    report = read_json(runner_path)
    checkpoint = report.get("checkpoint_artifacts", {})
    if not isinstance(checkpoint, dict) or checkpoint.get("status") != "pass":
        return {"status": "not_required"}
    manifest_path = Path(str(checkpoint.get("manifest") or "")).resolve()
    store_root = checkpoint_root(run_dir).resolve()
    if not manifest_path.is_file() or not manifest_path.is_relative_to(store_root):
        return {
            "status": "fail",
            "errors": ["current checkpoint manifest is unavailable for live-state re-audit"],
        }
    manifest = read_json(manifest_path)
    prior_equivalence = manifest.get("equivalence_certificate", {})
    if (
        isinstance(prior_equivalence, dict)
        and prior_equivalence.get("live_state_witness_match") is not None
    ):
        return {"status": "not_required"}

    board_dir = run_dir / "verification" / "board_simulation"
    board_manifest = read_json(board_dir / "board_simulation_manifest.json")
    output_errors: list[str] = []
    output_plan = execution_output_plan(board_manifest, output_errors)
    progress_row = output_plan.get("progress_event_log", {})
    if output_errors or not isinstance(progress_row, dict):
        return {
            "status": "fail",
            "errors": output_errors
            or ["board progress output plan is unavailable for live-state re-audit"],
        }
    progress_relative = progress_row.get("path")
    if not isinstance(progress_relative, Path):
        return {
            "status": "fail",
            "errors": ["board progress output path is invalid for live-state re-audit"],
        }
    cold_live_progress = board_dir / progress_relative
    restored_live_progress = (
        board_dir
        / "checkpoint"
        / "equivalence"
        / "restored_outputs"
        / progress_relative
    )
    restore_report = read_json(
        board_dir / "checkpoint" / "equivalence" / "restore_report.json"
    )
    certificate_root = manifest_path.parent

    def resolve_certificate_path(value: Any) -> Path:
        path = Path(str(value or ""))
        return path if path.is_absolute() else certificate_root / path

    cold_suffix = resolve_certificate_path(
        prior_equivalence.get("cold_progress_suffix", {}).get("path")
        if isinstance(prior_equivalence, dict)
        else None
    )
    restored_suffix = resolve_certificate_path(
        prior_equivalence.get("restored_progress_suffix", {}).get("path")
        if isinstance(prior_equivalence, dict)
        else None
    )
    cold_required: dict[str, Path] = {}
    restored_required: dict[str, Path] = {}
    comparisons = (
        prior_equivalence.get("required_artifact_comparisons", [])
        if isinstance(prior_equivalence, dict)
        else []
    )
    for row in comparisons if isinstance(comparisons, list) else []:
        if not isinstance(row, dict) or not row.get("kind"):
            continue
        kind = str(row["kind"])
        cold_required[kind] = resolve_certificate_path(row.get("cold_path"))
        restored_required[kind] = resolve_certificate_path(row.get("restored_path"))

    capture_report = manifest.get("capture_report", {})
    semantic_cut = manifest.get("semantic_cut", {})
    cold_terminal = (
        prior_equivalence.get("cold_terminal", {})
        if isinstance(prior_equivalence, dict)
        else {}
    )
    restored_terminal = (
        prior_equivalence.get("restored_terminal", {})
        if isinstance(prior_equivalence, dict)
        else {}
    )
    equivalence = framework_equivalence_certificate(
        request_sha256=str(manifest.get("request_sha256") or ""),
        execution_identity=manifest.get("execution_identity", {}),
        semantic_cut=semantic_cut if isinstance(semantic_cut, dict) else {},
        capture_report=(
            capture_report if isinstance(capture_report, dict) else {}
        ),
        restore_report=restore_report,
        cold_progress_path=cold_suffix,
        restored_progress_path=restored_suffix,
        cold_live_progress_path=cold_live_progress,
        restored_live_progress_path=restored_live_progress,
        cold_required_artifacts=cold_required,
        restored_required_artifacts=restored_required,
        cold_terminal=cold_terminal if isinstance(cold_terminal, dict) else {},
        restored_terminal=(
            restored_terminal if isinstance(restored_terminal, dict) else {}
        ),
    )
    for key in (
        "restore_runtime_failure_evidence",
        "cold_semantic_suffix_materialization",
        "restored_semantic_suffix_materialization",
    ):
        if isinstance(prior_equivalence, dict) and prior_equivalence.get(key) is not None:
            equivalence[key] = json.loads(json.dumps(prior_equivalence[key]))
    _relativize_equivalence_report_paths(equivalence, certificate_root)
    write_json(certificate_root / "equivalence_report.json", equivalence)

    errors = [str(value) for value in equivalence.get("errors", []) if str(value)]
    if equivalence.get("status") == "pass":
        errors.insert(
            0,
            "legacy checkpoint certificate predates the mandatory live-state witness identity",
        )
        equivalence["status"] = "fail"
        equivalence["complete_required_state_coverage"] = False
        equivalence["errors"] = errors
        write_json(certificate_root / "equivalence_report.json", equivalence)
    calibration = {
        "schema_version": "spatialaccagent.same_source_checkpoint_calibration.v1",
        "status": "fail",
        "source": "framework_offline_live_state_reaudit",
        "failure_class": "simulation_checkpoint_restore_equivalence_failed",
        "errors": errors,
        "equivalence_report": equivalence,
        "same_compiled_simulator_reused": True,
        "second_vcs_compile_was_not_launched": True,
        "serial_execution": True,
        "offline_reaudit_did_not_rerun_vcs": True,
    }
    manifest["equivalence_attempt"] = equivalence
    manifest["equivalence_certificate"] = {}
    manifest["same_source_calibration"] = calibration
    manifest["active"] = False
    write_json(manifest_path, manifest)

    invalidation = invalidate_debug_episode_checkpoint(run_dir, errors)
    checkpoint.update(
        {
            "status": "fail",
            "failure_class": "simulation_checkpoint_restore_equivalence_failed",
            "equivalence_status": "fail",
            "errors": errors,
            "manifest_sha256": sha256_file(manifest_path),
            "debug_episode_activation": invalidation,
        }
    )
    report["checkpoint_artifacts"] = checkpoint
    report["checkpoint_same_source_calibration"] = calibration
    report["framework_live_state_reaudit"] = {
        "schema_version": "spatialaccagent.checkpoint_live_state_reaudit.v1",
        "status": "fail",
        "checkpoint_id": manifest.get("checkpoint_id"),
        "offline_reaudit_did_not_rerun_vcs": True,
        "live_state_witness_diff": equivalence.get("live_state_witness_diff", {}),
        "errors": errors,
    }
    write_json(runner_path, report)
    return report["framework_live_state_reaudit"]


def _relativize_equivalence_report_paths(
    report: dict[str, Any],
    root: Path,
) -> None:
    for key in ("cold_progress_suffix", "restored_progress_suffix"):
        row = report.get(key, {})
        if not isinstance(row, dict) or not row.get("path"):
            continue
        path = Path(str(row["path"]))
        if path.is_relative_to(root):
            row["path"] = path.relative_to(root).as_posix()
    for key in (
        "cold_semantic_suffix_materialization",
        "restored_semantic_suffix_materialization",
    ):
        row = report.get(key, {})
        if not isinstance(row, dict):
            continue
        for path_key in ("path", "source_path"):
            path = Path(str(row.get(path_key) or ""))
            if path.is_relative_to(root):
                row[path_key] = path.relative_to(root).as_posix()
    for row in report.get("required_artifact_comparisons", []):
        if not isinstance(row, dict):
            continue
        for key in ("cold_path", "restored_path"):
            path = Path(str(row.get(key) or ""))
            if path.is_relative_to(root):
                row[key] = path.relative_to(root).as_posix()


def _link_or_copy_checkpoint_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def _record_checkpoint_calibration_failure(
    pending: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    report = json.loads(json.dumps(pending["runner_report"]))
    manifest_path = Path(str(pending["checkpoint_manifest_path"]))
    manifest = read_json(manifest_path)
    if execution.get("failure_class") not in {
        "remote_recovery_indeterminate",
        "remote_tool_transport_failure",
    }:
        manifest["same_source_calibration"] = execution
        write_json(manifest_path, manifest)
    checkpoint = report.get("checkpoint_artifacts", {})
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    report["checkpoint_artifacts"] = {
        **checkpoint,
        "status": "fail",
        "failure_class": execution.get("failure_class")
        or "simulation_checkpoint_restore_equivalence_failed",
        "equivalence_execution": execution,
        "errors": [
            str(value) for value in execution.get("errors", []) if str(value)
        ],
    }
    report["checkpoint_same_source_calibration"] = execution
    report["checkpoint_calibration_only"] = True
    return report


def calibrate_existing_same_source_checkpoint(
    run_dir: Path,
    timeout_sec: int,
    pending: dict[str, Any],
) -> dict[str, Any]:
    """Replay an existing cold capsule with its already compiled remote simv."""

    board_manifest, resolved, errors = validate_manifest(run_dir)
    checkpoint_manifest = pending.get("checkpoint_manifest", {})
    job_contract = pending.get("remote_job_contract", {})
    if errors:
        return _record_checkpoint_calibration_failure(
            pending,
            {
                "schema_version": "spatialaccagent.same_source_checkpoint_calibration.v1",
                "status": "fail",
                "failure_class": "current_exact_board_identity_invalid",
                "errors": errors,
                "second_vcs_compile_was_not_launched": True,
            },
        )
    compile_plan = resolved["vcs_compile_plan"]
    if (
        compile_plan.get("sha256") != job_contract.get("vcs_compile_plan_sha256")
        or simulation_execution_identity(board_manifest).get("compiled_model_sha256")
        != checkpoint_manifest.get("execution_identity", {}).get(
            "compiled_model_sha256"
        )
    ):
        return _record_checkpoint_calibration_failure(
            pending,
            {
                "schema_version": "spatialaccagent.same_source_checkpoint_calibration.v1",
                "status": "fail",
                "failure_class": "compiled_model_identity_mismatch",
                "errors": [
                    "current exact-board compile identity differs from the captured simulator"
                ],
                "second_vcs_compile_was_not_launched": True,
            },
        )

    tool = tool_profile(run_dir)
    host = str(tool.get("host") or "")
    port = int(tool.get("port") or 22)
    remote_dir = str(checkpoint_manifest.get("remote_workdir") or "")
    if not host or not remote_dir:
        return _record_checkpoint_calibration_failure(
            pending,
            {
                "schema_version": "spatialaccagent.same_source_checkpoint_calibration.v1",
                "status": "fail",
                "failure_class": "remote_calibration_identity_missing",
                "errors": ["checkpoint host or remote workdir is missing"],
                "second_vcs_compile_was_not_launched": True,
            },
        )

    request = {
        "semantic_cut": checkpoint_manifest.get("semantic_cut", {}),
        "storage_policy": checkpoint_manifest.get("storage_policy", {}),
    }
    plan = {
        "mode": "cold_capture",
        "request": request,
        "request_sha256": checkpoint_manifest.get("request_sha256"),
        "execution_identity": checkpoint_manifest.get("execution_identity", {}),
        "contract": checkpoint_contract(board_manifest),
    }
    output_plan = resolved["execution_output_plan"]
    board_dir = run_dir / "verification" / "board_simulation"
    equivalence_progress_contract = same_source_equivalence_progress_contract(
        cctg_progress_contract(run_dir, board_manifest),
        board_dir / output_plan["progress_event_log"]["path"],
        checkpoint_manifest.get("capture_report", {}),
        pending.get("runner_report", {}).get("run", {}),
    )
    equivalence_oracle = equivalence_progress_contract.get(
        "same_source_equivalence_oracle", {}
    )
    if (
        not isinstance(equivalence_oracle, dict)
        or equivalence_oracle.get("status") != "ready"
    ):
        return _record_checkpoint_calibration_failure(
            pending,
            {
                "schema_version": "spatialaccagent.same_source_checkpoint_calibration.v1",
                "status": "fail",
                "failure_class": "same_source_equivalence_oracle_unavailable",
                "errors": [
                    str(value)
                    for value in equivalence_oracle.get("errors", [])
                    if str(value)
                ],
                "same_source_equivalence_oracle": equivalence_oracle,
                "second_vcs_compile_was_not_launched": True,
            },
        )
    output_paths = checkpoint_equivalence_output_paths(board_manifest, output_plan)
    workload_plusargs: list[str] = []
    runtime_plusargs = board_manifest.get("vcs", {}).get("runtime_plusargs", {})
    for key, artifact_name in runtime_plusargs.items():
        artifact_path = resolved["artifact_paths"].get(str(artifact_name))
        if not isinstance(artifact_path, Path):
            return _record_checkpoint_calibration_failure(
                pending,
                {
                    "schema_version": "spatialaccagent.same_source_checkpoint_calibration.v1",
                    "status": "fail",
                    "failure_class": "workload_runtime_identity_missing",
                    "errors": [f"runtime plusarg {key} has no current artifact"],
                    "second_vcs_compile_was_not_launched": True,
                },
            )
        workload_plusargs.append(
            f"+{key}=artifacts/{artifact_name}{artifact_path.suffix}"
        )
    simulator_path = (
        compile_plan["commands"][-1]["cwd"] / compile_plan["output"]
    )
    output_parents = {
        path.parent.as_posix()
        for path in output_paths
        if path.parent != Path(".")
    }
    output_parents.update({"checkpoint/equivalence", "checkpoint/state"})
    prepare_output_dirs = (
        "mkdir -p "
        + " ".join(shlex.quote(value) for value in sorted(output_parents))
        + "; "
    )
    simulation_log_relative = output_plan["simulation_log"]["path"]
    equivalence_plusargs = [
        *workload_plusargs,
        *checkpoint_equivalence_runtime_plusargs(plan),
    ]
    commands = {
        "prepare": checkpoint_equivalence_archive_command(
            output_paths,
            destination=Path("checkpoint/equivalence/cold_outputs"),
        ),
        "simulate": (
            prepare_output_dirs
            + f"./{shlex.quote(simulator_path.as_posix())} "
            + " ".join(shlex.quote(value) for value in equivalence_plusargs)
            + f" > {shlex.quote(simulation_log_relative.as_posix())} 2>&1"
        ),
        "finalize": checkpoint_equivalence_restore_cold_command(output_paths),
    }
    out_dir = run_dir / "verification" / "vcs"
    checkpoint_id = str(checkpoint_manifest.get("checkpoint_id") or "unknown")
    label_suffix = checkpoint_id[:12]
    prepare_result = run_or_recover_remote_command(
        host=host,
        port=port,
        command=commands["prepare"],
        remote_dir=remote_dir,
        cwd=out_dir,
        timeout_sec=timeout_sec,
        label=f"checkpoint_equivalence_prepare_{label_suffix}",
    )
    equivalence_simulation: dict[str, Any] = {
        "status": "not_run",
        "returncode": None,
        "failure_class": None,
    }
    finalize_result: dict[str, Any] = {"status": "not_run"}
    if prepare_result.get("status") == "pass":
        observer = LiveProgressObserver(
            host=host,
            port=port,
            run_dir=run_dir,
            remote_path=output_plan["progress_event_log"]["path"],
            fingerprint=(
                f"{job_contract.get('input_fingerprint_sha256')}:"
                f"same_source_calibration:{checkpoint_id}"
            ),
            progress_contract=equivalence_progress_contract,
            live_namespace="checkpoint_equivalence_calibration_live",
        )
        equivalence_simulation = run_or_recover_remote_command(
            host=host,
            port=port,
            command=commands["simulate"],
            remote_dir=remote_dir,
            cwd=out_dir,
            timeout_sec=timeout_sec,
            label=f"vcs_checkpoint_equivalence_simulate_oracle_v2_{label_suffix}",
            progress_callback=observer,
        )
        if equivalence_simulation.get("remote_job_preserved") is not True:
            finalize_result = run_or_recover_remote_command(
                host=host,
                port=port,
                command=commands["finalize"],
                remote_dir=remote_dir,
                cwd=out_dir,
                timeout_sec=timeout_sec,
                label=f"checkpoint_equivalence_finalize_{label_suffix}",
            )
    execution = {
        "schema_version": "spatialaccagent.same_source_checkpoint_calibration.v1",
        "status": (
            "executed"
            if prepare_result.get("status") == "pass"
            and finalize_result.get("status") == "pass"
            else "fail"
        ),
        "source_checkpoint_id": checkpoint_id,
        "source_checkpoint_manifest_sha256": pending.get(
            "checkpoint_manifest_sha256"
        ),
        "remote_workdir": remote_dir,
        "remote_input_fingerprint_sha256": job_contract.get(
            "input_fingerprint_sha256"
        ),
        "prepare": prepare_result,
        "simulation": equivalence_simulation,
        "finalize": finalize_result,
        "same_compiled_simulator_reused": True,
        "second_vcs_compile_was_not_launched": True,
        "cold_prefix_was_not_replayed": True,
        "serial_execution": True,
        "runtime_calibration_eligibility": pending.get(
            "runtime_calibration_eligibility", {}
        ),
        "policy": {
            "calibration_does_not_issue_a_hardware_verdict": True,
            "cross_revision_reuse_still_requires_causal_cut_certificate": True,
        },
    }
    if prepare_result.get("status") != "pass" or finalize_result.get("status") != "pass":
        failure = (
            prepare_result
            if prepare_result.get("status") != "pass"
            else finalize_result
        )
        execution["failure_class"] = str(
            failure.get("failure_class")
            or "same_source_checkpoint_calibration_execution_failed"
        )
        execution["errors"] = [
            str(failure.get("summary") or execution["failure_class"])
        ]
        return _record_checkpoint_calibration_failure(pending, execution)

    raw_root = board_dir / "checkpoint_calibration" / checkpoint_id
    if raw_root.exists():
        shutil.rmtree(raw_root)
    raw_root.mkdir(parents=True)

    def download(relative: Path) -> tuple[Path, subprocess.CompletedProcess[str]]:
        local_path = raw_root / relative
        _prepare_fresh_transfer_target(local_path)
        result = run_transfer_command(
            [
                "scp",
                "-q",
                "-P",
                str(port),
                "-o",
                "StrictHostKeyChecking=no",
                f"{host}:{remote_dir}/{relative.as_posix()}",
                str(local_path),
            ],
            timeout_sec,
        )
        if result.returncode != 0:
            local_path.unlink(missing_ok=True)
        return local_path, result

    restore_path, restore_download = download(
        Path("checkpoint/equivalence/restore_report.json")
    )
    restore_report = read_json(restore_path) if restore_download.returncode == 0 else {}
    restored_paths: dict[str, Path] = {}
    for kind, original in (
        ("simulation_log", simulation_log_relative),
        ("progress_event_log", output_plan["progress_event_log"]["path"]),
        ("rtl_output", Path(str(board_manifest["rtl_output_file"]))),
        ("boundary_trace", Path(str(board_manifest["boundary_trace_file"]))),
    ):
        path, transfer = download(
            Path("checkpoint/equivalence/restored_outputs") / original
        )
        restored_paths[kind] = path
        if transfer.returncode != 0:
            path.unlink(missing_ok=True)

    source_manifest_path = Path(str(pending["checkpoint_manifest_path"]))
    source_dir = source_manifest_path.parent
    state_rows = checkpoint_manifest.get("state_artifacts", [])
    schema_path = next(
        (
            source_dir / str(row.get("path"))
            for row in state_rows
            if isinstance(row, dict) and row.get("kind") == "dut_vpi_schema"
        ),
        Path(),
    )
    restored_simulation_log = restored_paths.get("simulation_log", Path())
    restore_runtime_failure_evidence = simulation_runtime_failure_evidence(
        restored_simulation_log
    )
    vpi_schema_recheck = checkpoint_vpi_restore_schema_verified(
        restored_simulation_log,
        schema_path,
    )
    restore_report["runtime_state_schema_match"] = bool(
        restore_report.get("runtime_state_schema_match") is True
        and vpi_schema_recheck
    )
    if vpi_schema_recheck:
        restore_report["runtime_state_schema_sha256"] = checkpoint_manifest.get(
            "state_schema", {}
        ).get("sha256")
    restore_report["framework_vpi_schema_recheck"] = {
        "status": "pass" if vpi_schema_recheck else "fail",
        "simulation_log": str(restored_simulation_log),
        "schema_path": str(schema_path),
    }
    restore_report["runtime_failure_evidence"] = restore_runtime_failure_evidence

    store_work = checkpoint_root(run_dir) / f".calibrating_{checkpoint_id}"
    if store_work.exists():
        shutil.rmtree(store_work)
    store_work.mkdir(parents=True)
    for row in state_rows:
        if not isinstance(row, dict):
            continue
        relative = Path(str(row.get("path") or ""))
        _link_or_copy_checkpoint_file(source_dir / relative, store_work / relative)
    capture_report = checkpoint_manifest.get("capture_report", {})
    write_json(store_work / "capture_report.json", capture_report)
    evidence_root = store_work / "equivalence_evidence"
    anchor_sequence = int(capture_report["captured_sequence"])
    anchor_cycle = int(capture_report["captured_cycle"])
    cold_progress = board_dir / output_plan["progress_event_log"]["path"]
    cold_suffix = evidence_root / "cold" / "progress_event_log.jsonl"
    restored_suffix = evidence_root / "restored" / "progress_event_log.jsonl"
    cold_suffix_result = materialize_checkpoint_semantic_suffix(
        cold_progress,
        cold_suffix,
        anchor_sequence=anchor_sequence,
        anchor_cycle=anchor_cycle,
    )
    restored_suffix_result = materialize_checkpoint_semantic_suffix(
        restored_paths.get("progress_event_log", Path()),
        restored_suffix,
        anchor_sequence=anchor_sequence,
        anchor_cycle=anchor_cycle,
    )

    prior_report = pending["runner_report"]
    prior_outputs = prior_report.get("outputs", {})
    cold_required = {
        "rtl_output": Path(
            str(prior_outputs.get("rtl_output_file", {}).get("path") or "")
        ),
        "boundary_trace": Path(
            str(prior_outputs.get("boundary_trace_file", {}).get("path") or "")
        ),
    }

    def persist_required(source: Path, side: str, kind: str) -> Path:
        suffix = source.suffix or ".bin"
        target = evidence_root / side / f"{kind}{suffix}"
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return target

    cold_persisted = {
        kind: persist_required(path, "cold", kind)
        for kind, path in cold_required.items()
    }
    restored_persisted = {
        kind: persist_required(restored_paths.get(kind, Path()), "restored", kind)
        for kind in ("rtl_output", "boundary_trace")
    }
    equivalence_report = framework_equivalence_certificate(
        request_sha256=str(checkpoint_manifest.get("request_sha256") or ""),
        execution_identity=checkpoint_manifest.get("execution_identity", {}),
        semantic_cut=checkpoint_manifest.get("semantic_cut", {}),
        capture_report=capture_report,
        restore_report=restore_report,
        cold_progress_path=cold_suffix,
        restored_progress_path=restored_suffix,
        cold_live_progress_path=cold_progress,
        restored_live_progress_path=restored_paths.get(
            "progress_event_log", Path()
        ),
        cold_required_artifacts=cold_persisted,
        restored_required_artifacts=restored_persisted,
        cold_terminal={
            "returncode": prior_report.get("run", {}).get("returncode"),
            "failure_class": prior_report.get("run", {}).get("failure_class"),
        },
        restored_terminal={
            "returncode": equivalence_simulation.get("returncode"),
            "failure_class": equivalence_simulation.get("failure_class"),
        },
    )
    equivalence_report["restore_runtime_failure_evidence"] = (
        restore_runtime_failure_evidence
    )
    equivalence_report["cold_semantic_suffix_materialization"] = (
        cold_suffix_result
    )
    equivalence_report["restored_semantic_suffix_materialization"] = (
        restored_suffix_result
    )
    materialization_errors = []
    for side, result in (
        ("cold", cold_suffix_result),
        ("restored", restored_suffix_result),
    ):
        if result.get("status") == "pass":
            continue
        materialization_errors.extend(
            f"{side} semantic suffix materialization: {value}"
            for value in result.get("errors", [])
            if str(value)
        )
    if materialization_errors:
        equivalence_report["errors"] = list(
            dict.fromkeys(
                materialization_errors + equivalence_report.get("errors", [])
            )
        )
    _relativize_equivalence_report_paths(equivalence_report, store_work)
    write_json(store_work / "equivalence_report.json", equivalence_report)
    calibrated_manifest = framework_checkpoint_manifest(
        plan,
        capture_report,
        state_rows,
        equivalence_report=equivalence_report,
        remote_workdir=remote_dir,
    )
    calibrated_manifest["created_at_unix_sec"] = checkpoint_manifest.get(
        "created_at_unix_sec", calibrated_manifest.get("created_at_unix_sec")
    )
    calibrated_manifest["remote_acknowledgment_status"] = "pass"
    if checkpoint_manifest.get("remote_artifact_persistence") is not None:
        calibrated_manifest["remote_artifact_persistence"] = checkpoint_manifest.get(
            "remote_artifact_persistence"
        )
    cold_duration = prior_report.get("run", {}).get("duration_sec")
    restored_duration = equivalence_simulation.get("duration_sec")
    speedup = (
        float(cold_duration) / float(restored_duration)
        if isinstance(cold_duration, (int, float))
        and isinstance(restored_duration, (int, float))
        and restored_duration > 0
        else None
    )
    execution.update(
        {
            "status": "pass" if equivalence_report.get("status") == "pass" else "fail",
            "failure_class": (
                None
                if equivalence_report.get("status") == "pass"
                else "simulation_checkpoint_restore_equivalence_failed"
            ),
            "equivalence_certificate_status": equivalence_report.get("status"),
            "equivalence_errors": equivalence_report.get("errors", []),
            "cold_semantic_suffix_materialization": cold_suffix_result,
            "restored_semantic_suffix_materialization": restored_suffix_result,
            "cold_wall_duration_sec": cold_duration,
            "restored_wall_duration_sec": restored_duration,
            "measured_wall_clock_speedup": speedup,
            "calibration_runner_implementation_sha256": sha256_file(
                Path(__file__).resolve()
            ),
        }
    )
    calibrated_manifest["same_source_calibration"] = execution
    calibrated_manifest["calibration_source_checkpoint_id"] = checkpoint_id
    calibrated_manifest["calibration_source_manifest_sha256"] = pending.get(
        "checkpoint_manifest_sha256"
    )
    write_json(store_work / "manifest.json", calibrated_manifest)
    calibrated_id = str(calibrated_manifest["checkpoint_id"])
    final_dir = checkpoint_root(run_dir) / calibrated_id
    if calibrated_id == checkpoint_id:
        for name in ("equivalence_evidence",):
            source = store_work / name
            if source.exists():
                shutil.copytree(source, final_dir / name, dirs_exist_ok=True)
        shutil.copy2(
            store_work / "equivalence_report.json",
            final_dir / "equivalence_report.json",
        )
        write_json(final_dir / "manifest.json", calibrated_manifest)
        shutil.rmtree(store_work)
    elif final_dir.exists():
        existing = read_json(final_dir / "manifest.json")
        if existing.get("checkpoint_id") != calibrated_id:
            execution["status"] = "fail"
            execution["failure_class"] = "content_addressed_checkpoint_conflict"
            execution["errors"] = [
                "calibrated checkpoint directory has a conflicting identity"
            ]
            shutil.rmtree(store_work)
            return _record_checkpoint_calibration_failure(pending, execution)
        shutil.rmtree(store_work)
    else:
        store_work.rename(final_dir)

    manifest_path = final_dir / "manifest.json"
    episode_activation = (
        activate_checkpoint_for_debug_episode(run_dir, manifest_path)
        if equivalence_report.get("status") == "pass"
        else {
            "status": "not_run",
            "summary": "same-source equivalence did not pass",
        }
    )
    calibrated_manifest = read_json(manifest_path)
    storage_policy = calibrated_manifest.get("storage_policy", {})
    retention = checkpoint_retention_plan(
        checkpoint_manifests(run_dir),
        max_count=int(storage_policy.get("max_checkpoint_count") or 3),
        max_bytes=int(storage_policy.get("max_checkpoint_bytes") or 8 * 1024**3),
    )
    retention_execution = apply_checkpoint_retention_plan(run_dir, retention)
    checkpoint_result = {
        "status": "pass" if equivalence_report.get("status") == "pass" else "fail",
        "mode": "cold_capture",
        "checkpoint_id": calibrated_id,
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "total_state_bytes": calibrated_manifest.get("total_state_bytes"),
        "portable_state_capsule_status": calibrated_manifest.get(
            "portable_state_capsule", {}
        ).get("status"),
        "causal_cut_certificate_status": calibrated_manifest.get(
            "causal_cut_certificate", {}
        ).get("status"),
        "equivalence_status": equivalence_report.get("status"),
        "equivalence_execution": execution,
        "runtime_calibration_eligibility": pending.get(
            "runtime_calibration_eligibility", {}
        ),
        "failure_class": execution.get("failure_class"),
        "errors": [
            str(value) for value in equivalence_report.get("errors", []) if str(value)
        ],
        "remote_acknowledgment_status": "pass",
        "debug_episode_activation": episode_activation,
        "retention_plan": retention,
        "retention_execution": retention_execution,
    }
    report = json.loads(json.dumps(prior_report))
    report["checkpoint_artifacts"] = checkpoint_result
    report["checkpoint_same_source_calibration"] = execution
    report["checkpoint_calibration_only"] = True
    report["checkpoint_calibration_did_not_compile_or_replay_cold_prefix"] = True
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=int(os.environ.get("SPATIALACC_TOOL_TIMEOUT_SEC", "0")),
        help="outer VCS wall-clock timeout in seconds; <=0 waits without a wall-clock limit",
    )
    return parser.parse_args(argv)


def _normalized_board_vcs_report(report: dict[str, Any]) -> dict[str, Any]:
    """Give every runner exit the same small status surface."""

    normalized = dict(report)
    normalized.setdefault("schema_version", SCHEMA_VERSION)
    normalized.setdefault("verification_layer", "layer3_real_board_axi_ddr")
    normalized.setdefault("stage_pass_eligible", False)
    normalized.setdefault("exact_board_preflight_passed", False)
    normalized.setdefault("exact_board_acceptance_passed", False)
    normalized.setdefault("pass_regex_matched", False)
    normalized.setdefault("required_outputs_copied", False)
    normalized.setdefault("structured_monitors_passed", False)
    normalized.setdefault("pipeline_overlap_passed", False)
    normalized.setdefault("progress_event_log_valid", False)
    return normalized


def execute(run_dir: Path, timeout_sec: int) -> dict[str, Any]:
    return _normalized_board_vcs_report(
        _execute_board_vcs(run_dir, timeout_sec)
    )


def acknowledge_checkpoint_after_remote_persistence(
    run_dir: Path,
    report: dict[str, Any],
    persistence: dict[str, Any],
) -> dict[str, Any]:
    checkpoint = report.get("checkpoint_artifacts", {})
    if (
        not isinstance(checkpoint, dict)
        or checkpoint.get("status") != "pass"
        or checkpoint.get("mode") != "cold_capture"
        or persistence.get("status") != "pass"
    ):
        return checkpoint if isinstance(checkpoint, dict) else {}
    manifest_path = Path(str(checkpoint.get("manifest") or ""))
    if not manifest_path.is_file() or not manifest_path.is_relative_to(
        checkpoint_root(run_dir).resolve()
    ):
        return {
            **checkpoint,
            "remote_acknowledgment_status": "fail",
            "remote_acknowledgment_error": (
                "checkpoint manifest is missing or outside the checkpoint store"
            ),
        }
    manifest = read_json(manifest_path)
    if manifest.get("remote_workdir") != report.get("remote_workdir"):
        return {
            **checkpoint,
            "remote_acknowledgment_status": "fail",
            "remote_acknowledgment_error": "checkpoint remote workdir mismatch",
        }
    manifest["remote_acknowledgment_status"] = "pass"
    write_json(manifest_path, manifest)
    return {
        **checkpoint,
        "remote_acknowledgment_status": "pass",
    }


def automatic_restore_check_environment(
    run_dir: Path,
    report: dict[str, Any],
) -> dict[str, str]:
    """Continue a successful capture directly into its one restore check."""

    if (
        report.get("status") != "checkpoint_capture_complete"
        or os.environ.get("SPATIALACC_FAST_REPLAY_RESTORE_CHECK") == "1"
    ):
        return {}
    state = read_fast_replay_state(run_dir)
    request_path = fast_replay_request_path(run_dir)
    if (
        state.get("status") != "captured"
        or state.get("verified") is not False
        or not request_path.is_file()
    ):
        return {}
    return {
        "SPATIALACC_CHECKPOINT_REQUIRED": "1",
        "SPATIALACC_CHECKPOINT_REPLAY": "1",
        "SPATIALACC_CHECKPOINT_REQUEST": str(request_path),
        "SPATIALACC_FAST_REPLAY": "1",
        "SPATIALACC_FAST_REPLAY_STATE": str(fast_replay_state_path(run_dir)),
        "SPATIALACC_FAST_REPLAY_RESTORE_CHECK": "1",
    }


def finalize_runner_report(
    run_dir: Path,
    report: dict[str, Any],
    *,
    lease: dict[str, Any],
    runner_implementation_sha256: str,
) -> tuple[dict[str, Any], Path]:
    """Persist one runner result and update execution-only replay state."""

    report["heavy_job_lease"] = {**lease, "status": "released"}
    report["runner_implementation_sha256"] = runner_implementation_sha256
    manifest_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "board_simulation_manifest.json"
    )
    manifest = read_json(manifest_path)
    if manifest:
        report["validation_mode"] = str(
            manifest.get("validation_mode") or "exact_sample_physical_ddr"
        )
        report["preflight_manifest_projection_sha256"] = (
            preflight_manifest_projection_sha256(manifest)
        )
    out = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    write_json(out, report)
    checkpoint = report.get("checkpoint_artifacts", {})
    if (
        report.get("phase") in {"remote_vcs", "fast_replay_recapture"}
        and isinstance(checkpoint, dict)
        and checkpoint.get("mode") == "cold_capture"
        and checkpoint.get("status") == "pass"
    ):
        report["checkpoint_artifacts"] = acknowledge_checkpoint_after_remote_persistence(
            run_dir,
            report,
            {"status": "pass"},
        )
        write_json(out, report)
    if (
        report.get("phase") in {
            "remote_vcs",
            "fast_replay_recapture",
            "fast_replay_restore_check",
        }
        and report.get("checkpoint_calibration_only") is not True
    ):
        report["fast_replay_state"] = update_fast_replay_state(run_dir, report)
        write_json(out, report)
    binding = board_run_binding(report)
    if binding:
        try:
            update_live_state_slot(
                run_dir,
                "board_run",
                board_run_status(report),
                binding=binding,
            )
        except OSError:
            pass
    return report, out


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir.resolve()
    runner_implementation_sha256 = sha256_file(Path(__file__).resolve())
    captured_transition: dict[str, Any] | None = None
    while True:
        with heavy_job_lease(
            run_dir,
            purpose="exact_board_vcs_controller",
            wait=True,
        ) as lease:
            report = execute(run_dir, args.timeout_sec)
        report, out = finalize_runner_report(
            run_dir,
            report,
            lease=lease,
            runner_implementation_sha256=runner_implementation_sha256,
        )
        restore_env = automatic_restore_check_environment(run_dir, report)
        if not restore_env:
            break
        captured_transition = {
            "status": "capture_complete",
            "checkpoint_id": report.get("checkpoint_artifacts", {}).get(
                "checkpoint_id"
            ),
            "remote_workdir": report.get("remote_workdir"),
            "next_action": "restore_once_and_check",
        }
        os.environ.pop("SPATIALACC_FAST_REPLAY_RECAPTURE", None)
        os.environ.update(restore_env)

    if captured_transition is not None:
        report["automatic_restore_check"] = {
            **captured_transition,
            "status": "complete",
            "result_status": report.get("status"),
            "restore_marker_seen": report.get(
                "checkpoint_restore_marker_seen"
            ),
            "observation_logs_rebound": report.get(
                "checkpoint_observation_logs_rebound"
            ),
            "board_progress_after_restore": report.get(
                "board_progress_after_restore"
            ),
        }
        write_json(out, report)
    print(out)
    if report.get("status") not in {
        "pass",
        "candidate_pass",
        "checkpoint_capture_complete",
        "checkpoint_restore_complete",
    }:
        print("case_board_vcs_functional.py: " + "; ".join(report.get("errors", [str(report.get("phase"))])[:10]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
