"""Verification-only evidence for a connected-kernel contradiction replay.

The board wrapper can observe complete ingress with no egress while a prior
single-layer CCTG certificate reports boundary liveness.  This module creates a
fresh, immutable-input replay that adds direct lifecycle probes to a *copy* of
the semantic testbench.  It never edits generated RTL, the canonical testbench,
or any workload artifact.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


IMMUTABLE_INPUT_SCHEMA = "spatialaccagent.connected_kernel_targeted_replay_inputs.v1"
TARGETED_TRACE_SCHEMA = "spatialaccagent.connected_kernel_cctg_targeted_replay_trace.v1"
CAUSAL_CONTEXT_SCHEMA = "spatialaccagent.connected_kernel_targeted_replay_causal_context.v1"
TARGETED_MANIFEST_SCHEMA = "spatialaccagent.connected_kernel_targeted_replay_manifest.v1"
RECONCILIATION_SCHEMA = "spatialaccagent.connected_kernel_cctg_contradiction_reconciliation.v1"

DIRECT_MARKER = "SPATIALACC_CONNECTED_KERNEL_DIRECT"
DIRECT_RECORD_RE = re.compile(
    rf"{DIRECT_MARKER}\s+kind=(?P<kind>\S+)\s+cycle=(?P<cycle>\d+)\s+"
    r"valid=(?P<valid>[01])\s+ready=(?P<ready>[01])\s+fire=(?P<fire>[01])\s+"
    r"accepted=(?P<accepted>\d+)\s+token=(?P<token>-?\d+)\s+beat=(?P<beat>-?\d+)\s+"
    r"st=(?P<st>[01])\s+last=(?P<last>[01])"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _row_path(row: Any, label: str, blockers: list[str]) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        blockers.append(f"{label} is not a hash-bound artifact row")
        return None
    path = Path(str(row.get("path") or ""))
    expected = str(row.get("sha256") or "")
    if not path.is_file():
        blockers.append(f"{label} is missing: {path}")
        return None
    if len(expected) != 64:
        blockers.append(f"{label} has no SHA-256 binding")
        return None
    actual = sha256_file(path)
    if actual != expected:
        blockers.append(f"{label} SHA-256 mismatch: {path}")
        return None
    return {"label": label, "path": str(path), "sha256": actual, "byte_count": path.stat().st_size}


def _path_binding(path: Path, expected: Any, label: str, blockers: list[str]) -> dict[str, Any] | None:
    return _row_path({"path": str(path), "sha256": expected}, label, blockers)


def immutable_semantic_replay_inputs(run_dir: Path) -> tuple[Path, dict[str, Any]]:
    """Freeze every immutable semantic input before deriving a probe testbench."""

    semantic_path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    repair_path = run_dir / "repair" / "immutable_semantic_replay_input_manifest.json"
    blockers: list[str] = []
    semantic = read_json(semantic_path) if semantic_path.is_file() else {}
    section = semantic.get("single_layer", {}) if isinstance(semantic.get("single_layer"), dict) else {}
    if semantic.get("status") != "ready":
        blockers.append("semantic testbench manifest is not ready")
    if section.get("status") != "ready" or section.get("real_weight_binding_verified") is not True:
        blockers.append("single-layer semantic testbench or real-weight binding is not ready")

    rows: list[dict[str, Any]] = []
    semantic_binding = _path_binding(
        semantic_path,
        sha256_file(semantic_path) if semantic_path.is_file() else None,
        "semantic_testbench_manifest",
        blockers,
    )
    if semantic_binding:
        rows.append(semantic_binding)
    for label, row in (
        ("canonical_semantic_testbench", {"path": section.get("testbench"), "sha256": section.get("testbench_sha256")} ),
        ("single_layer_expected_output", section.get("expected_output")),
        ("single_layer_real_weight_stream", section.get("real_weight_stream")),
        ("numeric_policy", {"path": semantic.get("numeric_policy"), "sha256": semantic.get("numeric_policy_sha256")} ),
        ("dut_weight_binding_manifest", {"path": semantic.get("dut_weight_binding_manifest"), "sha256": _existing_sha256(semantic.get("dut_weight_binding_manifest"))}),
        ("dut_weight_binding_requirements", {"path": semantic.get("dut_weight_binding_requirements"), "sha256": semantic.get("dut_weight_binding_requirements_sha256")} ),
    ):
        binding = _row_path(row, label, blockers)
        if binding:
            rows.append(binding)
    for index, row in enumerate(section.get("input_vectors", [])):
        binding = _row_path(row, f"single_layer_input_vector[{index}]", blockers)
        if binding:
            rows.append(binding)
    runtime = section.get("runtime_constant_stream", {})
    runtime_row = (
        runtime.get("stream", {})
        if isinstance(runtime, dict) and isinstance(runtime.get("stream"), dict)
        else runtime
    )
    binding = _row_path(runtime_row, "single_layer_runtime_constant_stream", blockers)
    if binding:
        rows.append(binding)
    harness = section.get("dut_harness", {}) if isinstance(section.get("dut_harness"), dict) else {}
    source_rows = harness.get("source_files", []) if isinstance(harness.get("source_files"), list) else []
    if not source_rows:
        blockers.append("single-layer semantic harness has no source closure")
    for index, row in enumerate(source_rows):
        binding = _row_path(row, f"single_layer_source_closure[{index}]", blockers)
        if binding:
            rows.append(binding)
    contract = section.get("pipeline_overlap_contract", {}) if isinstance(section.get("pipeline_overlap_contract"), dict) else {}
    if not str(contract.get("contract_sha256") or ""):
        blockers.append("single-layer pipeline/CCTG contract has no declared hash")
    if int(contract.get("token_count") or 0) <= 0 or int(contract.get("beats_per_token") or 0) <= 0:
        blockers.append("single-layer pipeline/CCTG contract has invalid token geometry")
    duplicate_paths = [row["path"] for row in rows]
    if len(set(duplicate_paths)) != len(duplicate_paths):
        # The same data may be represented by separate semantic roles; preserve
        # those roles but make the identity explicit rather than accepting an
        # accidental unbound duplicate.
        role_paths: dict[str, list[str]] = {}
        for row in rows:
            role_paths.setdefault(row["path"], []).append(row["label"])
    else:
        role_paths = {}
    report = {
        "schema_version": IMMUTABLE_INPUT_SCHEMA,
        "status": "pass" if not blockers else "fail",
        "summary": (
            "immutable real-weight semantic replay inputs are hash-bound"
            if not blockers
            else "immutable semantic replay input binding failed closed"
        ),
        "semantic_testbench_manifest": str(semantic_path),
        "semantic_testbench_manifest_sha256": sha256_file(semantic_path) if semantic_path.is_file() else None,
        "single_layer_semantic_contract_sha256": canonical_sha256(section) if section else None,
        "pipeline_contract": {
            "declared_sha256": contract.get("contract_sha256"),
            "canonical_sha256": canonical_sha256(contract) if contract else None,
            "token_count": contract.get("token_count"),
            "beats_per_token": contract.get("beats_per_token"),
            "required_boundaries": contract.get("required_boundaries", []),
        },
        "artifact_rows": rows,
        "role_path_aliases": role_paths,
        "source_closure_sha256": canonical_sha256(
            [row for row in rows if row["label"].startswith("single_layer_source_closure[")]
        ),
        "policy": {
            "canonical_testbench_is_read_only": True,
            "generated_rtl_is_read_only": True,
            "real_input_weight_runtime_golden_and_numeric_policy_are_immutable": True,
            "replay_testbench_may_add_read_only_observations_only": True,
        },
        "blockers": blockers,
    }
    write_json(repair_path, report)
    return repair_path, report


def _existing_sha256(path_value: Any) -> str | None:
    path = Path(str(path_value or ""))
    return sha256_file(path) if path.is_file() else None


def _identifiers(source: str) -> set[str]:
    return set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_$]*\b", source))


def _one_identifier(identifiers: set[str], pattern: str, role: str, blockers: list[str]) -> str:
    matches = sorted(value for value in identifiers if re.fullmatch(pattern, value, re.IGNORECASE))
    if len(matches) != 1:
        blockers.append(f"connected-kernel probe cannot uniquely bind {role}: {matches}")
        return ""
    return matches[0]


def discover_direct_probe_bindings(section: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Discover generated-harness hierarchy without target-model constants."""

    blockers: list[str] = []
    harness = section.get("dut_harness", {}) if isinstance(section.get("dut_harness"), dict) else {}
    top_module = str(harness.get("top_module") or "")
    testbench = Path(str(section.get("testbench") or ""))
    source_rows = harness.get("source_files", []) if isinstance(harness.get("source_files"), list) else []
    if not top_module or not testbench.is_file():
        return {}, ["semantic harness top module or canonical testbench is missing"]
    testbench_text = testbench.read_text(encoding="utf-8", errors="ignore")
    instance_matches = re.findall(
        rf"\b{re.escape(top_module)}\s+(?P<instance>[A-Za-z_][A-Za-z0-9_$]*)\s*\(",
        testbench_text,
    )
    if len(instance_matches) != 1:
        blockers.append(f"semantic testbench cannot uniquely bind harness instance: {instance_matches}")
        return {}, blockers
    sources: list[tuple[Path, str]] = []
    for row in source_rows:
        path = Path(str(row.get("path") or "")) if isinstance(row, dict) else Path()
        if path.is_file():
            sources.append((path, path.read_text(encoding="utf-8", errors="ignore")))
    harness_source = next(
        (
            text
            for _, text in sources
            if re.search(rf"\bmodule\s+{re.escape(top_module)}\b", text)
        ),
        "",
    )
    core_matches = [
        match
        for match in re.finditer(
            r"^\s*(?P<module>[A-Za-z_][A-Za-z0-9_$]*)\s+(?P<instance>[A-Za-z_][A-Za-z0-9_$]*)\s*\(\s*(?P<body>\.[\s\S]*?)^\s*\);",
            harness_source,
            re.MULTILINE,
        )
        if ".io_in_valid" in match.group("body") and ".io_out_valid" in match.group("body")
    ]
    if len(core_matches) != 1:
        blockers.append("semantic harness cannot uniquely bind connected-kernel instance")
        return {}, blockers
    core_module = core_matches[0].group("module")
    core_instance = core_matches[0].group("instance")
    core_source = next(
        (text for _, text in sources if re.search(rf"\bmodule\s+{re.escape(core_module)}\b", text)),
        "",
    )
    identifiers = _identifiers(core_source)
    required_ports = [
        "io_in_valid",
        "io_in_ready",
        "io_in_bits_addr",
        "io_in_bits_st",
        "io_in_bits_last",
        "io_out_valid",
        "io_out_ready",
    ]
    missing_ports = [name for name in required_ports if name not in identifiers]
    if missing_ports:
        blockers.append(f"connected-kernel direct lifecycle ports are unavailable: {missing_ports}")
    mul_valid = _one_identifier(identifiers, r".*mlp.*mul.*io.*out.*valid.*", "MLP-mul valid", blockers)
    down_valid = _one_identifier(identifiers, r".*mlp.*down.*io.*out.*valid.*", "MLP-down valid", blockers)
    residual_valid = _one_identifier(identifiers, r".*add2.*io.*out.*valid.*", "residual-2 valid", blockers)
    residual_ready = _one_identifier(identifiers, r".*add2.*io.*computed.*ready.*", "residual-2 computed ready", blockers)

    def companion(valid: str, replacement: str, role: str) -> str:
        candidate = valid.replace("valid", replacement)
        if not candidate or candidate not in identifiers:
            blockers.append(f"connected-kernel probe lacks {role} companion for {valid}")
            return ""
        return candidate

    bindings = {
        "testbench_instance": instance_matches[0],
        "core_module": core_module,
        "core_instance": core_instance,
        "core_path": f"{instance_matches[0]}.{core_instance}",
        "signals": {
            "mlp_mul_valid": mul_valid,
            "mlp_mul_ready": companion(mul_valid, "ready", "MLP-mul ready"),
            "mlp_mul_addr": companion(mul_valid, "bits_addr", "MLP-mul addr"),
            "mlp_mul_st": companion(mul_valid, "bits_st", "MLP-mul st"),
            "mlp_mul_last": companion(mul_valid, "bits_last", "MLP-mul last"),
            "mlp_down_valid": down_valid,
            "mlp_down_ready": companion(down_valid, "ready", "MLP-down ready"),
            "mlp_down_addr": companion(down_valid, "bits_addr", "MLP-down addr"),
            "mlp_down_st": companion(down_valid, "bits_st", "MLP-down st"),
            "mlp_down_last": companion(down_valid, "bits_last", "MLP-down last"),
            "residual_valid": residual_valid,
            "residual_ready": residual_ready,
        },
    }
    return (bindings if not blockers else {}), blockers


