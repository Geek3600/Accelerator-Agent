#!/usr/bin/env python3
"""Discover app-shell integration targets and rebuild a bounded contract.

This tool is evidence-producing, not a board-specific patcher. It inspects the
Vivado app-shell project named by the current contract, records candidate IPs,
runs, files, and BD cells, and writes a recovery contract. It only selects a
target automatically when the evidence is unambiguous or an explicit
SPATIALACC_APP_SHELL_TARGET_IP is provided.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.semantic_simulator import persistent_remote_tool_workdir


SOURCE_WEIGHTS = {
    "bd_cell": 10,
    "ip": 8,
    "run": 3,
    "file": 1,
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def nonblank(value: Any) -> bool:
    return value is not None and value != "" and value != [] and str(value).strip().lower() not in {"none", "null"}


def first_nonblank(*values: Any) -> Any:
    for value in values:
        if nonblank(value):
            return value
    return None


def tcl_quote(value: Any) -> str:
    text = str(value or "")
    return "{" + text.replace("\\", "\\\\").replace("}", "\\}") + "}"


def run_cmd(argv: list[str], timeout_sec: int | None = None) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_sec, check=False)
        return {
            "argv": argv,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-8000:],
            "stderr_tail": proc.stderr[-8000:],
            "duration_sec": time.monotonic() - started,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "returncode": 124,
            "stdout_tail": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else "",
            "duration_sec": time.monotonic() - started,
        }


def parse_kv_report(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def split_items(value: str, limit: int = 160) -> list[str]:
    if not value:
        return []
    return [item for item in (part.strip() for part in value.split(",")) if item][:limit]


def compact_unique(items: list[str], limit: int = 120) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
        if len(result) >= limit:
            break
    return result


def truthy(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def scalar_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def list_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if any(sep in text for sep in [",", ";", "\n"]):
        return [item for item in (part.strip() for part in re.split(r"[,;\n]+", text)) if item]
    return [text]


def normalize_hint(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("\\", "/").rsplit("/", 1)[-1]
    text = re.sub(r"\s+", " ", text)
    return text


def add_hint(hints: list[str], sources: list[dict[str, str]], value: Any, source: str) -> None:
    for item in list_items(value):
        hint = normalize_hint(item)
        if len(hint) < 3:
            continue
        if hint not in hints:
            hints.append(hint)
            sources.append({"source": source, "value": item})


def env_value(name: str) -> str | None:
    value = os.environ.get(name)
    return value.strip() if isinstance(value, str) and value.strip() else None


def build_target_discovery_policy(contract: dict[str, Any]) -> dict[str, Any]:
    policy = contract.get("target_discovery_policy", {}) if isinstance(contract.get("target_discovery_policy"), dict) else {}
    target = contract.get("integration_target", {}) if isinstance(contract.get("integration_target"), dict) else {}
    hints: list[str] = []
    hint_sources: list[dict[str, str]] = []

    env_target = env_value("SPATIALACC_APP_SHELL_TARGET_IP")
    contract_target = first_nonblank(target.get("ip_name"), target.get("bd_cell"))
    explicit_target = first_nonblank(env_target, contract_target)
    if env_target:
        add_hint(hints, hint_sources, env_target, "env.SPATIALACC_APP_SHELL_TARGET_IP")
    elif contract_target:
        add_hint(hints, hint_sources, contract_target, "contract.integration_target")

    for key in ["candidate_name_hints", "target_name_hints", "keywords", "hint_keywords"]:
        add_hint(hints, hint_sources, policy.get(key), f"contract.target_discovery_policy.{key}")
    add_hint(hints, hint_sources, env_value("SPATIALACC_APP_SHELL_TARGET_KEYWORDS"), "env.SPATIALACC_APP_SHELL_TARGET_KEYWORDS")

    exclude_keywords: list[str] = []
    exclude_sources: list[dict[str, str]] = []
    for key in ["exclude_keywords", "exclude_name_hints"]:
        add_hint(exclude_keywords, exclude_sources, policy.get(key), f"contract.target_discovery_policy.{key}")
    add_hint(exclude_keywords, exclude_sources, env_value("SPATIALACC_APP_SHELL_EXCLUDE_KEYWORDS"), "env.SPATIALACC_APP_SHELL_EXCLUDE_KEYWORDS")

    env_auto_select = env_value("SPATIALACC_APP_SHELL_AUTO_SELECT_TARGET")
    auto_select = truthy(env_auto_select, truthy(policy.get("auto_select"), False)) if env_auto_select is not None else truthy(policy.get("auto_select"), False)
    score_threshold = scalar_int(env_value("SPATIALACC_APP_SHELL_TARGET_SCORE_THRESHOLD"), scalar_int(policy.get("score_threshold"), 30))
    selection_margin = scalar_int(env_value("SPATIALACC_APP_SHELL_TARGET_SELECTION_MARGIN"), scalar_int(policy.get("selection_margin"), 8))
    return {
        "schema_version": "spatialaccagent.app_shell_target_discovery_policy.v0",
        "explicit_target": str(explicit_target).strip() if explicit_target else None,
        "hint_keywords": hints,
        "hint_sources": hint_sources,
        "exclude_keywords": exclude_keywords,
        "exclude_sources": exclude_sources,
        "auto_select": auto_select,
        "auto_select_enabled": auto_select,
        "score_threshold": score_threshold,
        "selection_margin": selection_margin,
        "no_default_model_or_board_keywords": True,
        "policy_source": "contract/profile/env only; Vivado project names are evidence, not built-in selection rules",
    }


def build_tcl(project_xpr: str, hint_keywords: list[str]) -> str:
    keyword_tcl = " ".join(tcl_quote(item) for item in hint_keywords)
    return f"""# Generated by SpatialAccAgent app_shell_target_discovery.py.
