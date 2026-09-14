"""Durable storage policy for exact-board real-tool evidence."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .semantic_simulator import (
    persist_remote_artifact_receipt,
    persistent_remote_tool_workdir,
    sha256_file,
)


RTL_SUFFIXES = {".v", ".sv", ".vhd", ".vhdl"}


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def board_remote_stage_root(
    manifest: dict[str, Any],
    run_dir: Path,
    host: str,
) -> str:
    root = str(
        manifest.get("remote_workdir")
        or os.environ.get("SPATIALACC_REMOTE_BOARD_VCS_ROOT")
        or persistent_remote_tool_workdir(host, "board_vcs", run_dir.name)
    ).rstrip("/")
    if (
        not root.startswith("/")
        or root == "/"
        or any(part in {".", ".."} for part in root.split("/"))
        or any(value in root for value in ("\0", "\n", "\r"))
    ):
        raise ValueError("board VCS remote stage root must be a safe absolute path")
    return root


def _path(value: Any) -> Path | None:
    text = str(value or "").strip()
    return Path(text) if text else None


def _append_path(paths: list[Path], value: Any) -> None:
    path = _path(value)
    if path is not None and path.is_file() and path.resolve() not in {
        item.resolve() for item in paths
    }:
        paths.append(path)


def _manifest_source_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = manifest.get("source_files")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _dynamic_evidence_paths(executed_manifest: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    records = executed_manifest.get("dynamic_evidence_records")
    if isinstance(records, list):
        for row in records:
            if isinstance(row, dict):
                _append_path(paths, row.get("path"))
    return paths


def persist_board_remote_artifacts(
    *,
    run_dir: Path,
    report: dict[str, Any],
    host: str,
    port: int,
    timeout_sec: int,
) -> dict[str, Any]:
    recovery = (
        report.get("remote_job_recovery_contract", {})
        if isinstance(report.get("remote_job_recovery_contract"), dict)
        else {}
    )
    job_contract_path = _path(recovery.get("job_contract"))
    fingerprint = str(report.get("input_fingerprint_sha256") or "")
    remote_dir = str(report.get("remote_workdir") or "").rstrip("/")
    job_contract = read_json(job_contract_path) if job_contract_path else {}
    remote_stage_root = str(job_contract.get("remote_stage_root") or "").rstrip("/")
    blockers = []
    if job_contract_path is None:
        blockers.append("board runner did not publish its remote job contract")
    if not remote_stage_root:
        blockers.append("board remote job contract has no persistent stage root")
    if blockers:
        return {
            "status": "fail",
            "blockers": blockers,
            "remote_workdir": remote_dir or None,
        }

    manifest_path = _path(report.get("manifest"))
    source_identity_path = _path(report.get("source_identity"))
    executed_manifest_path = _path(report.get("executed_manifest"))
    manifest = read_json(manifest_path) if manifest_path else {}
    executed_manifest = (
        read_json(executed_manifest_path) if executed_manifest_path else {}
    )
    integrity_blockers: list[str] = []
    for row in executed_manifest.get("dynamic_evidence_records", []):
        if not isinstance(row, dict) or not row.get("sha256"):
            continue
        path = _path(row.get("path"))
        if path is None or not path.is_file():
            integrity_blockers.append(
                f"hash-bound board evidence is missing: {row.get('path')}"
            )
        elif sha256_file(path) != str(row.get("sha256")):
            integrity_blockers.append(
                f"hash-bound board evidence changed before archival: {path}"
            )

    evidence_paths: list[Path] = []
    for value in (
        executed_manifest_path,
        report.get("compile_log"),
        report.get("sim_log"),
    ):
        _append_path(evidence_paths, value)
    for path in _dynamic_evidence_paths(executed_manifest):
        _append_path(evidence_paths, path)
    outputs = report.get("outputs")
    if isinstance(outputs, dict):
        for row in outputs.values():
            if isinstance(row, dict):
                _append_path(evidence_paths, row.get("path"))
    monitor_results = report.get("structured_monitor_results")
    if isinstance(monitor_results, dict):
        for row in monitor_results.values():
            if isinstance(row, dict):
                _append_path(evidence_paths, row.get("path"))

    required_evidence_paths: list[Path] = []
    for value in (executed_manifest_path, report.get("compile_log")):
        path = _path(value)
        if path is not None:
            required_evidence_paths.append(path)
    run_result = report.get("run")
    if isinstance(run_result, dict) and run_result.get("status") != "not_run":
        sim_log = _path(report.get("sim_log"))
        if sim_log is not None:
            required_evidence_paths.append(sim_log)
    for row in executed_manifest.get("dynamic_evidence_records", []):
        if isinstance(row, dict) and row.get("sha256"):
            path = _path(row.get("path"))
            if path is not None:
                required_evidence_paths.append(path)

    source_identity_paths: list[Path] = []
    for value in (manifest_path, source_identity_path):
        _append_path(source_identity_paths, value)
    source_rows = _manifest_source_rows(manifest)
    for row in source_rows:
        _append_path(source_identity_paths, row.get("path"))

    stage_sources = run_dir / "verification" / "board_simulation" / "vcs_stage" / "sources"
    snapshot_source_paths: list[Path] = []
    for row in source_rows:
        source = _path(row.get("path"))
        if source is None or source.suffix.lower() not in RTL_SUFFIXES:
            continue
        if str(row.get("role") or "") not in {
            "compute_slot_adapter",
            "multilayer_harness",
            "protocol_monitor",
            "testbench",
        }:
            continue
        staged_source = stage_sources / source.name
        if staged_source.is_file():
            expected_sha256 = str(row.get("sha256") or "")
            if expected_sha256 and sha256_file(staged_source) != expected_sha256:
                integrity_blockers.append(
                    f"staged board source changed before archival: {staged_source}"
                )
            snapshot_source_paths.append(staged_source)

    if integrity_blockers:
        return {
            "status": "fail",
            "blockers": integrity_blockers,
            "remote_workdir": remote_dir,
        }

    return persist_remote_artifact_receipt(
        host=host,
        port=port,
        run_dir=run_dir,
        namespace="board_vcs",
        remote_stage_root=remote_stage_root,
        remote_dir=remote_dir,
        fingerprint=fingerprint,
        job_contract_path=job_contract_path,
        evidence_paths=evidence_paths,
        required_evidence_paths=required_evidence_paths,
        source_identity_paths=source_identity_paths,
        snapshot_source_paths=snapshot_source_paths,
        timeout_sec=timeout_sec,
    )