def _direct_probe_block(bindings: dict[str, Any], beats_per_token: int) -> str:
    core = str(bindings["core_path"])
    signal = bindings["signals"]
    return f'''

  // Verification-only direct lifecycle probes. These counters and displays do
  // not drive DUT ports or alter the canonical semantic testbench.
  integer connected_kernel_direct_cycle = 0;
  integer connected_kernel_ingress_accepted = 0;
  integer connected_kernel_egress_accepted = 0;
  integer connected_kernel_mlp_mul_accepted = 0;
  integer connected_kernel_mlp_down_accepted = 0;
  reg connected_kernel_direct_started = 0;
  reg connected_kernel_egress_valid_seen = 0;
  reg connected_kernel_egress_ready_seen = 0;
  reg connected_kernel_residual_valid_seen = 0;
  reg connected_kernel_residual_ready_seen = 0;
  always @(posedge clock) begin
    if (reset) begin
      connected_kernel_direct_cycle = 0;
      connected_kernel_ingress_accepted = 0;
      connected_kernel_egress_accepted = 0;
      connected_kernel_mlp_mul_accepted = 0;
      connected_kernel_mlp_down_accepted = 0;
      connected_kernel_direct_started = 0;
      connected_kernel_egress_valid_seen = 0;
      connected_kernel_egress_ready_seen = 0;
      connected_kernel_residual_valid_seen = 0;
      connected_kernel_residual_ready_seen = 0;
    end else begin
      connected_kernel_direct_cycle = connected_kernel_direct_cycle + 1;
      if (start && !connected_kernel_direct_started) begin
        connected_kernel_direct_started = 1;
        $display("{DIRECT_MARKER} kind=start cycle=%0d valid=0 ready=0 fire=0 accepted=0 token=-1 beat=-1 st=0 last=0", connected_kernel_direct_cycle);
      end
      if ({core}.io_in_valid && {core}.io_in_ready) begin
        connected_kernel_ingress_accepted = connected_kernel_ingress_accepted + 1;
        if ({core}.io_in_bits_st || {core}.io_in_bits_last)
          $display("{DIRECT_MARKER} kind=core_ingress cycle=%0d valid=1 ready=1 fire=1 accepted=%0d token=%0d beat=%0d st=%0d last=%0d", connected_kernel_direct_cycle, connected_kernel_ingress_accepted, {core}.io_in_bits_addr / {beats_per_token}, {core}.io_in_bits_addr % {beats_per_token}, {core}.io_in_bits_st, {core}.io_in_bits_last);
      end
      if ({core}.{signal['mlp_mul_valid']} && {core}.{signal['mlp_mul_ready']}) begin
        connected_kernel_mlp_mul_accepted = connected_kernel_mlp_mul_accepted + 1;
        if ({core}.{signal['mlp_mul_st']} || {core}.{signal['mlp_mul_last']})
          $display("{DIRECT_MARKER} kind=mlp_mul_tail cycle=%0d valid=1 ready=1 fire=1 accepted=%0d token=-1 beat=-1 st=%0d last=%0d", connected_kernel_direct_cycle, connected_kernel_mlp_mul_accepted, {core}.{signal['mlp_mul_st']}, {core}.{signal['mlp_mul_last']});
      end
      if ({core}.{signal['mlp_down_valid']} && {core}.{signal['mlp_down_ready']}) begin
        connected_kernel_mlp_down_accepted = connected_kernel_mlp_down_accepted + 1;
        if ({core}.{signal['mlp_down_st']} || {core}.{signal['mlp_down_last']})
          $display("{DIRECT_MARKER} kind=mlp_down_tail cycle=%0d valid=1 ready=1 fire=1 accepted=%0d token=-1 beat=-1 st=%0d last=%0d", connected_kernel_direct_cycle, connected_kernel_mlp_down_accepted, {core}.{signal['mlp_down_st']}, {core}.{signal['mlp_down_last']});
      end
      if ({core}.{signal['residual_valid']} != connected_kernel_residual_valid_seen || {core}.{signal['residual_ready']} != connected_kernel_residual_ready_seen) begin
        connected_kernel_residual_valid_seen = {core}.{signal['residual_valid']};
        connected_kernel_residual_ready_seen = {core}.{signal['residual_ready']};
        $display("{DIRECT_MARKER} kind=residual2_frontier cycle=%0d valid=%0d ready=%0d fire=%0d accepted=%0d token=-1 beat=-1 st=0 last=0", connected_kernel_direct_cycle, {core}.{signal['residual_valid']}, {core}.{signal['residual_ready']}, {core}.{signal['residual_valid']} && {core}.{signal['residual_ready']}, connected_kernel_egress_accepted);
      end
      if ({core}.io_out_valid != connected_kernel_egress_valid_seen || {core}.io_out_ready != connected_kernel_egress_ready_seen || ({core}.io_out_valid && {core}.io_out_ready && ((connected_kernel_egress_accepted % {beats_per_token}) == {beats_per_token - 1}))) begin
        connected_kernel_egress_valid_seen = {core}.io_out_valid;
        connected_kernel_egress_ready_seen = {core}.io_out_ready;
        $display("{DIRECT_MARKER} kind=core_egress cycle=%0d valid=%0d ready=%0d fire=%0d accepted=%0d token=%0d beat=%0d st=0 last=%0d", connected_kernel_direct_cycle, {core}.io_out_valid, {core}.io_out_ready, {core}.io_out_valid && {core}.io_out_ready, connected_kernel_egress_accepted + ({core}.io_out_valid && {core}.io_out_ready), connected_kernel_egress_accepted / {beats_per_token}, connected_kernel_egress_accepted % {beats_per_token}, ((connected_kernel_egress_accepted % {beats_per_token}) == {beats_per_token - 1}));
      end
      if ({core}.io_out_valid && {core}.io_out_ready)
        connected_kernel_egress_accepted = connected_kernel_egress_accepted + 1;
    end
  end
'''