set project_xpr {tcl_quote(project_xpr)}
set hint_keywords [list {keyword_tcl}]
set report_path "app_shell_target_discovery.txt"

proc record {{fh key value}} {{
  set clean [string map [list "\\n" " " "\\r" " " "=" ":"] $value]
  puts $fh "$key=$clean"
  puts "SPATIALACC_TARGET_DISCOVERY $key=$clean"
}}

proc matches_hint {{text}} {{
  global hint_keywords
  if {{[llength $hint_keywords] == 0}} {{
    return 1
  }}
  set lower [string tolower $text]
  foreach kw $hint_keywords {{
    if {{[string match "*$kw*" $lower]}} {{
      return 1
    }}
  }}
  return 0
}}

set fh [open $report_path w]
record $fh project_xpr $project_xpr
record $fh hint_keywords [join $hint_keywords ","]

if {{![file exists $project_xpr]}} {{
  record $fh project_exists 0
  close $fh
  exit 0
}}
record $fh project_exists 1

set open_status [catch {{open_project $project_xpr}} open_message]
record $fh open_project_status $open_status
record $fh open_project_message $open_message
if {{$open_status != 0}} {{
  close $fh
  exit 0
}}

record $fh current_project [current_project]
record $fh fileset_top [get_property TOP [current_fileset]]

set runs [get_runs -quiet *]
set candidate_runs {{}}
foreach run $runs {{
  if {{[matches_hint $run]}} {{
    lappend candidate_runs $run
  }}
}}
record $fh runs [join [lrange $runs 0 200] ","]
record $fh candidate_runs [join [lrange $candidate_runs 0 120] ","]

set project_files [get_files -quiet *]
set candidate_files {{}}
set hdl_files {{}}
foreach file $project_files {{
  set lower [string tolower $file]
  if {{[string match "*.sv" $lower] || [string match "*.v" $lower] || [string match "*.vhd" $lower] || [string match "*.xci" $lower] || [string match "*.xml" $lower]}} {{
    lappend hdl_files $file
  }}
  if {{[llength $hint_keywords] > 0 && [matches_hint $file]}} {{
    lappend candidate_files $file
  }}
}}
record $fh project_hdl_files_count [llength $hdl_files]
record $fh candidate_files [join [lrange $candidate_files 0 160] ","]

set ip_status [catch {{get_ips -quiet *}} ips]
record $fh get_ips_status $ip_status
if {{$ip_status == 0}} {{
  set ip_items {{}}
  set candidate_ips {{}}
  foreach ip $ips {{
    set vlnv [get_property -quiet VLNV $ip]
    set row "$ip|$vlnv"
    lappend ip_items $row
    if {{[matches_hint "$ip $vlnv"]}} {{
      lappend candidate_ips $row
    }}
  }}
  record $fh ips [join [lrange $ip_items 0 160] ","]
  record $fh candidate_ips [join [lrange $candidate_ips 0 120] ","]
}} else {{
  record $fh get_ips_message $ips
}}

set bd_files [get_files -quiet *.bd]
record $fh bd_files [join $bd_files ","]
record $fh bd_count [llength $bd_files]
set bd_cells_all {{}}
set candidate_bd_cells {{}}
set bd_open_failures {{}}
foreach bd $bd_files {{
  set bd_status [catch {{open_bd_design $bd}} bd_message]
  record $fh "bd_open_status.$bd" $bd_status
  record $fh "bd_open_message.$bd" $bd_message
  if {{$bd_status != 0}} {{
    lappend bd_open_failures "$bd|$bd_message"
    continue
  }}
  set cells [get_bd_cells -quiet -hier *]
  set intf_pins [get_bd_intf_pins -quiet -hier *]
  record $fh "bd_cells_count.$bd" [llength $cells]
  record $fh "bd_intf_pins_count.$bd" [llength $intf_pins]
  foreach cell $cells {{
    set vlnv [get_property -quiet VLNV $cell]
    set row "$cell|$vlnv"
    if {{[llength $bd_cells_all] < 200}} {{
      lappend bd_cells_all $row
    }}
    if {{[matches_hint "$cell $vlnv"]}} {{
      lappend candidate_bd_cells "$bd|$row"
    }}
  }}
}}
record $fh bd_open_failures [join [lrange $bd_open_failures 0 80] ","]
record $fh bd_cell_samples [join [lrange $bd_cells_all 0 160] ","]
record $fh candidate_bd_cells [join [lrange $candidate_bd_cells 0 120] ","]