def materialize_connected_kernel_replay_testbench(run_dir: Path, section: dict[str, Any]) -> tuple[Path | None, dict[str, Any]]:
    """Create an observation-only semantic testbench copy and its binding record."""

    immutable_path = run_dir / "repair" / "immutable_semantic_replay_input_manifest.json"
    immutable = read_json(immutable_path) if immutable_path.is_file() else {}
    testbench = Path(str(section.get("testbench") or ""))
    blockers = []
    if immutable.get("status") != "pass":
        blockers.append("immutable semantic replay input manifest is not passing")
    if not testbench.is_file() or sha256_file(testbench) != section.get("testbench_sha256"):
        blockers.append("canonical semantic testbench changed or is unavailable")
    bindings, binding_errors = discover_direct_probe_bindings(section)
    blockers.extend(binding_errors)
    contract = section.get("pipeline_overlap_contract", {}) if isinstance(section.get("pipeline_overlap_contract"), dict) else {}
    beats_per_token = int(contract.get("beats_per_token") or 0)
    if beats_per_token <= 0:
        blockers.append("pipeline overlap contract has no positive beats_per_token")
    replay_path = run_dir / "verification" / "debug_closure" / "connected_kernel_targeted_replay_tb.sv"
    report_path = run_dir / "verification" / "case_diagnostics" / "connected_kernel_targeted_replay_manifest.json"
    if not blockers:
        original = testbench.read_text(encoding="utf-8", errors="ignore")
        endmodule = original.rfind("endmodule")
        if endmodule < 0:
            blockers.append("canonical semantic testbench has no endmodule")
        else:
            replay_path.parent.mkdir(parents=True, exist_ok=True)
            replay_path.write_text(
                original[:endmodule] + _direct_probe_block(bindings, beats_per_token) + original[endmodule:],
                encoding="ascii",
            )
    report = {
        "schema_version": TARGETED_MANIFEST_SCHEMA,
        "status": "pass" if not blockers else "fail",
        "summary": (
            "connected-kernel direct-observation replay testbench is materialized"
            if not blockers
            else "connected-kernel direct-observation replay testbench could not be materialized"
        ),
        "immutable_input_manifest": {"path": str(immutable_path), "sha256": _existing_sha256(immutable_path)},
        "canonical_testbench": {"path": str(testbench), "sha256": section.get("testbench_sha256")},
        "replay_testbench": {"path": str(replay_path), "sha256": _existing_sha256(replay_path)},
        "direct_probe_bindings": bindings,
        "policy": {
            "canonical_testbench_modified": False,
            "generated_rtl_modified": False,
            "probe_is_read_only": True,
            "no_dut_port_is_driven_by_probe": True,
        },
        "blockers": blockers,
    }
    write_json(report_path, report)
    return (replay_path if not blockers else None), report