close_project
close $fh
exit 0
"""


def parse_candidate_name(text: str, source: str) -> str:
    parts = text.split("|")
    if source == "bd_cell" and len(parts) >= 2:
        value = parts[1]
    else:
        value = parts[0]
    value = value.rsplit("/", 1)[-1]
    for suffix in ["_synth_1", "_impl_1", "_synth", "_impl"]:
        if value.endswith(suffix):
            value = value[: -len(suffix)]
    return value


def matches_hint(text: str, hint: str | None) -> bool:
    if not hint:
        return False
    return normalize_hint(hint) in text.lower()


def score_candidate(item: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("name", ""))
    evidence_text = " ".join(str(value) for value in item.get("raw_evidence", []))
    text = f"{name} {evidence_text}".lower()
    score = sum(SOURCE_WEIGHTS.get(str(source), 0) for source in item.get("sources", []))
    matched_hints: list[str] = []
    excluded_by: list[str] = []
    explicit_target = policy.get("explicit_target")
    if explicit_target and matches_hint(text, str(explicit_target)):
        score += 100
        matched_hints.append(str(explicit_target))
    for hint in policy.get("hint_keywords", []):
        if matches_hint(text, str(hint)):
            score += 20
            matched_hints.append(str(hint))
    for hint in policy.get("exclude_keywords", []):
        if matches_hint(text, str(hint)):
            excluded_by.append(str(hint))
    item["score"] = score if not excluded_by else -1
    item["matched_hints"] = compact_unique(matched_hints, 16)
    item["excluded_by"] = compact_unique(excluded_by, 16)
    item["selection_policy"] = "explicit/profile/env hints plus source evidence weights; no built-in model or board keywords"
    return item


def collect_candidates(discovery: dict[str, str], policy: dict[str, Any]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}

    def add(raw: str, source: str) -> None:
        if not raw:
            return
        name = parse_candidate_name(raw, source)
        if not name:
            return
        item = by_name.setdefault(
            name,
            {
                "name": name,
                "sources": [],
                "raw_evidence": [],
                "score": 0,
            },
        )
        if source not in item["sources"]:
            item["sources"].append(source)
        if raw not in item["raw_evidence"]:
            item["raw_evidence"].append(raw)

    for value in split_items(discovery.get("candidate_runs", "")):
        add(value, "run")
    # HDL/XCI file matches are useful support evidence, but they are not
    # integration targets. Target candidates must be Vivado runs, IPs, or BD
    # cells so generated leaf files under an IP directory do not swamp the
    # selection set.
    for value in split_items(discovery.get("candidate_ips", "")):
        add(value, "ip")
    for value in split_items(discovery.get("candidate_bd_cells", "")):
        add(value, "bd_cell")

    candidates = []
    for item in by_name.values():
        candidates.append(score_candidate(item, policy))
    return sorted(candidates, key=lambda item: (-int(item.get("score", 0)), str(item.get("name", ""))))


def choose_target(candidates: list[dict[str, Any]], policy: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    explicit_target = policy.get("explicit_target")
    selectable = [item for item in candidates if not item.get("excluded_by")]
    if explicit_target:
        matches = [
            item
            for item in selectable
            if matches_hint(
                f"{item.get('name', '')} {' '.join(str(value) for value in item.get('raw_evidence', []))}",
                str(explicit_target),
            )
        ]
        if len(matches) == 1:
            return matches[0], "explicit_target_matched"
        if not matches:
            return None, "explicit_target_not_found"
        return None, "explicit_target_ambiguous"
    if not policy.get("hint_keywords"):
        return None, "no_explicit_target_hint"
    if not policy.get("auto_select_enabled"):
        return None, "auto_select_disabled"
    threshold = int(policy.get("score_threshold", 30))
    margin = int(policy.get("selection_margin", 8))
    strong = [item for item in selectable if int(item.get("score", 0)) >= threshold]
    if len(strong) == 1:
        return strong[0], "single_high_confidence_candidate"
    if not strong:
        return None, "no_high_confidence_candidate"
    if int(strong[0].get("score", 0)) - int(strong[1].get("score", 0)) >= margin:
        return strong[0], "top_candidate_margin_met"
    return None, "multiple_high_confidence_candidates"


def build_recovery_contract(
    contract: dict[str, Any],
    app_shell_report: dict[str, Any],
    discovery: dict[str, str],
    policy: dict[str, Any],
    candidates: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    selection_reason: str,
    report_path: Path,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(contract))
    target = updated.get("integration_target") if isinstance(updated.get("integration_target"), dict) else {}
    if selected:
        target["ip_name"] = selected.get("name")
        target["selection_source"] = selection_reason
        target["selection_evidence"] = selected.get("raw_evidence", [])[:12]
        updated["integration_target"] = target
        updated["status"] = "ready_for_app_shell_generation"
    else:
        updated["integration_target"] = target
        updated["status"] = "target_discovery_needs_approval"
    active_candidates = [item for item in candidates if not item.get("excluded_by")]
    excluded_candidates = [item for item in candidates if item.get("excluded_by")]
    updated["target_discovery_policy"] = policy
    updated["target_discovery"] = {
        "schema_version": "spatialaccagent.app_shell_target_discovery.v0",
        "status": "selected" if selected else "needs_approval",
        "selection_reason": selection_reason,
        "selected_target": selected,
        "candidate_count": len(active_candidates),
        "excluded_candidate_count": len(excluded_candidates),
        "candidates": active_candidates[:24],
        "excluded_candidates": excluded_candidates[:12],
        "target_discovery_policy": policy,
        "project": {
            "project_exists": discovery.get("project_exists"),
            "open_project_status": discovery.get("open_project_status"),
            "fileset_top": discovery.get("fileset_top"),
            "bd_count": discovery.get("bd_count"),
            "bd_open_failures": split_items(discovery.get("bd_open_failures", ""), 20),
        },
        "prior_app_shell_blockers": app_shell_report.get("blockers", [])[:8]
        if isinstance(app_shell_report.get("blockers"), list)
        else [],
        "report_path": str(report_path),
    }
    updated["required_actions"] = [
        "Use only target_discovery_policy plus Vivado evidence candidates as automatic sources for integration_target updates.",
        "If target_discovery.status is needs_approval, a design-team/human-boundary approval must select a target before app-shell bitstream generation.",
        "If the top block design fails to open, rehydrate project/IP cache metadata without modifying external project semantics before selecting a target.",
        "After a target is selected, rerun app_shell_runtime_bitstream and runtime ABI gates before board runtime.",
    ]
    return updated


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover app-shell integration target candidates and rebuild the contract.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--app-shell-report", type=Path, required=True)
    parser.add_argument("--out-contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = args.run_dir.resolve()
    contract = read_json(args.contract)
    app_shell_report = read_json_if_exists(args.app_shell_report)
    shell = contract.get("shell_project", {}) if isinstance(contract.get("shell_project"), dict) else {}
    runtime = contract.get("runtime_abi", {}) if isinstance(contract.get("runtime_abi"), dict) else {}

    remote_host = first_nonblank(os.environ.get("REMOTE_HOST"), shell.get("remote_host"), runtime.get("remote_host"))
    remote_port = str(first_nonblank(os.environ.get("REMOTE_PORT"), shell.get("remote_ssh_port"), "22"))
    vivado_bin = str(first_nonblank(os.environ.get("VIVADO_BIN"), ""))
    project_xpr = str(first_nonblank(os.environ.get("SPATIALACC_APP_SHELL_PROJECT_XPR"), shell.get("vivado_project_path"), ""))
    policy = build_target_discovery_policy(contract)
    remote_known_hosts = os.environ.get("REMOTE_KNOWN_HOSTS", "/tmp/codex_ssh_known_hosts").strip()
    remote_workdir = os.environ.get(
        "REMOTE_WORKDIR",
        persistent_remote_tool_workdir(
            str(remote_host or ""), "vivado_app_shell_target_discovery", run_dir.name
        ),
    ).strip()

    out_dir = run_dir / "backend_board" / "app_shell_recovery"
    scripts_dir = run_dir / "generated" / "backend" / "scripts"
    tcl_path = scripts_dir / "app_shell_target_discovery.tcl"
    discovery_path = out_dir / "app_shell_target_discovery.txt"

    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    for name, value in [
        ("shell_project.vivado_project_path", project_xpr),
        ("REMOTE_HOST", remote_host),
        ("VIVADO_BIN", vivado_bin),
    ]:
        if not nonblank(value):
            blockers.append(f"{name} is not configured")

    commands: list[dict[str, Any]] = []
    discovery: dict[str, str] = {}
    if not blockers:
        tcl_path.parent.mkdir(parents=True, exist_ok=True)
        tcl_path.write_text(build_tcl(project_xpr, policy.get("hint_keywords", [])), encoding="utf-8")
        ssh_base = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            f"UserKnownHostsFile={remote_known_hosts}",
            "-p",
            remote_port,
            str(remote_host),
        ]
        scp_base = [
            "scp",
            "-q",
            "-P",
            remote_port,
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            f"UserKnownHostsFile={remote_known_hosts}",
        ]
        commands.append(run_cmd([*ssh_base, f"mkdir -p {shlex.quote(remote_workdir)} && rm -f {shlex.quote(remote_workdir)}/*"], 120))
        commands.append(run_cmd([*scp_base, str(tcl_path), f"{remote_host}:{remote_workdir}/"], 300))
        stamp = time.strftime("%Y%m%d_%H%M%S")
        remote_vivado = (
            f"cd {shlex.quote(remote_workdir)} && "
            f"{shlex.quote(str(vivado_bin))} -mode batch -source app_shell_target_discovery.tcl "
            f"-log app_shell_target_discovery_{stamp}.log -journal app_shell_target_discovery.jou"
        )
        commands.append(run_cmd([*ssh_base, remote_vivado], None))
        out_dir.mkdir(parents=True, exist_ok=True)
        commands.append(run_cmd([*scp_base, f"{remote_host}:{remote_workdir}/app_shell_target_discovery.txt", str(discovery_path)], 300))
        commands.append(run_cmd([*scp_base, f"{remote_host}:{remote_workdir}/app_shell_target_discovery_*.log", str(out_dir) + "/"], 300))
        for command in commands:
            if command.get("returncode") != 0:
                blockers.append(f"command failed returncode={command.get('returncode')}: {' '.join(command.get('argv', [])[:3])}")
                break
        discovery = parse_kv_report(discovery_path)

    candidates = collect_candidates(discovery, policy)
    selected, selection_reason = choose_target(candidates, policy)
    active_candidates = [item for item in candidates if not item.get("excluded_by")]
    recovery_contract = build_recovery_contract(contract, app_shell_report, discovery, policy, candidates, selected, selection_reason, args.out)
    write_json(args.out_contract, recovery_contract)

    checks.extend(
        [
            {"name": "contract_loaded", "status": "pass", "path": str(args.contract)},
            {"name": "vivado_project_opened", "status": "pass" if discovery.get("open_project_status") == "0" else "fail", "summary": discovery.get("open_project_message", "")},
            {"name": "target_candidate_discovery", "status": "pass" if active_candidates else "fail", "summary": f"candidate_count={len(active_candidates)}"},
            {"name": "target_auto_selection", "status": "pass" if selected else "needs_approval", "summary": selection_reason},
            {"name": "recovery_contract_written", "status": "pass" if args.out_contract.is_file() else "fail", "path": str(args.out_contract)},
        ]
    )
    if discovery.get("open_project_status") != "0":
        blockers.append(f"app-shell project did not open for target discovery: {discovery.get('open_project_message', '')}")
    if not active_candidates:
        blockers.append("no app-shell integration target candidates were discovered from runs/files/IP/BD evidence")

    recovery_status = "selected" if selected else ("needs_approval" if active_candidates else "blocked")
    report = {
        "schema_version": "spatialaccagent.app_shell_target_discovery_tool.v0",
        "status": "pass" if discovery.get("open_project_status") == "0" and args.out_contract.is_file() else "fail",
        "summary": f"target_discovery={recovery_status} candidates={len(active_candidates)} selection_reason={selection_reason}",
        "run_dir": str(run_dir),
        "contract": str(args.contract),
        "updated_contract": str(args.out_contract),
        "app_shell_report": str(args.app_shell_report),
        "remote_host": remote_host,
        "remote_workdir": remote_workdir,
        "vivado_bin": vivado_bin,
        "shell_project_xpr": project_xpr,
        "target_discovery_policy": policy,
        "explicit_target": policy.get("explicit_target"),
        "auto_select_enabled": policy.get("auto_select_enabled"),
        "recovery_status": recovery_status,
        "selection_reason": selection_reason,
        "selected_target": selected,
        "target_candidates": active_candidates[:48],
        "excluded_target_candidates": [item for item in candidates if item.get("excluded_by")][:24],
        "discovery": {
            "project_exists": discovery.get("project_exists"),
            "open_project_status": discovery.get("open_project_status"),
            "fileset_top": discovery.get("fileset_top"),
            "hint_keywords": split_items(discovery.get("hint_keywords", "")),
            "candidate_runs": split_items(discovery.get("candidate_runs", "")),
            "candidate_files": split_items(discovery.get("candidate_files", ""), 80),
            "candidate_ips": split_items(discovery.get("candidate_ips", "")),
            "candidate_bd_cells": split_items(discovery.get("candidate_bd_cells", "")),
            "bd_open_failures": split_items(discovery.get("bd_open_failures", ""), 40),
            "bd_cell_samples": split_items(discovery.get("bd_cell_samples", ""), 40),
        },
        "checks": checks,
        "blockers": compact_unique(blockers),
        "bounded_recovery_actions": recovery_contract.get("required_actions", []),
        "commands": commands,
        "acceptance_policy": "This tool passes when it writes an evidence-derived recovery contract; app-shell bitstream pass remains a separate real-tool gate.",
    }
    write_json(args.out, report)
    if report["status"] != "pass":
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