def replay_semantic_contract(section: dict[str, Any], replay_testbench: Path) -> dict[str, Any]:
    """Return an in-memory contract that only changes the verification sink."""

    contract = copy.deepcopy(section)
    contract["testbench"] = str(replay_testbench)
    contract["testbench_sha256"] = sha256_file(replay_testbench)
    contract["rtl_output_capture"] = str(
        replay_testbench.parent / "connected_kernel_targeted_replay_output.memh"
    )
    return contract


def direct_observation_records(execution: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    unparsed = 0
    for key in ("sim_log", "sim_stderr_log"):
        path = Path(str(execution.get(key) or ""))
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if DIRECT_MARKER not in line:
                continue
            match = DIRECT_RECORD_RE.search(line)
            if match is None:
                unparsed += 1
                continue
            row = {name: int(match.group(name)) if name != "kind" else match.group(name) for name in DIRECT_RECORD_RE.groupindex}
            identity = tuple(row[name] for name in ("kind", "cycle", "valid", "ready", "fire", "accepted", "token", "beat", "st", "last"))
            if identity not in seen:
                seen.add(identity)
                records.append(row)
    records.sort(key=lambda row: (row["cycle"], row["kind"], row["accepted"]))
    return records, unparsed


def _fresh_remote_execution(execution: dict[str, Any]) -> bool:
    reuse = execution.get("remote_job_reuse", {}) if isinstance(execution.get("remote_job_reuse"), dict) else {}
    return bool(
        execution.get("status") == "pass"
        and execution.get("simulator") == "vcs"
        and execution.get("tool_scope") == "remote"
        and execution.get("fresh_remote_vcs_execution_required") is True
        and reuse.get("real_tool_was_not_relaunched") is False
        and isinstance(execution.get("run"), dict)
        and execution["run"].get("status") == "pass"
    )


def _board_contradiction(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json"
    diagnosis = read_json(path) if path.is_file() else {}
    rendered = json.dumps(diagnosis, sort_keys=True)
    ingress = re.findall(r'"core_ingress_accepted_count"\s*:\s*(\d+)', rendered)
    egress = re.findall(r'"core_egress_accepted_count"\s*:\s*(\d+)', rendered)
    return {
        "path": str(path),
        "sha256": _existing_sha256(path),
        "failure_class": diagnosis.get("failure_class"),
        "core_ingress_accepted_count": int(ingress[-1]) if ingress else None,
        "core_egress_accepted_count": int(egress[-1]) if egress else None,
    }


def materialize_connected_kernel_targeted_replay_evidence(
    run_dir: Path,
    execution: dict[str, Any],
    cctg_evidence: dict[str, Any],
) -> dict[str, Path | dict[str, Any]]:
    """Persist direct lifecycle evidence and a bounded board/CCTG reconciliation."""

    immutable_path = run_dir / "repair" / "immutable_semantic_replay_input_manifest.json"
    manifest_path = run_dir / "verification" / "case_diagnostics" / "connected_kernel_targeted_replay_manifest.json"
    immutable = read_json(immutable_path) if immutable_path.is_file() else {}
    manifest = read_json(manifest_path) if manifest_path.is_file() else {}
    records, unparsed = direct_observation_records(execution)
    by_kind = {kind: [row for row in records if row["kind"] == kind] for kind in {row["kind"] for row in records}}
    geometry = immutable.get("pipeline_contract", {}) if isinstance(immutable.get("pipeline_contract"), dict) else {}
    expected_ingress = int(geometry.get("token_count") or 0) * int(geometry.get("beats_per_token") or 0)
    latest = {
        kind: max(rows, key=lambda row: (row["accepted"], row["cycle"]))
        for kind, rows in by_kind.items() if rows
    }
    blockers: list[str] = []
    if immutable.get("status") != "pass" or manifest.get("status") != "pass":
        blockers.append("immutable replay input or direct-probe manifest is not passing")
    if not _fresh_remote_execution(execution):
        blockers.append("connected-kernel targeted replay requires a fresh completed remote VCS execution")
    if unparsed:
        blockers.append("connected-kernel direct observation stream contains unparsed markers")
    for kind in ("core_ingress", "mlp_mul_tail", "mlp_down_tail", "residual2_frontier", "core_egress"):
        if not by_kind.get(kind):
            blockers.append(f"connected-kernel direct observation is missing {kind}")
    start_witness = next(
        (
            row
            for row in by_kind.get("start", [])
            if row["accepted"] == 0
        ),
        None,
    )
    first_fired_ingress = next(
        (
            row
            for row in by_kind.get("core_ingress", [])
            if row["valid"] == 1
            and row["ready"] == 1
            and row["fire"] == 1
            and row["accepted"] == 1
        ),
        None,
    )
    if start_witness is None and first_fired_ingress is None:
        blockers.append(
            "connected-kernel direct observation is missing start and has no "
            "first accepted core-ingress handshake"
        )
    expected_ingress_complete = (
        latest.get("core_ingress", {}).get("accepted") == expected_ingress
    )
    expected_egress_complete = (
        latest.get("core_egress", {}).get("accepted") == expected_ingress
    )
    terminal_egress = next(
        (
            row
            for row in reversed(by_kind.get("core_egress", []))
            if row["fire"] == 1
            and row["accepted"] == expected_ingress
            and row["last"] == 1
        ),
        None,
    )
    if not expected_ingress_complete:
        blockers.append(
            "connected-kernel direct observation does not show complete core ingress"
        )
    if not expected_egress_complete:
        blockers.append(
            "connected-kernel direct observation does not show complete core egress"
        )
    if terminal_egress is None:
        blockers.append(
            "connected-kernel direct observation is missing terminal core egress last"
        )
    cctg_status = cctg_evidence.get("status") if isinstance(cctg_evidence, dict) else None
    if cctg_status != "pass" or cctg_evidence.get("fresh_remote_vcs_execution_observed") is not True:
        blockers.append("targeted replay has no fresh CCTG boundary evidence")
    trace = {
        "schema_version": TARGETED_TRACE_SCHEMA,
        "status": "pass" if not blockers else "fail",
        "summary": (
            "fresh direct connected-kernel lifecycle observations were captured"
            if not blockers
            else "fresh connected-kernel lifecycle observations are incomplete"
        ),
        "immutable_input_manifest": {"path": str(immutable_path), "sha256": _existing_sha256(immutable_path)},
        "direct_probe_manifest": {"path": str(manifest_path), "sha256": _existing_sha256(manifest_path)},
        "source_execution": {
            "input_fingerprint_sha256": execution.get("input_fingerprint_sha256"),
            "remote_workdir": execution.get("remote_workdir"),
            "sim_log": {"path": execution.get("sim_log"), "sha256": _existing_sha256(Path(str(execution.get("sim_log") or "")))},
            "sim_stderr_log": {"path": execution.get("sim_stderr_log"), "sha256": _existing_sha256(Path(str(execution.get("sim_stderr_log") or "")))},
        },
        "fresh_remote_vcs_execution_observed": _fresh_remote_execution(execution),
        "expected_ingress_beats": expected_ingress,
        "record_count": len(records),
        "unparsed_record_count": unparsed,
        "records": records,
        "latest_by_kind": latest,
        "start_witness": {
            "source": "standalone_start_marker" if start_witness is not None else "first_accepted_core_ingress",
            "record": start_witness or first_fired_ingress,
        },
        "lifecycle": {
            "ingress_complete": expected_ingress_complete,
            "egress_accepted_count": latest.get("core_egress", {}).get("accepted", 0),
            "egress_complete": expected_egress_complete,
            "terminal_egress_last": terminal_egress is not None,
            "mlp_mul_accepted_count": latest.get("mlp_mul_tail", {}).get("accepted", 0),
            "mlp_down_accepted_count": latest.get("mlp_down_tail", {}).get("accepted", 0),
        },
        "cctg_boundary_replay": cctg_evidence,
        "blockers": blockers,
    }
    trace_path = run_dir / "verification" / "debug_closure" / "connected_kernel_cctg_targeted_replay_trace.json"
    write_json(trace_path, trace)
    board = _board_contradiction(run_dir)
    direct = trace["lifecycle"]
    deterministic_earliest_owner = None
    if trace["status"] == "pass" and direct["ingress_complete"]:
        if direct["mlp_mul_accepted_count"] == 0:
            deterministic_earliest_owner = "before_mlp_mul_tail"
        elif direct["mlp_down_accepted_count"] == 0:
            deterministic_earliest_owner = "mlp_mul_to_mlp_down_tail"
        elif direct["egress_accepted_count"] == 0:
            deterministic_earliest_owner = "mlp_down_to_connected_kernel_egress"
    reconciliation = {
        "schema_version": RECONCILIATION_SCHEMA,
        "status": "pass" if trace["status"] == "pass" else "fail",
        "summary": "board and fresh connected-kernel observations are bound for Agent causal localization",
        "board_observation": board,
        "fresh_connected_kernel_observation": {
            "trace_path": str(trace_path),
            "trace_sha256": sha256_file(trace_path),
            "lifecycle": direct,
            "cctg_boundary_liveness_status": cctg_evidence.get("boundary_liveness_status"),
        },
        "deterministic_earliest_owner": deterministic_earliest_owner,
        "rtl_repair_authorized": deterministic_earliest_owner is not None,
        "policy": {
            "agent_must_localize_before_behavioral_repair": True,
            "board_wrapper_axi_ddr_and_data_artifacts_remain_read_only": True,
            "no_owner_means_no_rtl_repair_authorization": True,
        },
        "blockers": blockers,
    }
    reconciliation_path = run_dir / "verification" / "case_diagnostics" / "connected_kernel_cctg_contradiction_reconciliation.json"
    write_json(reconciliation_path, reconciliation)
    context = {
        "schema_version": CAUSAL_CONTEXT_SCHEMA,
        "status": "pass" if trace["status"] == "pass" else "fail",
        "summary": "fresh connected-kernel direct replay package for the next Agent decision",
        "immutable_semantic_replay_input_manifest": {"path": str(immutable_path), "sha256": _existing_sha256(immutable_path)},
        "connected_kernel_cctg_targeted_replay_trace": {"path": str(trace_path), "sha256": sha256_file(trace_path)},
        "connected_kernel_targeted_replay_manifest": {"path": str(manifest_path), "sha256": _existing_sha256(manifest_path)},
        "connected_kernel_cctg_contradiction_reconciliation": {"path": str(reconciliation_path), "sha256": sha256_file(reconciliation_path)},
        "direct_observation_sufficiency_status": trace["status"],
        "blockers": blockers,
    }
    context_path = run_dir / "verification" / "case_diagnostics" / "connected_kernel_targeted_replay_causal_context.json"
    write_json(context_path, context)
    return {
        "trace_path": trace_path,
        "trace": trace,
        "context_path": context_path,
        "context": context,
        "reconciliation_path": reconciliation_path,
        "reconciliation": reconciliation,
    }
