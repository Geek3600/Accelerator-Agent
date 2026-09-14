#!/usr/bin/env python3
"""Materialize a Vivado-derived external board simulation fixture.

The existing board identity describes the user design and its configured IPs.
This module follows those structured source-owner and interface-net relations to
the configured IP that owns the selected external timing model, asks Vivado for
that IP's official example simulation project, and snapshots the resulting VCS
compile authority.  It never searches legacy, case-specific fixture directories.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.verification.sample_project_board_interface_impl import (
    _decode_fact_field,
    _fetch_source_payloads,
    _parse_missing_instances,
    command_timeout,
    remote_exec,
    remote_read,
    run_checked,
    scp_prefix,
    sha256_bytes,
    sha256_file,
    source_bytes,
    ssh_prefix,
    write_json,
)


SCHEMA_VERSION = "spatialaccagent.external_simulation_fixture.v2"
AUTHORITY_SCHEMA_VERSION = "spatialaccagent.external_simulation_fixture_authority.v1"
EXPORT_SCHEMA_VERSION = "spatialaccagent.vivado_external_fixture_export.v1"
COMPILE_AUTHORITY_SCHEMA_VERSION = (
    "spatialaccagent.vivado_external_fixture_vcs_compile_authority.v2"
)
FORBIDDEN_LEGACY_ROOT = (REPO_ROOT / "verification" / "board_ddr_ip").resolve()

HDL_SUFFIXES = {
    ".v",
    ".vh",
    ".vp",
    ".sv",
    ".svh",
    ".svp",
    ".vhd",
    ".vhdl",
}
VCS_COMPILER_DRIVERS = {"vlogan", "vhdlan"}
CONTEXT_SUFFIXES = {
    ".sh",
    ".tcl",
    ".do",
    ".f",
    ".prj",
    ".setup",
    ".cfg",
    ".txt",
}


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _contract_sha256(report: dict[str, Any]) -> str:
    return canonical_sha256(
        {
            key: value
            for key, value in report.items()
            if key not in {"contract_sha256", "cache_reused"}
        }
    )


def _is_forbidden_legacy_path(value: Any) -> bool:
    text = str(value or "")
    if not text:
        return False
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    try:
        path.resolve(strict=False).relative_to(FORBIDDEN_LEGACY_ROOT)
    except ValueError:
        return False
    return True


def _path_guard(values: list[Any], label: str, blockers: list[str]) -> None:
    for value in values:
        if _is_forbidden_legacy_path(value):
            blockers.append(f"{label} references forbidden legacy fixture input: {value}")


def _tool_profile_vivado(run_dir: Path) -> tuple[dict[str, Any], list[str]]:
    path = run_dir / "input" / "tool_profile.json"
    profile = _read_json_if_exists(path)
    tools = [
        row
        for row in profile.get("tools", [])
        if isinstance(row, dict)
        and row.get("role") == "synthesis_implementation_bitstream_generation"
    ]
    blockers: list[str] = []
    if len(tools) != 1:
        blockers.append("tool_profile must declare exactly one Vivado tool endpoint")
        return {}, blockers
    tool = tools[0]
    for field in ("executable",):
        if not str(tool.get(field) or ""):
            blockers.append(f"Vivado tool profile is missing {field}")
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path) if path.is_file() else None,
        "host": str(tool.get("host") or ""),
        "port": int(tool.get("port") or 22),
        "executable": str(tool.get("executable") or ""),
        "role": str(tool.get("role") or ""),
        "name": str(tool.get("name") or ""),
    }, blockers


def _object_indexes(
    facts: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str, str], dict[str, Any]]]:
    by_id: dict[str, dict[str, Any]] = {}
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in facts.get("objects", []):
        if not isinstance(row, dict):
            continue
        object_id = str(row.get("object_id") or "")
        key = (
            str(row.get("bd_path") or ""),
            str(row.get("kind") or ""),
            str(row.get("path") or ""),
        )
        if object_id:
            by_id[object_id] = row
        by_key[key] = row
    return by_id, by_key


def _cell_for_owner_path(
    row: dict[str, Any],
    by_key: dict[tuple[str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    return by_key.get(
        (
            str(row.get("bd_path") or ""),
            "cell",
            str(row.get("owner_path") or ""),
        ),
        {},
    )


def _external_interfaces_by_cell(
    facts: dict[str, Any],
    by_key: dict[tuple[str, str, str], dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for port in facts.get("objects", []):
        if not isinstance(port, dict) or port.get("kind") != "interface_port":
            continue
        bd_path = str(port.get("bd_path") or "")
        for net_ref in port.get("connected_nets", []):
            if not isinstance(net_ref, dict) or net_ref.get("kind") != "interface_net":
                continue
            net = by_key.get((bd_path, "interface_net", str(net_ref.get("path") or "")), {})
            for member in net.get("members", []):
                if not isinstance(member, dict) or member.get("kind") != "interface_pin":
                    continue
                pin = by_key.get((bd_path, "interface_pin", str(member.get("path") or "")), {})
                cell = _cell_for_owner_path(pin, by_key)
                cell_id = str(cell.get("object_id") or "")
                if not cell_id:
                    continue
                member_rows = [
                    by_key.get((bd_path, "pin", str(value.get("path") or "")), {})
                    for value in pin.get("members", [])
                    if isinstance(value, dict) and value.get("kind") == "pin"
                ]
                result.setdefault(cell_id, []).append(
                    {
                        "interface_port": copy.deepcopy(port),
                        "interface_net": copy.deepcopy(net),
                        "provider_interface_pin": copy.deepcopy(pin),
                        "provider_member_pins": [
                            copy.deepcopy(value) for value in member_rows if value
                        ],
                    }
                )
    return result


def _configuration_projection(cell: dict[str, Any]) -> dict[str, Any]:
    properties = cell.get("properties", {}) if isinstance(cell.get("properties"), dict) else {}
    return {
        "vlnv": str(properties.get("VLNV") or ""),
        "configuration": {
            key: value
            for key, value in sorted(properties.items())
            if str(key).startswith("CONFIG.") and key != "CONFIG.Component_Name"
        },
    }


def _configured_ip_path(
    cell: dict[str, Any], source_rows: list[dict[str, Any]]
) -> tuple[str, list[str]]:
    properties = cell.get("properties", {}) if isinstance(cell.get("properties"), dict) else {}
    component = str(properties.get("CONFIG.Component_Name") or "")
    cell_id = str(cell.get("object_id") or "")
    candidates = {
        str(row.get("parent_composite_file") or "")
        for row in source_rows
        if cell_id in row.get("owner_cell_ids", [])
        and str(row.get("parent_composite_file") or "")
        and Path(str(row.get("parent_composite_file") or "")).stem == component
    }
    if not component:
        return "", [f"provider cell {cell_id} has no CONFIG.Component_Name"]
    if len(candidates) != 1:
        return "", [
            f"provider cell {cell_id} does not resolve to exactly one configured IP composite: {sorted(candidates)}"
        ]
    return next(iter(candidates)), []


def _verified_remote_digest(
    host: str, port: int, path: str, timeout: int
) -> tuple[str, int]:
    raw = source_bytes(host, path, timeout, port)
    return sha256_bytes(raw), len(raw)


def derive_external_fixture_authority(
    run_dir: Path, timeout: int = 0
) -> tuple[dict[str, Any], list[str]]:
    """Derive configured external-provider authority without semantic name tests."""

    run_dir = run_dir.resolve()
    identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
    facts_path = run_dir / "verification" / "board_interface" / "vivado_board_facts.json"
    target_profile_path = run_dir / "input" / "target_board_profile.json"
    identity = _read_json_if_exists(identity_path)
    facts = _read_json_if_exists(facts_path)
    target_profile = _read_json_if_exists(target_profile_path)
    tool, tool_blockers = _tool_profile_vivado(run_dir)
    blockers = list(tool_blockers)
    _path_guard([identity_path, facts_path, target_profile_path], "authority input", blockers)
    if identity.get("status") != "pass":
        blockers.append("exact board identity is not pass")
    if facts.get("status") != "pass":
        blockers.append("Vivado board facts are not pass")
    if not identity_path.is_file() or not facts_path.is_file():
        blockers.append("exact board identity or Vivado fact bundle is missing")
    if not target_profile_path.is_file():
        blockers.append("target board profile is missing")
    actual_facts_hash = sha256_file(facts_path) if facts_path.is_file() else ""
    if identity.get("vivado_facts_sha256") != actual_facts_hash:
        blockers.append("exact board identity does not bind the current Vivado fact bundle")
    project = facts.get("project", {}) if isinstance(facts.get("project"), dict) else {}
    project_path = str(project.get("path") or "")
    part = str(project.get("part") or "")
    if not project_path or project_path != str(identity.get("sample_project") or ""):
        blockers.append("Vivado facts and exact identity do not bind one sample project")
    if not part:
        blockers.append("Vivado facts do not declare the exact project part")
    profile_part = str(
        target_profile.get("board", {}).get("fpga_part")
        if isinstance(target_profile.get("board"), dict)
        else ""
    )
    required_part = str(
        target_profile.get("board_pass_criteria", {}).get("required_fpga_part")
        if isinstance(target_profile.get("board_pass_criteria"), dict)
        else ""
    )
    for label, value in (("target profile", profile_part), ("board pass criteria", required_part)):
        if value and part and value != part:
            blockers.append(f"{label} part does not match the Vivado project part")
    if project_path and not blockers:
        try:
            project_hash, project_size = _verified_remote_digest(
                tool.get("host", ""), int(tool.get("port") or 22), project_path, timeout
            )
        except Exception as exc:
            blockers.append(f"cannot hash the exact sample project: {exc}")
            project_hash, project_size = "", 0
        else:
            if identity.get("sample_project_sha256") != project_hash:
                blockers.append("sample project changed after exact board discovery")
    else:
        project_hash, project_size = "", 0

    by_id, by_key = _object_indexes(facts)
    external_by_cell = _external_interfaces_by_cell(facts, by_key)
    source_rows = [
        row for row in facts.get("simulation", {}).get("source_files", []) if isinstance(row, dict)
    ]
    source_by_id = {str(row.get("source_id") or ""): row for row in source_rows}
    timing = identity.get("timing_contract", {}) if isinstance(identity.get("timing_contract"), dict) else {}
    memory = timing.get("memory_timing_model", {}) if isinstance(timing.get("memory_timing_model"), dict) else {}
    memory_source_ids = {str(value) for value in memory.get("source_ids", []) if str(value)}
    unknown_sources = sorted(memory_source_ids - set(source_by_id))
    if not memory_source_ids or unknown_sources:
        blockers.append(f"memory timing source authority is missing or unknown: {unknown_sources}")
    owner_cells = {
        str(owner)
        for source_id in memory_source_ids
        for owner in source_by_id.get(source_id, {}).get("owner_cell_ids", [])
        if str(owner)
    }
    candidates = owner_cells.intersection(external_by_cell)
    calibration_owner_cells: set[str] = set()
    for row in timing.get("calibration", []):
        if not isinstance(row, dict):
            continue
        driver = by_id.get(str(row.get("driver_object_id") or ""), {})
        cell = _cell_for_owner_path(driver, by_key) if driver else {}
        if cell.get("object_id"):
            calibration_owner_cells.add(str(cell["object_id"]))
    if calibration_owner_cells:
        calibrated = candidates.intersection(calibration_owner_cells)
        if calibrated:
            candidates = calibrated
    if not candidates:
        blockers.append(
            "selected timing sources do not structurally resolve to an external-interface provider cell"
        )

    cells = {
        str(row.get("object_id") or ""): row
        for row in facts.get("objects", [])
        if isinstance(row, dict) and row.get("kind") == "cell" and row.get("object_id")
    }
    primary_configuration_hashes = {
        canonical_sha256(_configuration_projection(cells[cell_id]))
        for cell_id in candidates
        if cell_id in cells
    }
    expanded_cells = {
        cell_id
        for cell_id, cell in cells.items()
        if cell_id in external_by_cell
        and canonical_sha256(_configuration_projection(cell)) in primary_configuration_hashes
    }
    groups: dict[str, dict[str, Any]] = {}
    for cell_id in sorted(expanded_cells):
        cell = cells[cell_id]
        projection = _configuration_projection(cell)
        configuration_sha = canonical_sha256(projection)
        component = str(cell.get("properties", {}).get("CONFIG.Component_Name") or "")
        xci_path, path_errors = _configured_ip_path(cell, source_rows)
        blockers.extend(path_errors)
        _path_guard([xci_path], "configured IP authority", blockers)
        xci_sha = ""
        xci_size = 0
        if xci_path and not _is_forbidden_legacy_path(xci_path):
            try:
                xci_sha, xci_size = _verified_remote_digest(
                    tool.get("host", ""), int(tool.get("port") or 22), xci_path, timeout
                )
            except Exception as exc:
                blockers.append(f"cannot hash configured IP {xci_path}: {exc}")
        instance = {
            "cell_id": cell_id,
            "bd_path": cell.get("bd_path"),
            "cell_path": cell.get("path"),
            "component_name": component,
            "configured_ip": {
                "remote_path": xci_path,
                "sha256": xci_sha,
                "size_bytes": xci_size,
            },
            "external_interfaces": external_by_cell.get(cell_id, []),
            "selected_by_runtime_timing_authority": cell_id in candidates,
        }
        group = groups.setdefault(
            configuration_sha,
            {
                "configuration_sha256": configuration_sha,
                "configuration": projection,
                "instances": [],
            },
        )
        group["instances"].append(instance)
    for group in groups.values():
        group["instances"] = sorted(group["instances"], key=lambda row: row["cell_id"])
        representatives = [
            row for row in group["instances"] if row["selected_by_runtime_timing_authority"]
        ] or group["instances"]
        group["representative"] = copy.deepcopy(representatives[0])
    if not groups:
        blockers.append("no configured external simulation provider group was derived")

    identity_vivado_tool = identity.get("vivado_tool", {}) if isinstance(identity.get("vivado_tool"), dict) else {}
    for field in ("host", "port", "executable"):
        expected = tool.get(field)
        actual = identity_vivado_tool.get(field)
        if field == "port":
            expected, actual = int(expected or 22), int(actual or 22)
        if actual != expected:
            blockers.append(f"exact identity Vivado tool differs from tool_profile: {field}")
    include_feedback_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "reports"
        / "vcs_compile.log"
    )
    include_feedback_edges = _vcs_missing_include_edges(include_feedback_path)
    previous_fixture = _read_json_if_exists(
        run_dir
        / "verification"
        / "board_interface"
        / "external_simulation_fixture.json"
    )
    previous_authority = (
        previous_fixture.get("authority", {})
        if isinstance(previous_fixture.get("authority"), dict)
        else {}
    )
    previous_feedback = (
        previous_authority.get("literal_include_feedback", {})
        if isinstance(previous_authority.get("literal_include_feedback"), dict)
        else {}
    )
    for row in previous_feedback.get("edges", []):
        if isinstance(row, dict) and row not in include_feedback_edges:
            include_feedback_edges.append(copy.deepcopy(row))
    authority = {
        "schema_version": AUTHORITY_SCHEMA_VERSION,
        "run_dir": str(run_dir),
        "identity": {
            "path": str(identity_path),
            "sha256": sha256_file(identity_path) if identity_path.is_file() else None,
        },
        "vivado_facts": {"path": str(facts_path), "sha256": actual_facts_hash or None},
        "target_board_profile": {
            "path": str(target_profile_path),
            "sha256": sha256_file(target_profile_path) if target_profile_path.is_file() else None,
        },
        "sample_project": {
            "remote_path": project_path,
            "sha256": project_hash or None,
            "size_bytes": project_size,
            "part": part,
            "vivado_version": project.get("vivado_version"),
        },
        "vivado_tool": tool,
        "memory_timing_source_ids": sorted(memory_source_ids),
        "provider_groups": [groups[key] for key in sorted(groups)],
        "literal_include_feedback": {
            "source": "real_vcs_sfc_or_missing_include_diagnostic",
            "path": str(include_feedback_path),
            "edges": include_feedback_edges,
            "projection_sha256": canonical_sha256(include_feedback_edges),
        },
        "implementation": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__).resolve()),
            "vivado_tcl_sha256": sha256_bytes(VIVADO_EXTERNAL_FIXTURE_TCL.encode("utf-8")),
        },
        "policy": {
            "provider_selected_from_source_owner_and_interface_graph": True,
            "provider_names_or_model_names_not_used_for_selection": True,
            "vivado_official_example_and_export_simulation_are_authoritative": True,
            "legacy_fixture_inputs_forbidden": str(FORBIDDEN_LEGACY_ROOT),
            "user_project_opened_read_only": True,
        },
    }
    authority["authority_sha256"] = canonical_sha256(authority)
    return authority, blockers


VIVADO_EXTERNAL_FIXTURE_TCL = r'''# SpatialAccAgent configured-IP external fixture exporter.
proc hexfield {value} {
  binary scan [encoding convertto utf-8 $value] H* encoded
  return $encoded
}
proc emit {fh tag args} {
  set line $tag
  foreach value $args { append line "\t[hexfield $value]" }
  puts $fh $line
}
proc safe_prop {object property} {
  if {[catch {set properties [list_property $object]}]} { return "" }
  if {[lsearch -exact $properties $property] < 0} { return "" }
  if {[catch {set value [get_property $property $object]}]} { return "" }
  return $value
}
proc walk_files {root} {
  set result {}
  foreach path [glob -nocomplain -directory $root *] {
    if {[file isdirectory $path]} {
      set result [concat $result [walk_files $path]]
    } else {
      lappend result $path
    }
  }
  return $result
}
if {$argc < 5 || (($argc - 3) % 2) != 0} {
  error "usage: external_fixture.tcl project.xpr manifest.tsv output_root group component ..."
}
set project_path [lindex $argv 0]
set manifest_path [lindex $argv 1]
set output_root [lindex $argv 2]
set fh [open $manifest_path w]
emit $fh META schema spatialaccagent.vivado_external_fixture_stream.v1
emit $fh META vivado_version [version -short]
emit $fh META source_project $project_path

for {set arg_index 3} {$arg_index < $argc} {incr arg_index 2} {
  set group [lindex $argv $arg_index]
  set component [lindex $argv [expr {$arg_index + 1}]]
  set open_error ""
  if {[catch {open_project -read_only $project_path} open_error]} {
    emit $fh PROVIDER $group $component fail $open_error
    continue
  }
  set source_part [safe_prop [current_project] PART]
  set ips [get_ips -all -quiet $component]
  if {[llength $ips] != 1} {
    emit $fh PROVIDER $group $component fail "configured IP count is [llength $ips]"
    close_project
    continue
  }
  set ip [lindex $ips 0]
  emit $fh PROVIDER $group $component pass ""
  emit $fh PROVIDER_PART $group $source_part
  foreach property [lsort [list_property $ip]] {
    if {[catch {set value [get_property $property $ip]}]} { continue }
    emit $fh IP_PROPERTY $group $property $value
  }
  set ip_file [safe_prop $ip IP_FILE]
  if {$ip_file eq ""} { set ip_file [safe_prop $ip IP_OUTPUT_DIR] }
  emit $fh IP_FILE $group $ip_file
  close_project

  # Import the exact configured XCI into scratch storage. Some read-only user
  # projects cannot host the temporary .Xil directory used by example export.
  set scratch_dir [file join $output_root "source_${group}"]
  set scratch_name "external_fixture_[string range $group 0 15]"
  set imported_name "provider_[string range $group 0 15]"
  set import_error ""
  if {[catch {
    create_project -force $scratch_name $scratch_dir -part $source_part
    import_ip -srcset sources_1 -name $imported_name $ip_file
    set imported_ips [get_ips -all -quiet $imported_name]
    if {[llength $imported_ips] != 1} {
      error "imported configured IP count is [llength $imported_ips]"
    }
    set ip [lindex $imported_ips 0]
  } import_error]} {
    emit $fh EXAMPLE $group fail "" "" $import_error
    catch {close_project}
    continue
  }
  set example_dir [file join $output_root "example_${group}"]
  set example_error ""
  if {[catch {open_example_project -in_process -force -dir $example_dir $ip} example_error]} {
    emit $fh EXAMPLE $group fail "" "" $example_error
    catch {close_project}
    continue
  }
  set example_project [current_project]
  set example_part [safe_prop $example_project PART]
  emit $fh EXAMPLE $group pass $example_project $example_part ""
  set simsets [get_filesets -quiet -filter {FILESET_TYPE == SimulationSrcs}]
  emit $fh FILESET_COUNT $group [llength $simsets]
  set fileset_index 0
  foreach simset $simsets {
    set top [safe_prop $simset TOP]
    set top_lib [safe_prop $simset TOP_LIB]
    set source_set [safe_prop $simset SOURCE_SET]
    set compile_error ""
    if {[catch {update_compile_order -fileset $simset} compile_error]} {
      emit $fh FILESET $group $fileset_index $simset fail $top $top_lib $source_set $compile_error
      incr fileset_index
      continue
    }
    emit $fh FILESET $group $fileset_index $simset pass $top $top_lib $source_set ""
    set sources [get_files -compile_order sources -used_in simulation -of_objects $simset]
    set order 0
    foreach source $sources {
      emit $fh SOURCE $group $fileset_index $order $source
      foreach property [lsort [list_property $source]] {
        if {[catch {set value [get_property $property $source]}]} { continue }
        emit $fh SOURCE_PROPERTY $group $fileset_index $order $property $value
      }
      incr order
    }
    set missing_path [file join $output_root "missing_${group}_${fileset_index}.txt"]
    if {[catch {report_compile_order -missing_instances -used_in simulation -of_objects $simset -file $missing_path} missing_error]} {
      emit $fh MISSING_STATUS $group $fileset_index fail $missing_error
    } else {
      set missing_fh [open $missing_path r]
      set missing_text [read $missing_fh]
      close $missing_fh
      emit $fh MISSING_STATUS $group $fileset_index pass ""
      emit $fh MISSING_REPORT $group $fileset_index $missing_text
    }
    set export_dir [file join $output_root "export_${group}_${fileset_index}"]
    if {[catch {export_simulation -simulator vcs -of_objects $simset -directory $export_dir -absolute_path -force} export_error]} {
      emit $fh EXPORT_STATUS $group $fileset_index fail $export_error
    } else {
      emit $fh EXPORT_STATUS $group $fileset_index pass ""
      foreach path [lsort [walk_files $export_dir]] {
        emit $fh EXPORT_FILE $group $fileset_index $path [file size $path]
      }
    }
    incr fileset_index
  }
  catch {close_project}
}
emit $fh META export_status pass
close $fh
exit 0
'''


def parse_external_fixture_stream(raw: bytes) -> dict[str, Any]:
    metadata: dict[str, str] = {}
    providers: dict[str, dict[str, Any]] = {}
    for number, raw_line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        fields = raw_line.split("\t")
        tag = fields[0]
        values = [_decode_fact_field(value) for value in fields[1:]]
        try:
            if tag == "META":
                metadata[values[0]] = values[1]
                continue
            group = values[0]
            provider = providers.setdefault(
                group,
                {"group_id": group, "ip_properties": {}, "filesets": {}},
            )
            if tag == "PROVIDER":
                provider.update(
                    {"component_name": values[1], "status": values[2], "diagnostic": values[3]}
                )
            elif tag == "PROVIDER_PART":
                provider["source_part"] = values[1]
            elif tag == "IP_PROPERTY":
                provider["ip_properties"][values[1]] = values[2]
            elif tag == "IP_FILE":
                provider["ip_file"] = values[1]
            elif tag == "EXAMPLE":
                provider["example"] = {
                    "status": values[1],
                    "project": values[2],
                    "part": values[3],
                    "diagnostic": values[4],
                }
            elif tag == "FILESET_COUNT":
                provider["fileset_count"] = int(values[1])
            elif tag in {
                "FILESET",
                "SOURCE",
                "SOURCE_PROPERTY",
                "MISSING_STATUS",
                "MISSING_REPORT",
                "EXPORT_STATUS",
                "EXPORT_FILE",
            }:
                fileset_index = int(values[1])
                fileset = provider["filesets"].setdefault(
                    fileset_index,
                    {
                        "index": fileset_index,
                        "sources": {},
                        "export_files": [],
                    },
                )
                if tag == "FILESET":
                    fileset.update(
                        {
                            "name": values[2],
                            "status": values[3],
                            "top": values[4],
                            "top_lib": values[5],
                            "source_set": values[6],
                            "diagnostic": values[7],
                        }
                    )
                elif tag == "SOURCE":
                    order = int(values[2])
                    fileset["sources"][order] = {
                        "compile_order": order,
                        "remote_path": values[3],
                        "properties": {},
                    }
                elif tag == "SOURCE_PROPERTY":
                    fileset["sources"][int(values[2])]["properties"][values[3]] = values[4]
                elif tag == "MISSING_STATUS":
                    fileset["missing_status"] = values[2]
                    fileset["missing_diagnostic"] = values[3]
                elif tag == "MISSING_REPORT":
                    fileset["missing_report"] = values[2]
                elif tag == "EXPORT_STATUS":
                    fileset["export_status"] = values[2]
                    fileset["export_diagnostic"] = values[3]
                elif tag == "EXPORT_FILE":
                    fileset["export_files"].append(
                        {"remote_path": values[2], "size_bytes": int(values[3])}
                    )
            else:
                raise ValueError(f"unknown external fixture record {tag}")
        except (IndexError, KeyError, ValueError) as exc:
            raise ValueError(f"malformed external fixture record at line {number}: {tag}") from exc
    if metadata.get("schema") != "spatialaccagent.vivado_external_fixture_stream.v1":
        raise ValueError("external fixture stream schema is missing or unsupported")
    normalized_providers: list[dict[str, Any]] = []
    for group in sorted(providers):
        provider = providers[group]
        filesets = []
        for index in sorted(provider["filesets"]):
            fileset = provider["filesets"][index]
            fileset["sources"] = [
                fileset["sources"][order] for order in sorted(fileset["sources"])
            ]
            fileset["export_files"] = sorted(
                fileset["export_files"], key=lambda row: row["remote_path"]
            )
            filesets.append(fileset)
        provider["filesets"] = filesets
        normalized_providers.append(provider)
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "metadata": metadata,
        "providers": normalized_providers,
    }


def _validate_raw_export(
    raw_export: dict[str, Any], authority: dict[str, Any]
) -> list[str]:
    blockers: list[str] = []
    expected = {
        str(row.get("configuration_sha256") or ""): row
        for row in authority.get("provider_groups", [])
        if isinstance(row, dict)
    }
    observed = {
        str(row.get("group_id") or ""): row
        for row in raw_export.get("providers", [])
        if isinstance(row, dict)
    }
    if set(observed) != set(expected):
        blockers.append("Vivado external fixture export does not cover every provider configuration exactly once")
    expected_part = str(authority.get("sample_project", {}).get("part") or "")
    expected_version = str(authority.get("sample_project", {}).get("vivado_version") or "")
    if expected_version and raw_export.get("metadata", {}).get("vivado_version") != expected_version:
        blockers.append("external fixture export Vivado version differs from the sample-project facts")
    for group_id, expected_group in expected.items():
        row = observed.get(group_id, {})
        representative = expected_group.get("representative", {})
        if row.get("status") != "pass":
            blockers.append(f"Vivado configured-IP lookup failed for provider group {group_id}")
        if row.get("component_name") != representative.get("component_name"):
            blockers.append(f"Vivado export returned a different configured IP for provider group {group_id}")
        if row.get("ip_file") != representative.get("configured_ip", {}).get("remote_path"):
            blockers.append(f"Vivado export returned a different configured IP file for provider group {group_id}")
        if row.get("source_part") != expected_part or row.get("example", {}).get("part") != expected_part:
            blockers.append(f"Vivado example project part differs for provider group {group_id}")
        if row.get("example", {}).get("status") != "pass":
            blockers.append(f"Vivado example project generation failed for provider group {group_id}")
        if int(row.get("fileset_count") or 0) <= 0 or not row.get("filesets"):
            blockers.append(f"Vivado example project has no simulation fileset for provider group {group_id}")
        for fileset in row.get("filesets", []):
            label = f"provider {group_id} fileset {fileset.get('index')}"
            if fileset.get("status") != "pass" or not fileset.get("top"):
                blockers.append(f"{label} has no valid simulation top/compile order")
            if not fileset.get("sources"):
                blockers.append(f"{label} has an empty simulation compile source set")
            if fileset.get("missing_status") != "pass":
                blockers.append(f"{label} missing-instance report failed")
            unresolved, parse_errors = _parse_missing_instances(
                str(fileset.get("missing_report") or "")
            )
            blockers.extend(f"{label}: {value}" for value in parse_errors)
            fileset["compile_order_missing_instance_diagnostics"] = unresolved
            if fileset.get("export_status") != "pass" or not fileset.get("export_files"):
                blockers.append(f"{label} has no successful VCS export_simulation artifact set")
            paths = [
                str(source.get("remote_path") or "") for source in fileset.get("sources", [])
            ] + [
                str(value.get("remote_path") or "") for value in fileset.get("export_files", [])
            ]
            if any(not path for path in paths):
                blockers.append(f"{label} contains an artifact without an absolute source path")
            _path_guard(paths, label, blockers)
    return blockers


def _normalized_remote_path(path: str) -> str:
    return posixpath.normpath(str(PurePosixPath(path))) if path else ""


def _is_hdl_path(path: str, file_type: str = "") -> bool:
    lowered_type = str(file_type or "").strip().lower()
    if any(value in lowered_type for value in ("verilog", "vhdl")):
        return True
    return PurePosixPath(path).suffix.lower() in HDL_SUFFIXES


def _shell_logical_lines(text: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    pieces: list[str] = []
    start = 0
    for number, physical in enumerate(text.splitlines(), 1):
        stripped = physical.rstrip()
        if not pieces:
            start = number
        if stripped.endswith("\\"):
            pieces.append(stripped[:-1])
            continue
        pieces.append(physical)
        result.append((start, " ".join(pieces)))
        pieces = []
    if pieces:
        result.append((start, " ".join(pieces)))
    return result


_SHELL_VARIABLE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")


def _expand_shell_variables(value: str, variables: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2) or ""
        return variables.get(name, match.group(0))

    expanded = value
    for _ in range(8):
        updated = _SHELL_VARIABLE.sub(replace, expanded)
        if updated == expanded:
            break
        expanded = updated
    return expanded


def _resolve_script_input(script_path: str, value: str) -> str:
    value = value.strip()
    if not value or "$" in value or "`" in value or "$(" in value:
        return ""
    if posixpath.isabs(value):
        return _normalized_remote_path(value)
    return _normalized_remote_path(posixpath.join(posixpath.dirname(script_path), value))


def _compiler_driver(token: str) -> str:
    name = PurePosixPath(token.strip("'\"")).name.lower()
    return name if name in VCS_COMPILER_DRIVERS else ""


def _parse_vcs_compile_invocations(
    raw_export: dict[str, Any], payloads: dict[str, bytes]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse the actual HDL inputs passed by Vivado's exported VCS scripts."""

    invocations: list[dict[str, Any]] = []
    blockers: list[str] = []
    for provider in raw_export.get("providers", []):
        for fileset in provider.get("filesets", []):
            for artifact in fileset.get("export_files", []):
                script_path = str(artifact.get("remote_path") or "")
                raw = payloads.get(script_path)
                if raw is None or PurePosixPath(script_path).suffix.lower() not in CONTEXT_SUFFIXES:
                    continue
                text = raw.decode("utf-8", errors="replace")
                variables: dict[str, str] = {
                    "PWD": posixpath.dirname(script_path),
                }
                for line_number, logical_line in _shell_logical_lines(text):
                    stripped = logical_line.strip()
                    assignment = re.fullmatch(
                        r"(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)", stripped
                    )
                    if assignment and not assignment.group(2).lstrip().startswith("("):
                        try:
                            values = shlex.split(
                                _expand_shell_variables(assignment.group(2), variables),
                                comments=True,
                                posix=True,
                            )
                        except ValueError:
                            continue
                        if len(values) == 1:
                            variables[assignment.group(1)] = values[0]
                        continue
                    expanded = _expand_shell_variables(logical_line, variables)
                    try:
                        tokens = shlex.split(expanded, comments=True, posix=True)
                    except ValueError as exc:
                        if re.search(
                            r"(?:^|\s)(?:[^\s]+/)?(?:vlogan|vhdlan)(?=\s)", expanded
                        ):
                            blockers.append(
                                f"cannot parse VCS export command {script_path}:{line_number}: {exc}"
                            )
                        continue
                    driver_index = next(
                        (index for index, token in enumerate(tokens) if _compiler_driver(token)),
                        None,
                    )
                    if driver_index is None:
                        continue
                    tokens = tokens[driver_index:]
                    pipeline_index = next(
                        (index for index, token in enumerate(tokens) if token in {"|", "||", "&&", ";"}),
                        len(tokens),
                    )
                    tokens = tokens[:pipeline_index]
                    driver = _compiler_driver(tokens[0])
                    work_library = ""
                    include_directories: list[str] = []
                    inputs: list[str] = []
                    index = 1
                    while index < len(tokens):
                        token = tokens[index]
                        if token == "-work" and index + 1 < len(tokens):
                            work_library = tokens[index + 1]
                            index += 2
                            continue
                        if token.startswith("+incdir+"):
                            for value in token[len("+incdir+") :].split("+"):
                                resolved = _resolve_script_input(script_path, value)
                                if resolved:
                                    include_directories.append(resolved)
                            index += 1
                            continue
                        if token in {"-f", "-F"} and index + 1 < len(tokens):
                            blockers.append(
                                f"VCS export command {script_path}:{line_number} uses an indirect file list; "
                                "the official HDL input closure is not explicit"
                            )
                            index += 2
                            continue
                        if not token.startswith(("-", "+")) and _is_hdl_path(token):
                            resolved = _resolve_script_input(script_path, token)
                            if resolved:
                                inputs.append(resolved)
                        index += 1
                    if not inputs:
                        blockers.append(
                            f"VCS compiler invocation has no explicit HDL input: {script_path}:{line_number}"
                        )
                        continue
                    invocation_id = "external-fixture-invocation:" + canonical_sha256(
                        [script_path, line_number, driver, work_library, inputs]
                    )[:24]
                    invocations.append(
                        {
                            "invocation_id": invocation_id,
                            "script_remote_path": script_path,
                            "line_number": line_number,
                            "driver": driver,
                            "work_library": work_library,
                            "input_remote_paths": list(dict.fromkeys(inputs)),
                            "include_directories": list(dict.fromkeys(include_directories)),
                            "argv": tokens,
                            "provider_configuration_sha256": provider.get("group_id"),
                            "fileset_index": fileset.get("index"),
                        }
                    )
    if not invocations:
        blockers.append("Vivado VCS export contains no parseable HDL compiler invocation")
    return invocations, blockers


def _executable_ancestors(executable: str) -> list[str]:
    current = PurePosixPath(executable).parent
    result: list[str] = []
    while str(current) not in {"", ".", "/"} and len(result) < 8:
        result.append(str(current))
        current = current.parent
    return result


def _setup_candidates(
    host: str, port: int, ancestor: str, timeout: int, max_depth: int = 8
) -> list[str]:
    if host:
        try:
            raw = remote_exec(
                host,
                port,
                [
                    "find",
                    ancestor,
                    "-maxdepth",
                    str(max_depth),
                    "-type",
                    "f",
                    "-name",
                    "synopsys_sim.setup",
                    "-print",
                ],
                timeout,
            )
        except Exception:
            return []
        return sorted(
            {
                _normalized_remote_path(value)
                for value in raw.decode("utf-8", errors="replace").splitlines()
                if value.strip()
            }
        )
    root = Path(ancestor)
    if not root.is_dir():
        return []
    result: list[str] = []
    for current, directories, files in os.walk(root):
        relative_depth = len(Path(current).relative_to(root).parts)
        if relative_depth >= max_depth:
            directories[:] = []
        if "synopsys_sim.setup" in files:
            result.append(str((Path(current) / "synopsys_sim.setup").resolve()))
    return sorted(set(result))


def _parse_synopsys_setup(
    setup_path: str,
    host: str,
    port: int,
    timeout: int,
) -> tuple[list[dict[str, str]], list[dict[str, Any]], dict[str, bytes], list[str]]:
    mappings: list[dict[str, str]] = []
    files: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    blockers: list[str] = []
    pending = [_normalized_remote_path(setup_path)]
    visited: set[str] = set()
    while pending and len(visited) < 32:
        path = pending.pop(0)
        if path in visited:
            continue
        visited.add(path)
        try:
            raw = source_bytes(host, path, timeout, port)
        except Exception as exc:
            blockers.append(f"cannot read synopsys setup dependency {path}: {exc}")
            continue
        payloads[path] = raw
        files.append(
            {
                "remote_path": path,
                "sha256": sha256_bytes(raw),
                "size_bytes": len(raw),
            }
        )
        variables = {"PWD": posixpath.dirname(path)}
        for line_number, original in enumerate(
            raw.decode("utf-8", errors="replace").splitlines(), 1
        ):
            line = original.split("#", 1)[0].strip()
            if not line:
                continue
            include = re.fullmatch(r"OTHERS\s*=\s*(.+)", line, re.IGNORECASE)
            if include:
                value = _expand_shell_variables(include.group(1).strip().strip("'\""), variables)
                resolved = _resolve_script_input(path, value)
                if not resolved:
                    blockers.append(f"unresolved OTHERS mapping in {path}:{line_number}")
                else:
                    pending.append(resolved)
                continue
            mapping = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_$.-]*)\s*:\s*(.+)", line)
            if mapping:
                value = _expand_shell_variables(mapping.group(2).strip().strip("'\""), variables)
                resolved = _resolve_script_input(path, value)
                mappings.append(
                    {
                        "library": mapping.group(1),
                        "configured_path": mapping.group(2).strip(),
                        "resolved_directory": resolved,
                        "setup_remote_path": path,
                    }
                )
                continue
            assignment = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)", line)
            if assignment:
                variables[assignment.group(1)] = _expand_shell_variables(
                    assignment.group(2).strip().strip("'\""), variables
                )
    if pending:
        blockers.append("synopsys setup include graph exceeds the bounded closure")
    return mappings, files, payloads, blockers


def _directory_exists(host: str, port: int, path: str, timeout: int) -> bool:
    if not path:
        return False
    if not host:
        return Path(path).is_dir()
    try:
        remote_exec(host, port, ["test", "-d", path], timeout)
    except Exception:
        return False
    return True


def _resolved_vivado_tool(
    authority: dict[str, Any], timeout: int
) -> dict[str, Any]:
    tool = authority.get("vivado_tool", {})
    host = str(tool.get("host") or "")
    port = int(tool.get("port") or 22)
    configured_executable = str(tool.get("executable") or "")
    resolved_executable = configured_executable
    if host:
        try:
            resolved = remote_exec(
                host, port, ["readlink", "-f", configured_executable], timeout
            ).decode("utf-8", errors="replace").strip()
            resolved_executable = resolved or configured_executable
        except Exception:
            pass
    elif Path(configured_executable).exists():
        resolved_executable = str(Path(configured_executable).resolve())
    return {
        "host": host,
        "port": port,
        "configured_executable": configured_executable,
        "resolved_executable": _normalized_remote_path(resolved_executable),
    }


def _discover_synopsys_setup(
    authority: dict[str, Any],
    invocations: list[dict[str, Any]],
    timeout: int,
    resolved_tool: dict[str, Any] | None = None,
    excluded_roots: tuple[str, ...] = (),
) -> tuple[dict[str, Any], dict[str, bytes], list[str]]:
    resolved_tool = resolved_tool or _resolved_vivado_tool(authority, timeout)
    host = str(resolved_tool.get("host") or "")
    port = int(resolved_tool.get("port") or 22)
    executable = str(resolved_tool.get("resolved_executable") or "")
    compile_work_libraries = sorted(
        {
            str(row.get("work_library") or "")
            for row in invocations
            if str(row.get("work_library") or "")
        }
    )
    if not compile_work_libraries:
        return {}, {}, ["VCS compiler invocations declare no required work libraries"]

    work_libraries_by_key: dict[str, str] = {}
    for library in compile_work_libraries:
        key = library.lower()
        previous = work_libraries_by_key.get(key)
        if previous is not None and previous != library:
            return {}, {}, [
                "VCS compiler work libraries differ only by case and are ambiguous: "
                f"{previous}, {library}"
            ]
        work_libraries_by_key[key] = library

    candidate_paths: dict[str, list[str]] = {}
    for ancestor in _executable_ancestors(executable):
        for candidate in _setup_candidates(host, port, ancestor, timeout):
            if not host and any(_is_within(candidate, root) for root in excluded_roots):
                continue
            candidate_paths.setdefault(candidate, []).append(ancestor)

    examined: list[dict[str, Any]] = []
    payloads_by_candidate: dict[str, dict[str, bytes]] = {}
    for candidate, discovery_ancestors in sorted(candidate_paths.items()):
        mappings, files, setup_payloads, parse_blockers = _parse_synopsys_setup(
            candidate, host, port, timeout
        )
        by_library: dict[str, list[dict[str, str]]] = {}
        for mapping in mappings:
            key = mapping["library"].lower()
            if key in work_libraries_by_key:
                by_library.setdefault(key, []).append(mapping)

        required_rows = []
        candidate_blockers = list(parse_blockers)
        covered_libraries: list[str] = []
        for library_key, matches in sorted(by_library.items()):
            covered_libraries.append(work_libraries_by_key[library_key])
            distinct_directories = {
                str(match.get("resolved_directory") or "") for match in matches
            }
            if len(distinct_directories) != 1:
                candidate_blockers.append(
                    f"compile work library {work_libraries_by_key[library_key]} has "
                    f"{len(distinct_directories)} conflicting mappings"
                )
                continue
            directory = next(iter(distinct_directories))
            exists = _directory_exists(host, port, directory, timeout)
            required_rows.append(
                {
                    "library": work_libraries_by_key[library_key],
                    "directory": directory,
                    "exists": exists,
                }
            )
            if not exists:
                candidate_blockers.append(
                    "required compile-library directory does not exist: "
                    f"{work_libraries_by_key[library_key]}={directory}"
                )

        coverage_count = len(covered_libraries)
        descriptor = {
            "remote_path": candidate,
            "search_ancestors": discovery_ancestors,
            "resolved_tool_executable": executable,
            "compile_work_libraries": compile_work_libraries,
            "covered_compile_work_libraries": sorted(covered_libraries),
            "unmapped_compile_work_libraries": sorted(
                set(compile_work_libraries) - set(covered_libraries)
            ),
            "coverage_strength": {
                "covered_library_count": coverage_count,
                "compile_work_library_count": len(compile_work_libraries),
            },
            "required_libraries": sorted(covered_libraries),
            "required_library_directories": required_rows,
            "library_mappings": mappings,
            "files": files,
            "blockers": candidate_blockers,
        }
        examined.append(descriptor)
        payloads_by_candidate[candidate] = setup_payloads

    strongest_coverage = max(
        (
            int(row.get("coverage_strength", {}).get("covered_library_count") or 0)
            for row in examined
        ),
        default=0,
    )
    if strongest_coverage <= 0:
        return {}, {}, [
            "no synopsys_sim.setup candidate covers any VCS compile work library; "
            f"compile_work_libraries={compile_work_libraries}; "
            f"examined={[row.get('remote_path') for row in examined]}"
        ]
    strongest = [
        row
        for row in examined
        if int(row.get("coverage_strength", {}).get("covered_library_count") or 0)
        == strongest_coverage
    ]
    if len(strongest) != 1:
        return {}, {}, [
            "multiple synopsys_sim.setup authorities have equal strongest compile-library "
            f"coverage ({strongest_coverage}/{len(compile_work_libraries)}): "
            f"{[row.get('remote_path') for row in strongest]}"
        ]
    descriptor = strongest[0]
    if descriptor.get("blockers"):
        return {}, {}, [
            "strongest synopsys_sim.setup compile-library authority is unusable: "
            f"{descriptor.get('remote_path')}; blockers={descriptor.get('blockers')}"
        ]
    descriptor = {
        **descriptor,
        "status": "pass",
        "selection_policy": (
            "unique_strongest_nonempty_compile_work_library_coverage"
        ),
    }
    descriptor["setup_authority_sha256"] = canonical_sha256(descriptor)
    return descriptor, payloads_by_candidate[str(descriptor["remote_path"])], []


def _derive_vivado_installation_hdl_authority(
    resolved_tool: dict[str, Any], additional_paths: list[str]
) -> tuple[dict[str, Any], list[str]]:
    executable = str(resolved_tool.get("resolved_executable") or "")
    normalized_paths = sorted(
        {_normalized_remote_path(path) for path in additional_paths if str(path)}
    )
    if not normalized_paths:
        descriptor = {
            "status": "not_required",
            "resolved_tool_executable": executable,
            "selection_policy": (
                "deepest_vivado_executable_ancestor_containing_all_invoked_installation_hdl"
            ),
            "selected_root": "",
            "input_remote_paths": [],
            "files": [],
        }
        descriptor["authority_sha256"] = canonical_sha256(descriptor)
        return descriptor, []

    candidates = [
        ancestor
        for ancestor in _executable_ancestors(executable)
        if all(_is_within(path, ancestor) for path in normalized_paths)
    ]
    if not candidates:
        return {}, [
            "official VCS compiler invocation references additional HDL outside every "
            "resolved Vivado executable ancestor: "
            f"executable={executable}; paths={normalized_paths}"
        ]
    deepest_length = max(len(PurePosixPath(path).parts) for path in candidates)
    deepest = [
        path for path in candidates if len(PurePosixPath(path).parts) == deepest_length
    ]
    if len(deepest) != 1:
        return {}, [
            "multiple equally deep Vivado installation roots contain all invoked additional HDL: "
            f"{deepest}"
        ]
    descriptor = {
        "status": "pass",
        "resolved_tool_executable": executable,
        "selection_policy": (
            "deepest_vivado_executable_ancestor_containing_all_invoked_installation_hdl"
        ),
        "selected_root": deepest[0],
        "candidate_roots": candidates,
        "input_remote_paths": normalized_paths,
        "files": [],
    }
    descriptor["authority_sha256"] = canonical_sha256(descriptor)
    return descriptor, []


def _literal_hdl_includes(raw: bytes) -> list[str]:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//.*?$", " ", text, flags=re.MULTILINE)
    result: list[str] = []
    for match in re.finditer(
        r'(?m)^[ \t]*`include[ \t]+["<]([^">]+)[">]', text
    ):
        value = match.group(1).strip()
        normalized = posixpath.normpath(value)
        if (
            not value
            or posixpath.isabs(value)
            or normalized in {"", ".", ".."}
            or normalized.startswith("../")
            or any(token in value for token in ("\0", "\n", "\r", "\\"))
        ):
            result.append("")
        elif normalized not in result:
            result.append(normalized)
    return result


def _vcs_missing_include_edges(log_path: Path) -> list[dict[str, str]]:
    if not log_path.is_file():
        return []
    text = log_path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(
        r'Source file "([^"]+)" cannot be opened.*?'
        r'"([^"]+)",\s*\d+',
        flags=re.DOTALL,
    )
    edges: list[dict[str, str]] = []
    for match in pattern.finditer(text):
        include_name = posixpath.normpath(match.group(1).strip())
        including_basename = PurePosixPath(match.group(2).strip()).name
        if (
            not include_name
            or not including_basename
            or posixpath.isabs(include_name)
            or include_name in {".", ".."}
            or include_name.startswith("../")
        ):
            continue
        row = {
            "including_basename": including_basename,
            "include_name": include_name,
        }
        if row not in edges:
            edges.append(row)
    return edges


def _remove_recursive_literal_includes(
    raw: bytes, ancestor_basenames: set[str], guard_seed: str
) -> tuple[bytes, list[str]]:
    removed: list[str] = []
    output: list[str] = []
    pattern = re.compile(r'^[ \t]*`include[ \t]+["<]([^">]+)[">].*$')
    text = raw.decode("utf-8", errors="replace")
    for line in text.splitlines(keepends=True):
        match = pattern.match(line.rstrip("\r\n"))
        include_name = posixpath.normpath(match.group(1).strip()) if match else ""
        if match and PurePosixPath(include_name).name in ancestor_basenames:
            removed.append(include_name)
            newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            output.append(newline)
        else:
            output.append(line)
    projected = "".join(output)
    unique_removed = list(dict.fromkeys(removed))
    if unique_removed:
        guard = "SPATIALACC_INCLUDE_GUARD_" + hashlib.sha256(
            guard_seed.encode("utf-8")
        ).hexdigest()[:24].upper()
        if f"`ifndef {guard}" not in projected:
            projected = (
                f"`ifndef {guard}\n`define {guard}\n"
                + projected
                + ("" if projected.endswith("\n") else "\n")
                + f"`endif // {guard}\n"
            )
    return projected.encode("utf-8"), unique_removed


def _find_paths(
    host: str,
    port: int,
    root: str,
    *,
    kind: str,
    name: str = "",
    relative_suffix: str = "",
    timeout: int,
) -> list[str]:
    if not root:
        return []
    if host:
        argv = ["find", root, "-type", kind]
        if name:
            argv.extend(["-name", name])
        if relative_suffix:
            argv.extend(["-path", f"*/{relative_suffix}"])
        argv.append("-print")
        try:
            raw = remote_exec(host, port, argv, timeout)
        except Exception:
            return []
        return sorted(
            {
                _normalized_remote_path(value)
                for value in raw.decode("utf-8", errors="replace").splitlines()
                if value.strip()
            }
        )

    path = Path(root)
    if not path.is_dir():
        return []
    result: list[str] = []
    if kind == "d":
        candidates = (candidate for candidate in path.rglob("*") if candidate.is_dir())
    else:
        candidates = (candidate for candidate in path.rglob("*") if candidate.is_file())
    for candidate in candidates:
        candidate_text = candidate.as_posix()
        if name and candidate.name != name:
            continue
        if relative_suffix and not candidate_text.endswith("/" + relative_suffix):
            continue
        result.append(_normalized_remote_path(str(candidate.resolve())))
    return sorted(set(result))


def _path_is_file(host: str, port: int, path: str, timeout: int) -> bool:
    if not path:
        return False
    if not host:
        return Path(path).is_file()
    try:
        remote_exec(host, port, ["test", "-f", path], timeout)
    except Exception:
        return False
    return True


def _vivado_ip_catalog_roots(
    resolved_tool: dict[str, Any], timeout: int
) -> list[str]:
    host = str(resolved_tool.get("host") or "")
    port = int(resolved_tool.get("port") or 22)
    executable = str(resolved_tool.get("resolved_executable") or "")
    roots: list[str] = []
    for ancestor in _executable_ancestors(executable):
        candidate = _normalized_remote_path(posixpath.join(ancestor, "data", "ip"))
        if _directory_exists(host, port, candidate, timeout):
            roots.append(candidate)
    return roots


def _provider_installation_roots(
    authority: dict[str, Any],
    resolved_tool: dict[str, Any],
    invocations: list[dict[str, Any]],
    timeout: int,
) -> tuple[dict[str, list[str]], list[str]]:
    host = str(resolved_tool.get("host") or "")
    port = int(resolved_tool.get("port") or 22)
    catalog_roots = _vivado_ip_catalog_roots(resolved_tool, timeout)
    invocation_paths: dict[str, list[str]] = {}
    for invocation in invocations:
        group_id = str(invocation.get("provider_configuration_sha256") or "")
        invocation_paths.setdefault(group_id, []).extend(
            _normalized_remote_path(str(value))
            for value in invocation.get("input_remote_paths", [])
            if str(value)
        )

    roots_by_group: dict[str, list[str]] = {}
    for group_id, paths in invocation_paths.items():
        roots: set[str] = set()
        for path in paths:
            for catalog_root in catalog_roots:
                if not _is_within(path, catalog_root):
                    continue
                relative = posixpath.relpath(path, catalog_root)
                parts = PurePosixPath(relative).parts
                if len(parts) >= 3:
                    roots.add(
                        _normalized_remote_path(
                            posixpath.join(catalog_root, parts[0], parts[1])
                        )
                    )
        if roots:
            roots_by_group[group_id] = sorted(roots)
    return roots_by_group, []


def _exact_vivado_ip_source_roots(
    resolved_tool: dict[str, Any],
    source_path: str,
    source_raw: bytes,
    timeout: int,
) -> tuple[list[str], list[str]]:
    """Anchor an exported compiler input to byte-identical Vivado IP sources."""

    host = str(resolved_tool.get("host") or "")
    port = int(resolved_tool.get("port") or 22)
    catalog_roots = _vivado_ip_catalog_roots(resolved_tool, timeout)
    source_path = _normalized_remote_path(source_path)
    source_digest = sha256_bytes(source_raw)
    candidates: set[str] = set()
    for catalog_root in catalog_roots:
        if _is_within(source_path, catalog_root):
            candidates.add(source_path)
        else:
            candidates.update(
                _find_paths(
                    host,
                    port,
                    catalog_root,
                    kind="f",
                    name=PurePosixPath(source_path).name,
                    timeout=timeout,
                )
            )
    try:
        candidate_payloads = (
            _fetch_source_payloads(host, port, sorted(candidates), timeout)
            if candidates
            else {}
        )
    except Exception as exc:
        return [], [
            f"cannot anchor exported compiler input in the Vivado IP catalog: {exc}"
        ]
    matching = sorted(
        path
        for path, raw in candidate_payloads.items()
        if sha256_bytes(raw) == source_digest
    )
    roots: set[str] = set()
    for path in matching:
        for catalog_root in catalog_roots:
            if not _is_within(path, catalog_root):
                continue
            relative = posixpath.relpath(path, catalog_root)
            parts = PurePosixPath(relative).parts
            if len(parts) >= 3:
                roots.add(
                    _normalized_remote_path(
                        posixpath.join(catalog_root, parts[0], parts[1])
                    )
                )
    return sorted(roots), []


def _resolve_vcs_literal_include_dependencies(
    authority: dict[str, Any],
    resolved_tool: dict[str, Any],
    invocations: list[dict[str, Any]],
    payloads: dict[str, bytes],
    timeout: int,
) -> tuple[dict[str, Any], dict[str, bytes], dict[str, bytes], list[str]]:
    """Resolve include-only installation files from the selected provider tree."""

    host = str(resolved_tool.get("host") or "")
    port = int(resolved_tool.get("port") or 22)
    provider_roots, blockers = _provider_installation_roots(
        authority, resolved_tool, invocations, timeout
    )
    fetched: dict[str, bytes] = {}
    projection_payloads: dict[str, bytes] = {}
    payload_by_normalized = {
        _normalized_remote_path(path): raw for path, raw in payloads.items()
    }
    additional_paths: set[str] = set()
    projections: list[dict[str, Any]] = []
    projection_by_virtual: dict[str, tuple[str, bytes]] = {}
    source_root_cache: dict[tuple[str, str], list[str]] = {}
    forced_includes_by_basename: dict[str, list[str]] = {}
    include_feedback = authority.get("literal_include_feedback", {})
    for row in (
        include_feedback.get("edges", [])
        if isinstance(include_feedback, dict)
        else []
    ):
        if not isinstance(row, dict):
            continue
        basename = str(row.get("including_basename") or "")
        include_name = str(row.get("include_name") or "")
        if basename and include_name:
            forced_includes_by_basename.setdefault(basename, []).append(include_name)
    queue: list[dict[str, Any]] = []
    for invocation in invocations:
        for path in invocation.get("input_remote_paths", []):
            normalized = _normalized_remote_path(str(path))
            raw = payload_by_normalized.get(normalized)
            if raw is not None:
                queue.append(
                    {
                        "actual_path": normalized,
                        "virtual_path": normalized,
                        "include_root": "",
                        "raw": raw,
                        "forced_includes": forced_includes_by_basename.get(
                            PurePosixPath(normalized).name, []
                        ),
                        "ancestor_basenames": [PurePosixPath(normalized).name],
                        "invocation": invocation,
                    }
                )
        include_roots = [
            _normalized_remote_path(str(value))
            for value in invocation.get("include_directories", [])
            if str(value)
        ]
        for normalized, raw in payload_by_normalized.items():
            matching_roots = [
                root for root in include_roots if _is_within(normalized, root)
            ]
            if not matching_roots or not _is_hdl_path(normalized):
                continue
            queue.append(
                {
                    "actual_path": normalized,
                    "virtual_path": normalized,
                    "include_root": matching_roots[0],
                    "raw": raw,
                    "forced_includes": forced_includes_by_basename.get(
                        PurePosixPath(normalized).name, []
                    ),
                    "ancestor_basenames": [PurePosixPath(normalized).name],
                    "invocation": invocation,
                }
            )

    visited: set[tuple[str, str, str]] = set()
    while queue:
        node = queue.pop(0)
        invocation = node["invocation"]
        invocation_id = str(invocation.get("invocation_id") or "")
        visit_key = (
            invocation_id,
            str(node["actual_path"]),
            str(node["virtual_path"]),
        )
        if visit_key in visited:
            continue
        visited.add(visit_key)
        include_names = _literal_hdl_includes(node["raw"])
        for include_name in node.get("forced_includes", []):
            if include_name not in include_names:
                include_names.append(include_name)
        for include_name in include_names:
            if not include_name:
                blockers.append(
                    "official VCS compiler input contains a nonportable literal include: "
                    f"{node['actual_path']}"
                )
                continue
            include_directories = [
                _normalized_remote_path(str(value))
                for value in invocation.get("include_directories", [])
                if str(value)
            ]
            source_virtual_directory = _normalized_remote_path(
                posixpath.dirname(str(node["virtual_path"]))
            )

            def include_root_for(virtual_path: str) -> str:
                preferred = str(node["include_root"])
                for root in [preferred, *include_directories]:
                    if root and _is_within(virtual_path, root):
                        return root
                return ""

            virtual_candidates = [
                _normalized_remote_path(
                    posixpath.join(source_virtual_directory, include_name)
                ),
                *[
                    _normalized_remote_path(posixpath.join(root, include_name))
                    for root in include_directories
                ],
            ]
            resolved: tuple[str, str, str, bytes] | None = None
            for virtual_path in virtual_candidates:
                projected = projection_by_virtual.get(virtual_path)
                if projected is not None:
                    resolved = (
                        projected[0],
                        virtual_path,
                        include_root_for(virtual_path),
                        projected[1],
                    )
                    break
                raw = payload_by_normalized.get(virtual_path)
                if raw is not None:
                    resolved = (
                        virtual_path,
                        virtual_path,
                        include_root_for(virtual_path),
                        raw,
                    )
                    additional_paths.add(virtual_path)
                    break

            direct_candidates = [
                (
                    _normalized_remote_path(
                        posixpath.join(posixpath.dirname(str(node["actual_path"])), include_name)
                    ),
                    virtual_candidates[0],
                    include_root_for(virtual_candidates[0]),
                ),
                *[
                    (
                        _normalized_remote_path(posixpath.join(root, include_name)),
                        _normalized_remote_path(posixpath.join(root, include_name)),
                        root,
                    )
                    for root in include_directories
                ],
            ]
            if resolved is None:
                for actual_path, virtual_path, include_root in direct_candidates:
                    if not _path_is_file(host, port, actual_path, timeout):
                        continue
                    raw = _fetch_source_payloads(
                        host, port, [actual_path], timeout
                    )[actual_path]
                    fetched[actual_path] = raw
                    payload_by_normalized[actual_path] = raw
                    if actual_path == virtual_path:
                        additional_paths.add(actual_path)
                    else:
                        projection_by_virtual[virtual_path] = (actual_path, raw)
                    resolved = (actual_path, virtual_path, include_root, raw)
                    break

            if resolved is None:
                group_id = str(
                    invocation.get("provider_configuration_sha256") or ""
                )
                anchor_key = (
                    PurePosixPath(str(node["actual_path"])).name,
                    sha256_bytes(node["raw"]),
                )
                if anchor_key not in source_root_cache:
                    anchored_roots, anchor_blockers = _exact_vivado_ip_source_roots(
                        resolved_tool,
                        str(node["actual_path"]),
                        node["raw"],
                        timeout,
                    )
                    source_root_cache[anchor_key] = anchored_roots
                    blockers.extend(anchor_blockers)
                anchored_roots = source_root_cache[anchor_key]
                declared_roots = provider_roots.get(group_id, [])
                roots = anchored_roots or declared_roots
                if anchored_roots and declared_roots:
                    intersection = sorted(set(anchored_roots).intersection(declared_roots))
                    roots = intersection or anchored_roots
                candidates = sorted(
                    {
                        path
                        for root in roots
                        for path in _find_paths(
                            host,
                            port,
                            root,
                            kind="f",
                            relative_suffix=include_name,
                            timeout=timeout,
                        )
                    }
                )
                candidate_payloads: dict[str, bytes] = {}
                if candidates:
                    try:
                        candidate_payloads = _fetch_source_payloads(
                            host, port, candidates, timeout
                        )
                    except Exception as exc:
                        blockers.append(
                            f"cannot snapshot literal include {include_name}: {exc}"
                        )
                digests = {
                    sha256_bytes(raw) for raw in candidate_payloads.values()
                }
                if len(digests) > 1:
                    blockers.append(
                        "literal include has multiple content-distinct files in the selected "
                        f"provider installation: group={group_id}; include={include_name}; "
                        f"candidates={candidates}"
                    )
                    continue
                if candidate_payloads:
                    actual_path = sorted(candidate_payloads)[0]
                    raw = candidate_payloads[actual_path]
                    fetched.update(candidate_payloads)
                    payload_by_normalized.update(
                        {
                            _normalized_remote_path(path): value
                            for path, value in candidate_payloads.items()
                        }
                    )
                    include_root = str(node["include_root"])
                    if source_virtual_directory in include_directories:
                        include_root = source_virtual_directory
                        virtual_path = _normalized_remote_path(
                            posixpath.join(include_root, include_name)
                        )
                    elif include_root:
                        virtual_path = virtual_candidates[0]
                    elif include_directories:
                        include_root = include_directories[0]
                        virtual_path = _normalized_remote_path(
                            posixpath.join(include_root, include_name)
                        )
                    else:
                        blockers.append(
                            "literal include resolved from the selected provider installation but "
                            "the official VCS invocation has no portable include directory: "
                            f"{node['actual_path']} -> {include_name}"
                        )
                        continue
                    projection_by_virtual[virtual_path] = (actual_path, raw)
                    resolved = (actual_path, virtual_path, include_root, raw)

            if resolved is None:
                blockers.append(
                    "literal include is absent from the official export and selected provider "
                    f"installation: {node['actual_path']} -> {include_name}"
                )
                continue
            actual_path, virtual_path, include_root, raw = resolved
            if actual_path != virtual_path:
                if not include_root or not _is_within(virtual_path, include_root):
                    blockers.append(
                        "literal include projection is outside its official include directory: "
                        f"{actual_path} -> {virtual_path}"
                    )
                    continue
                projected_raw, removed_includes = _remove_recursive_literal_includes(
                    raw,
                    {
                        str(value)
                        for value in node.get("ancestor_basenames", [])
                        if str(value)
                    },
                    actual_path,
                )
                projection_payloads[virtual_path] = projected_raw
                projection_by_virtual[virtual_path] = (actual_path, projected_raw)
                raw = projected_raw
                relative_path = posixpath.relpath(virtual_path, include_root)
                binding = {
                    "provider_configuration_sha256": str(
                        invocation.get("provider_configuration_sha256") or ""
                    ),
                    "compile_invocation_id": invocation_id,
                    "including_remote_path": str(node["actual_path"]),
                    "include_name": include_name,
                    "resolved_remote_path": actual_path,
                    "target_include_remote_path": include_root,
                    "target_relative_path": relative_path,
                    "origin_sha256": sha256_bytes(
                        payload_by_normalized.get(actual_path, raw)
                    ),
                    "projected_sha256": sha256_bytes(projected_raw),
                    "recursive_include_edges_removed": removed_includes,
                    "resolution_policy": (
                        "official_search_order_then_unique_content_selected_provider_installation"
                    ),
                }
                if binding not in projections:
                    projections.append(binding)
            queue.append(
                {
                    "actual_path": actual_path,
                    "virtual_path": virtual_path,
                    "include_root": include_root,
                    "raw": raw,
                    "forced_includes": forced_includes_by_basename.get(
                        PurePosixPath(virtual_path).name, []
                    ),
                    "ancestor_basenames": [
                        *node.get("ancestor_basenames", []),
                        PurePosixPath(virtual_path).name,
                    ],
                    "invocation": invocation,
                }
            )

    descriptor = {
        "status": "pass" if not blockers else "fail",
        "selection_policy": (
            "recursive_literal_include_closure_from_official_vcs_search_order_and_selected_provider_vlnv"
        ),
        "provider_installation_roots": provider_roots,
        "additional_remote_paths": sorted(additional_paths),
        "projections": sorted(
            projections,
            key=lambda row: (
                row["compile_invocation_id"],
                row["target_include_remote_path"],
                row["target_relative_path"],
            ),
        ),
    }
    descriptor["authority_sha256"] = canonical_sha256(descriptor)
    return descriptor, fetched, projection_payloads, blockers


def _is_within(path: str, directory: str) -> bool:
    if not path or not directory or not posixpath.isabs(path) or not posixpath.isabs(directory):
        return False
    try:
        return posixpath.commonpath([path, directory]) == _normalized_remote_path(directory)
    except ValueError:
        return False


def _declared_design_units(raw: bytes, path: str, file_type: str = "") -> list[dict[str, str]]:
    if not _is_hdl_path(path, file_type):
        return []
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//.*?$|--.*?$", " ", text, flags=re.MULTILINE)
    patterns = [
        ("module", r"\bmodule\s+(?:automatic\s+|static\s+)?([A-Za-z_$][A-Za-z0-9_$]*)"),
        ("interface", r"\binterface\s+([A-Za-z_$][A-Za-z0-9_$]*)"),
        ("package", r"\bpackage\s+(?:body\s+)?([A-Za-z_$][A-Za-z0-9_$]*)"),
        ("program", r"\bprogram\s+([A-Za-z_$][A-Za-z0-9_$]*)"),
        ("primitive", r"\bprimitive\s+([A-Za-z_$][A-Za-z0-9_$]*)"),
        ("entity", r"\bentity\s+([A-Za-z][A-Za-z0-9_]*)\s+is\b"),
        ("architecture", r"\barchitecture\s+([A-Za-z][A-Za-z0-9_]*)\s+of\b"),
        ("configuration", r"\bconfiguration\s+([A-Za-z][A-Za-z0-9_]*)\s+of\b"),
    ]
    found: list[tuple[int, dict[str, str]]] = []
    for kind, pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            found.append((match.start(), {"kind": kind, "name": match.group(1)}))
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for _, row in sorted(found, key=lambda value: value[0]):
        key = (row["kind"].lower(), row["name"].lower())
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def _staged_directory_path(remote_directory: str) -> str:
    normalized = _normalized_remote_path(remote_directory)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def _staged_relative_path(remote_path: str) -> str:
    normalized = _normalized_remote_path(remote_path)
    basename = PurePosixPath(normalized).name
    if not basename or basename in {".", ".."} or any(value in basename for value in ("/", "\0", "\n", "\r")):
        raise ValueError(f"unsafe external fixture artifact basename: {remote_path!r}")
    parent_id = _staged_directory_path(posixpath.dirname(normalized))
    return str(PurePosixPath(parent_id) / basename)


def _run_vivado_export(
    authority: dict[str, Any], output_dir: Path, timeout: int
) -> tuple[dict[str, Any], dict[str, bytes], dict[str, Any]]:
    tool = authority["vivado_tool"]
    host = str(tool.get("host") or "")
    port = int(tool.get("port") or 22)
    executable = str(tool.get("executable") or "")
    project_path = str(authority["sample_project"]["remote_path"])
    output_dir.mkdir(parents=True, exist_ok=True)
    tcl_path = output_dir / "vivado_external_fixture_export.tcl"
    tcl_path.write_text(VIVADO_EXTERNAL_FIXTURE_TCL, encoding="utf-8")
    stdout_path = output_dir / "vivado_external_fixture_export.stdout.log"
    group_args = [
        value
        for group in authority.get("provider_groups", [])
        for value in (
            str(group.get("configuration_sha256") or ""),
            str(group.get("representative", {}).get("component_name") or ""),
        )
    ]

    def payload_paths(raw_export: dict[str, Any]) -> set[str]:
        paths = {
            str(source.get("remote_path") or "")
            for provider in raw_export.get("providers", [])
            for fileset in provider.get("filesets", [])
            for source in fileset.get("sources", [])
        } | {
            str(row.get("remote_path") or "")
            for provider in raw_export.get("providers", [])
            for fileset in provider.get("filesets", [])
            for row in fileset.get("export_files", [])
        } | {
            str(instance.get("configured_ip", {}).get("remote_path") or "")
            for group in authority.get("provider_groups", [])
            for instance in group.get("instances", [])
        }
        paths.discard("")
        forbidden_payloads: list[str] = []
        _path_guard(sorted(paths), "Vivado export payload", forbidden_payloads)
        if forbidden_payloads:
            raise RuntimeError("; ".join(forbidden_payloads))
        return paths

    if host:
        token = authority["authority_sha256"][:16]
        remote_dir = remote_exec(
            host,
            port,
            ["mktemp", "-d", f"/tmp/spatialaccagent_external_fixture_{token}_XXXXXX"],
            timeout,
        ).decode("utf-8", errors="replace").strip()
        if not remote_dir:
            raise RuntimeError("remote mktemp returned an empty external-fixture directory")
        remote_tcl = f"{remote_dir}/external_fixture.tcl"
        remote_manifest = f"{remote_dir}/fixture.tsv"
        remote_output = f"{remote_dir}/output"
        try:
            run_checked([*scp_prefix(port), str(tcl_path), f"{host}:{remote_tcl}"], timeout)
            argv = [
                executable,
                "-mode",
                "batch",
                "-notrace",
                "-nolog",
                "-nojournal",
                "-source",
                remote_tcl,
                "-tclargs",
                project_path,
                remote_manifest,
                remote_output,
                *group_args,
            ]
            proc = subprocess.run(
                [*ssh_prefix(host, port), shlex.join(argv)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=command_timeout(timeout),
                check=False,
            )
            stdout_path.write_bytes(proc.stdout)
            manifest_raw = remote_read(host, remote_manifest, timeout, port)
            raw_export = parse_external_fixture_stream(manifest_raw)
            paths = payload_paths(raw_export)
            payloads = _fetch_source_payloads(host, port, sorted(paths), timeout)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"Vivado external fixture export failed ({proc.returncode}); "
                    f"tail={proc.stdout.decode('utf-8', errors='replace')[-4000:]}"
                )
            transport = {
                "manifest_sha256": sha256_bytes(manifest_raw),
                "stdout_path": str(stdout_path),
                "stdout_sha256": sha256_file(stdout_path),
                "vivado_argv": argv,
            }
            return raw_export, payloads, transport
        finally:
            try:
                remote_exec(host, port, ["rm", "-rf", remote_dir], timeout)
            except Exception:
                pass
    with tempfile.TemporaryDirectory(prefix="spatialaccagent_external_fixture_") as temp_dir:
        manifest_path = Path(temp_dir) / "fixture.tsv"
        export_root = Path(temp_dir) / "output"
        argv = [
            executable,
            "-mode",
            "batch",
            "-notrace",
            "-nolog",
            "-nojournal",
            "-source",
            str(tcl_path),
            "-tclargs",
            project_path,
            str(manifest_path),
            str(export_root),
            *group_args,
        ]
        proc = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=command_timeout(timeout),
            check=False,
        )
        stdout_path.write_bytes(proc.stdout)
        if not manifest_path.is_file():
            raise RuntimeError(
                f"local Vivado external fixture export produced no manifest ({proc.returncode})"
            )
        manifest_raw = manifest_path.read_bytes()
        raw_export = parse_external_fixture_stream(manifest_raw)
        paths = payload_paths(raw_export)
        payloads = _fetch_source_payloads("", port, sorted(paths), timeout)
        if proc.returncode != 0:
            raise RuntimeError(
                f"local Vivado external fixture export failed ({proc.returncode}); "
                f"tail={proc.stdout.decode('utf-8', errors='replace')[-4000:]}"
            )
        return raw_export, payloads, {
            "manifest_sha256": sha256_bytes(manifest_raw),
            "stdout_path": str(stdout_path),
            "stdout_sha256": sha256_file(stdout_path),
            "vivado_argv": argv,
        }


def _materialize_snapshot(
    raw_export: dict[str, Any],
    payloads: dict[str, bytes],
    authority: dict[str, Any],
    output_dir: Path,
    timeout: int = 0,
) -> tuple[dict[str, Any], list[str]]:
    blockers = _validate_raw_export(raw_export, authority)
    payloads = dict(payloads)
    invocations, invocation_blockers = _parse_vcs_compile_invocations(raw_export, payloads)
    blockers.extend(invocation_blockers)
    resolved_tool = _resolved_vivado_tool(authority, timeout)
    setup, setup_payloads, setup_blockers = _discover_synopsys_setup(
        authority,
        invocations,
        timeout,
        resolved_tool,
        (str(output_dir.resolve()),),
    )
    blockers.extend(setup_blockers)
    for path, raw in setup_payloads.items():
        if path in payloads and payloads[path] != raw:
            blockers.append(f"synopsys setup payload conflicts with exported artifact: {path}")
        payloads[path] = raw

    fileset_paths = {
        str(source.get("remote_path") or "")
        for provider in raw_export.get("providers", [])
        for fileset in provider.get("filesets", [])
        for source in fileset.get("sources", [])
    }
    export_paths = {
        str(row.get("remote_path") or "")
        for provider in raw_export.get("providers", [])
        for fileset in provider.get("filesets", [])
        for row in fileset.get("export_files", [])
    }
    configured_ip_paths = {
        str(instance.get("configured_ip", {}).get("remote_path") or "")
        for group in authority.get("provider_groups", [])
        for instance in group.get("instances", [])
    }
    all_paths = fileset_paths | export_paths | configured_ip_paths
    all_paths.discard("")
    known_normalized = {_normalized_remote_path(path) for path in all_paths}
    invoked_paths = {
        _normalized_remote_path(path)
        for invocation in invocations
        for path in invocation.get("input_remote_paths", [])
        if str(path)
    }
    additional_installation_paths = sorted(invoked_paths - known_normalized)
    installation_authority, installation_blockers = (
        _derive_vivado_installation_hdl_authority(
            resolved_tool, additional_installation_paths
        )
    )
    blockers.extend(installation_blockers)
    additional_installation_paths = list(
        installation_authority.get("input_remote_paths", [])
    )
    missing_installation_paths = [
        path for path in additional_installation_paths if path not in payloads
    ]
    if missing_installation_paths:
        try:
            fetched = _fetch_source_payloads(
                str(resolved_tool.get("host") or ""),
                int(resolved_tool.get("port") or 22),
                missing_installation_paths,
                timeout,
            )
            payloads.update(fetched)
        except Exception as exc:
            blockers.append(f"cannot snapshot invoked Vivado installation HDL sources: {exc}")
    if installation_authority:
        installation_authority["files"] = [
            {
                "remote_path": path,
                "sha256": sha256_bytes(payloads[path]),
                "size_bytes": len(payloads[path]),
            }
            for path in additional_installation_paths
            if path in payloads
        ]
        installation_authority["authority_sha256"] = canonical_sha256(
            {
                key: value
                for key, value in installation_authority.items()
                if key != "authority_sha256"
            }
        )
    (
        include_dependency_authority,
        include_payloads,
        include_projection_payloads,
        include_blockers,
    ) = (
        _resolve_vcs_literal_include_dependencies(
            authority,
            resolved_tool,
            invocations,
            payloads,
            timeout,
        )
    )
    blockers.extend(include_blockers)
    for path, raw in include_payloads.items():
        existing = payloads.get(path)
        if existing is not None and existing != raw:
            blockers.append(
                f"literal include payload conflicts with exported artifact: {path}"
            )
        payloads[path] = raw
    all_paths.update(additional_installation_paths)
    all_paths.update(include_dependency_authority.get("additional_remote_paths", []))
    all_paths.update(str(row.get("remote_path") or "") for row in setup.get("files", []))
    all_paths.discard("")
    _path_guard(sorted(all_paths), "external fixture snapshot", blockers)

    payloads_by_normalized: dict[str, tuple[str, bytes]] = {}
    for remote_path, raw in payloads.items():
        normalized = _normalized_remote_path(remote_path)
        existing = payloads_by_normalized.get(normalized)
        if existing is not None and existing[1] != raw:
            blockers.append(
                "same-directory basename/content conflict in external fixture payloads: "
                f"{existing[0]} != {remote_path}"
            )
            continue
        payloads_by_normalized[normalized] = (remote_path, raw)
    missing_payloads = sorted(
        path for path in all_paths if _normalized_remote_path(path) not in payloads_by_normalized
    )
    if missing_payloads:
        blockers.append(f"external fixture snapshot omitted payloads: {missing_payloads}")

    fileset_metadata: dict[str, list[dict[str, Any]]] = {}
    export_metadata: dict[str, list[dict[str, Any]]] = {}
    for provider in raw_export.get("providers", []):
        for fileset in provider.get("filesets", []):
            for source in fileset.get("sources", []):
                normalized = _normalized_remote_path(str(source.get("remote_path") or ""))
                fileset_metadata.setdefault(normalized, []).append(
                    {
                        "provider_configuration_sha256": provider.get("group_id"),
                        "fileset_index": fileset.get("index"),
                        "compile_order": source.get("compile_order"),
                        "properties": copy.deepcopy(source.get("properties", {})),
                    }
                )
            for row in fileset.get("export_files", []):
                normalized = _normalized_remote_path(str(row.get("remote_path") or ""))
                export_metadata.setdefault(normalized, []).append(
                    {
                        "provider_configuration_sha256": provider.get("group_id"),
                        "fileset_index": fileset.get("index"),
                    }
                )
    hdl_export_paths = {
        path
        for path in export_metadata
        if _is_hdl_path(path)
    }
    invoked_hdl_paths = {path for path in invoked_paths if _is_hdl_path(path)}
    compiler_input_paths = invoked_hdl_paths - hdl_export_paths

    runtime_bindings: dict[str, dict[str, Any]] = {}
    for normalized in sorted(export_metadata):
        if normalized in hdl_export_paths:
            continue
        metadata_rows = export_metadata.get(normalized, [])
        relevant_invocations = [
            invocation
            for invocation in invocations
            if any(
                invocation.get("provider_configuration_sha256")
                == metadata.get("provider_configuration_sha256")
                and invocation.get("fileset_index") == metadata.get("fileset_index")
                for metadata in metadata_rows
            )
        ]
        relative_paths: list[str] = []
        binding_scripts: list[str] = []
        for invocation in relevant_invocations:
            script_path = _normalized_remote_path(
                str(invocation.get("script_remote_path") or "")
            )
            script_directory = posixpath.dirname(script_path)
            if normalized == script_path or not _is_within(normalized, script_directory):
                continue
            relative = posixpath.relpath(normalized, script_directory)
            if relative in {"", "."} or relative == ".." or relative.startswith("../"):
                continue
            authority_paths = [
                script_path,
                *(
                    _normalized_remote_path(str(path))
                    for row in relevant_invocations
                    for path in row.get("input_remote_paths", [])
                ),
            ]
            referenced = False
            for authority_path in dict.fromkeys(authority_paths):
                payload_entry = payloads_by_normalized.get(authority_path)
                if payload_entry is None:
                    continue
                text = payload_entry[1].decode("utf-8", errors="replace")
                candidates = [normalized, relative, posixpath.basename(relative)]
                if any(
                    re.search(
                        rf"(?<![A-Za-z0-9_./-]){re.escape(candidate)}(?![A-Za-z0-9_./-])",
                        text,
                    )
                    for candidate in candidates
                    if candidate
                ):
                    referenced = True
                    break
            if referenced:
                relative_paths.append(relative)
                binding_scripts.append(script_path)
        unique_relative_paths = list(dict.fromkeys(relative_paths))
        if len(unique_relative_paths) > 1:
            blockers.append(
                "runtime export artifact has conflicting command-directory paths: "
                f"{normalized} -> {unique_relative_paths}"
            )
            continue
        if unique_relative_paths:
            runtime_bindings[normalized] = {
                "runtime_staged_path": unique_relative_paths[0],
                "runtime_script_remote_paths": list(dict.fromkeys(binding_scripts)),
            }

    staged_dir = output_dir / "external_simulation_fixture_sources"
    materialized_by_normalized: dict[str, dict[str, Any]] = {}
    projected_include_rows: list[dict[str, Any]] = []
    staged_claims: dict[str, tuple[str, str]] = {}
    aliases_by_normalized: dict[str, list[str]] = {}
    for path in sorted(all_paths):
        aliases_by_normalized.setdefault(_normalized_remote_path(path), []).append(path)
    for normalized in sorted(aliases_by_normalized):
        payload_entry = payloads_by_normalized.get(normalized)
        if payload_entry is None or _is_forbidden_legacy_path(normalized):
            continue
        _, raw = payload_entry
        digest = sha256_bytes(raw)
        staged_path = _staged_relative_path(normalized)
        claim = staged_claims.get(staged_path)
        if claim is not None and claim[1] != digest:
            blockers.append(
                "same-directory basename/content conflict in staged external fixture: "
                f"{claim[0]} != {normalized}"
            )
            continue
        staged_claims[staged_path] = (normalized, digest)
        local_path = staged_dir / staged_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if local_path.is_file() and sha256_file(local_path) == digest:
            pass
        else:
            temp_path = local_path.with_suffix(local_path.suffix + ".tmp")
            temp_path.write_bytes(raw)
            os.replace(temp_path, local_path)
        if normalized in compiler_input_paths:
            classification = "compiler_input_hdl"
        elif normalized in hdl_export_paths:
            classification = "hdl_export_artifact"
        elif normalized in runtime_bindings:
            classification = "runtime_auxiliary"
        else:
            classification = "authority_evidence"
        metadata_rows = fileset_metadata.get(normalized, [])
        properties = next(
            (
                row.get("properties", {})
                for row in metadata_rows
                if isinstance(row.get("properties"), dict)
            ),
            {},
        )
        artifact_id = "external-fixture-artifact:" + canonical_sha256(
            [normalized, digest]
        )[:24]
        source_id = "external-fixture-source:" + canonical_sha256(
            [normalized, digest]
        )[:24]
        row = {
            "remote_path": normalized,
            "original_remote_paths": sorted(set(aliases_by_normalized[normalized])),
            "path": str(local_path.resolve()),
            "staged_path": staged_path,
            "sha256": digest,
            "size_bytes": len(raw),
            "source_id": source_id,
            "artifact_id": artifact_id,
            "classification": classification,
            "invoked_by_compile": normalized in invoked_hdl_paths,
            "declared_design_units": _declared_design_units(
                raw, normalized, str(properties.get("FILE_TYPE") or "")
            ),
        }
        materialized_by_normalized[normalized] = row

    materialized_by_staged_path = {
        str(row.get("staged_path") or ""): row
        for row in materialized_by_normalized.values()
        if str(row.get("staged_path") or "")
    }
    bound_include_dependencies: list[dict[str, Any]] = []
    for binding in include_dependency_authority.get("projections", []):
        if not isinstance(binding, dict):
            continue
        remote_path = _normalized_remote_path(
            str(binding.get("resolved_remote_path") or "")
        )
        include_root = _normalized_remote_path(
            str(binding.get("target_include_remote_path") or "")
        )
        relative_path = posixpath.normpath(
            str(binding.get("target_relative_path") or "")
        )
        target_remote_path = _normalized_remote_path(
            posixpath.join(include_root, relative_path)
        )
        payload_entry = payloads_by_normalized.get(remote_path)
        projected_raw = include_projection_payloads.get(target_remote_path)
        if (
            (payload_entry is None and projected_raw is None)
            or not include_root
            or relative_path in {"", ".", ".."}
            or relative_path.startswith("../")
            or posixpath.isabs(relative_path)
        ):
            blockers.append(
                "literal include projection is missing a safe payload/target binding: "
                f"{remote_path} -> {include_root}/{relative_path}"
            )
            continue
        raw = projected_raw if projected_raw is not None else payload_entry[1]
        digest = sha256_bytes(raw)
        staged_path = str(
            PurePosixPath(_staged_directory_path(include_root))
            / PurePosixPath(relative_path)
        )
        claim = staged_claims.get(staged_path)
        if claim is not None and claim[1] != digest:
            blockers.append(
                "literal include projection conflicts with an existing staged file: "
                f"{claim[0]} != {remote_path} at {staged_path}"
            )
            continue
        row = materialized_by_staged_path.get(staged_path)
        if row is None:
            staged_claims[staged_path] = (remote_path, digest)
            local_path = staged_dir / staged_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            if not local_path.is_file() or sha256_file(local_path) != digest:
                temp_path = local_path.with_suffix(local_path.suffix + ".tmp")
                temp_path.write_bytes(raw)
                os.replace(temp_path, local_path)
            artifact_id = "external-fixture-artifact:" + canonical_sha256(
                [target_remote_path, remote_path, staged_path, digest]
            )[:24]
            source_id = "external-fixture-source:" + canonical_sha256(
                [target_remote_path, remote_path, staged_path, digest]
            )[:24]
            row = {
                "remote_path": target_remote_path,
                "original_remote_paths": [remote_path],
                "include_origin_remote_path": remote_path,
                "path": str(local_path.resolve()),
                "staged_path": staged_path,
                "sha256": digest,
                "size_bytes": len(raw),
                "source_id": source_id,
                "artifact_id": artifact_id,
                "classification": "literal_include_dependency",
                "invoked_by_compile": False,
                "declared_design_units": _declared_design_units(raw, remote_path),
            }
            projected_include_rows.append(row)
            materialized_by_staged_path[staged_path] = row
        bound_include_dependencies.append({**binding, **row})

    include_dependency_authority = {
        **include_dependency_authority,
        "files": bound_include_dependencies,
    }
    include_dependency_authority["authority_sha256"] = canonical_sha256(
        {
            key: value
            for key, value in include_dependency_authority.items()
            if key != "authority_sha256"
        }
    )

    def artifact_for(remote_path: str) -> dict[str, Any]:
        return materialized_by_normalized.get(_normalized_remote_path(remote_path), {})

    providers = []
    export_artifacts = []
    export_contexts = []
    for provider in raw_export.get("providers", []):
        provider_row = {
            key: copy.deepcopy(value)
            for key, value in provider.items()
            if key != "filesets"
        }
        provider_row["filesets"] = []
        for fileset in provider.get("filesets", []):
            fileset_row = {
                key: copy.deepcopy(value)
                for key, value in fileset.items()
                if key not in {"sources", "export_files"}
            }
            source_rows = []
            for source in fileset.get("sources", []):
                remote_path = str(source.get("remote_path") or "")
                artifact = artifact_for(remote_path)
                properties = source.get("properties", {}) if isinstance(source.get("properties"), dict) else {}
                row = {
                    **copy.deepcopy(source),
                    **artifact,
                    "provider_configuration_sha256": provider.get("group_id"),
                    "fileset_index": fileset.get("index"),
                    "library": properties.get("LIBRARY", ""),
                    "file_type": properties.get("FILE_TYPE", ""),
                    "language": properties.get("FILE_TYPE", ""),
                    "is_global_include": str(properties.get("IS_GLOBAL_INCLUDE", "")).lower()
                    in {"1", "true"},
                    "parent_composite_file": properties.get("PARENT_COMPOSITE_FILE", ""),
                    "role": artifact.get("classification", "runtime_auxiliary"),
                }
                source_rows.append(row)
            artifact_rows = []
            for artifact_row in fileset.get("export_files", []):
                remote_path = str(artifact_row.get("remote_path") or "")
                artifact = {
                    **copy.deepcopy(artifact_row),
                    **artifact_for(remote_path),
                    "provider_configuration_sha256": provider.get("group_id"),
                    "fileset_index": fileset.get("index"),
                    "role": "vivado_export_simulation_artifact",
                }
                artifact_rows.append(artifact)
                export_artifacts.append(artifact)
                payload_entry = payloads_by_normalized.get(_normalized_remote_path(remote_path))
                raw = payload_entry[1] if payload_entry else b""
                if PurePosixPath(remote_path).suffix.lower() in CONTEXT_SUFFIXES and len(raw) <= 4 * 1024 * 1024:
                    export_contexts.append(
                        {
                            "remote_path": artifact.get("remote_path"),
                            "path": artifact.get("path"),
                            "staged_path": artifact.get("staged_path"),
                            "source_id": artifact.get("source_id"),
                            "artifact_id": artifact.get("artifact_id"),
                            "sha256": artifact.get("sha256"),
                            "text": raw.decode("utf-8", errors="replace"),
                        }
                    )
            fileset_row["sources"] = source_rows
            fileset_row["export_files"] = artifact_rows
            provider_row["filesets"].append(fileset_row)
        providers.append(provider_row)
    configured_ips = []
    for group in authority.get("provider_groups", []):
        for instance in group.get("instances", []):
            remote_path = str(instance.get("configured_ip", {}).get("remote_path") or "")
            configured_ips.append(
                {
                    "provider_configuration_sha256": group.get("configuration_sha256"),
                    "cell_id": instance.get("cell_id"),
                    "component_name": instance.get("component_name"),
                    **artifact_for(remote_path),
                }
            )

    invocations_by_path: dict[str, list[dict[str, Any]]] = {}
    invoked_order: list[str] = []
    for invocation in invocations:
        for path in invocation.get("input_remote_paths", []):
            normalized = _normalized_remote_path(str(path))
            if normalized not in invoked_order:
                invoked_order.append(normalized)
            invocations_by_path.setdefault(normalized, []).append(invocation)

    def compile_row(normalized: str) -> dict[str, Any]:
        artifact = materialized_by_normalized.get(normalized, {})
        metadata_rows = fileset_metadata.get(normalized, [])
        invocation_rows = invocations_by_path.get(normalized, [])
        properties = next(
            (
                row.get("properties", {})
                for row in metadata_rows
                if isinstance(row.get("properties"), dict)
            ),
            {},
        )
        provider_ids = list(
            dict.fromkeys(
                str(row.get("provider_configuration_sha256") or "")
                for row in [*metadata_rows, *export_metadata.get(normalized, []), *invocation_rows]
                if str(row.get("provider_configuration_sha256") or "")
            )
        )
        libraries = list(
            dict.fromkeys(
                [
                    str(properties.get("LIBRARY") or ""),
                    *(str(row.get("work_library") or "") for row in invocation_rows),
                ]
            )
        )
        libraries = [value for value in libraries if value]
        return {
            **artifact,
            "provider_configuration_sha256": provider_ids[0] if provider_ids else "",
            "provider_configuration_sha256s": provider_ids,
            "fileset_indexes": list(
                dict.fromkeys(row.get("fileset_index") for row in metadata_rows if row.get("fileset_index") is not None)
            ),
            "compile_orders": list(
                dict.fromkeys(row.get("compile_order") for row in metadata_rows if row.get("compile_order") is not None)
            ),
            "libraries": libraries,
            "library": libraries[0] if libraries else "",
            "file_type": str(properties.get("FILE_TYPE") or PurePosixPath(normalized).suffix),
            "language": str(properties.get("FILE_TYPE") or PurePosixPath(normalized).suffix),
            "compile_invocation_ids": [row["invocation_id"] for row in invocation_rows],
            "role": artifact.get("classification"),
        }

    compiler_inputs = [
        compile_row(path) for path in invoked_order if path in compiler_input_paths
    ]
    hdl_export_artifacts = [
        compile_row(path) for path in sorted(hdl_export_paths)
    ]
    compile_source_by_path = {
        row["remote_path"]: row
        for row in [*compiler_inputs, *hdl_export_artifacts]
        if row.get("remote_path") and row.get("invoked_by_compile")
    }
    compile_sources = [
        compile_source_by_path[path] for path in invoked_order if path in compile_source_by_path
    ]
    runtime_auxiliary_files = []
    runtime_staged_claims: dict[str, tuple[str, str]] = {}
    for normalized, binding in sorted(runtime_bindings.items()):
        artifact = materialized_by_normalized.get(normalized, {})
        if not artifact:
            continue
        runtime_staged_path = str(binding["runtime_staged_path"])
        claim = runtime_staged_claims.get(runtime_staged_path)
        if claim is not None and claim[1] != artifact.get("sha256"):
            blockers.append(
                "runtime auxiliary staging conflict: "
                f"{claim[0]} and {normalized} map to {runtime_staged_path}"
            )
            continue
        runtime_staged_claims[runtime_staged_path] = (
            normalized,
            str(artifact.get("sha256") or ""),
        )
        runtime_auxiliary_files.append(
            {
                **artifact,
                **binding,
                "runtime_script_artifact_ids": [
                    artifact_for(path).get("artifact_id")
                    for path in binding.get("runtime_script_remote_paths", [])
                ],
            }
        )
    if not compiler_inputs:
        blockers.append("materialized external fixture has no true compiler-input HDL")
    if not compile_sources:
        blockers.append("materialized external fixture has no official invoked compile sources")
    if not export_contexts:
        blockers.append("materialized external fixture has no readable VCS export command context")

    include_remote_paths: list[str] = []
    for invocation in invocations:
        for remote_path in invocation.get("include_directories", []):
            normalized = _normalized_remote_path(str(remote_path))
            if normalized and normalized not in include_remote_paths:
                include_remote_paths.append(normalized)
    include_directory_rows: list[dict[str, Any]] = []
    include_by_remote: dict[str, dict[str, Any]] = {}
    include_staged_claims: dict[str, str] = {}
    all_materialized_rows = [
        *materialized_by_normalized.values(),
        *projected_include_rows,
    ]
    for remote_path in include_remote_paths:
        staged_path = _staged_directory_path(remote_path)
        members = [
            row
            for row in sorted(
                all_materialized_rows,
                key=lambda value: (
                    str(value.get("staged_path") or ""),
                    str(value.get("remote_path") or ""),
                ),
            )
            if PurePosixPath(staged_path)
            in PurePosixPath(str(row.get("staged_path") or "")).parents
        ]
        if not members:
            blockers.append(
                f"official VCS include directory has no directly materialized members: {remote_path}"
            )
            continue
        existing_remote = include_staged_claims.get(staged_path)
        if existing_remote is not None and existing_remote != remote_path:
            blockers.append(
                "portable include-directory staging conflict: "
                f"{existing_remote} and {remote_path} map to {staged_path}"
            )
            continue
        include_staged_claims[staged_path] = remote_path
        if any(
            PurePosixPath(staged_path)
            not in PurePosixPath(str(row.get("staged_path") or "")).parents
            for row in members
        ):
            blockers.append(
                f"portable include-directory member staging is inconsistent: {remote_path}"
            )
            continue
        member_source_ids = [str(row.get("source_id") or "") for row in members]
        if any(not value for value in member_source_ids):
            blockers.append(
                f"portable include-directory member lacks source_id: {remote_path}"
            )
            continue
        row = {
            "include_dir_id": "external-fixture-include-dir:"
            + canonical_sha256([remote_path, staged_path, member_source_ids])[:24],
            "remote_path": remote_path,
            "staged_path": staged_path,
            "member_source_ids": member_source_ids,
        }
        include_directory_rows.append(row)
        include_by_remote[remote_path] = row

    bound_invocations = []
    for invocation in invocations:
        input_rows = [artifact_for(path) for path in invocation.get("input_remote_paths", [])]
        invocation_include_paths = [
            _normalized_remote_path(str(path))
            for path in invocation.get("include_directories", [])
        ]
        bound_invocations.append(
            {
                **invocation,
                "script_artifact_id": artifact_for(
                    str(invocation.get("script_remote_path") or "")
                ).get("artifact_id"),
                "input_source_ids": [row.get("source_id") for row in input_rows],
                "input_artifact_ids": [row.get("artifact_id") for row in input_rows],
                "include_directory_ids": [
                    include_by_remote[path]["include_dir_id"]
                    for path in invocation_include_paths
                    if path in include_by_remote
                ],
            }
        )
        if len(bound_invocations[-1]["include_directory_ids"]) != len(
            invocation_include_paths
        ):
            blockers.append(
                "VCS invocation include-directory IDs do not preserve the official path sequence: "
                f"{invocation.get('invocation_id')}"
            )

    setup_files = []
    for row in setup.get("files", []):
        setup_files.append({**row, **artifact_for(str(row.get("remote_path") or ""))})
    bound_setup = {
        **setup,
        **artifact_for(str(setup.get("remote_path") or "")),
        "files": setup_files,
    }
    if setup:
        bound_setup["setup_authority_sha256"] = canonical_sha256(
            {
                key: value
                for key, value in bound_setup.items()
                if key != "setup_authority_sha256"
            }
        )
    bound_installation_authority = {
        **installation_authority,
        "files": [
            {**row, **artifact_for(str(row.get("remote_path") or ""))}
            for row in installation_authority.get("files", [])
        ],
    }
    if installation_authority:
        bound_installation_authority["authority_sha256"] = canonical_sha256(
            {
                key: value
                for key, value in bound_installation_authority.items()
                if key != "authority_sha256"
            }
        )
    compile_authority = {
        "schema_version": COMPILE_AUTHORITY_SCHEMA_VERSION,
        "status": "pass" if not blockers else "fail",
        "source": "vivado_configured_ip_example_export_simulation_vcs",
        "project_part": authority.get("sample_project", {}).get("part"),
        "vivado_version": raw_export.get("metadata", {}).get("vivado_version"),
        "configured_ips": configured_ips,
        "compile_sources": compile_sources,
        "compiler_inputs": compiler_inputs,
        "hdl_export_artifacts": hdl_export_artifacts,
        "runtime_auxiliary_files": runtime_auxiliary_files,
        "compile_invocations": bound_invocations,
        "include_directories": include_directory_rows,
        "literal_include_dependency_closure": include_dependency_authority,
        "synopsys_sim_setup": bound_setup,
        "vivado_installation_hdl_authority": bound_installation_authority,
        "export_artifacts": export_artifacts,
        "export_contexts": export_contexts,
        "provider_groups_sha256": canonical_sha256(authority.get("provider_groups", [])),
        "classification_policy": {
            "compiler_input_hdl_requires_official_vlogan_or_vhdlan_invocation": True,
            "exported_hdl_is_separate_from_non_exported_compiler_input": True,
            "runtime_auxiliary_requires_export_file_and_relative_runtime_reference": True,
            "fileset_data_configured_ip_and_setup_are_not_runtime_auxiliary": True,
            "invoked_installation_hdl_requires_resolved_vivado_executable_ancestor": True,
            "literal_include_dependencies_are_recursively_hash_anchored_to_vivado_ip_sources": True,
            "literal_include_dependencies_are_projected_to_official_include_directories": True,
            "same_directory_basename_content_conflicts_fail_closed": True,
        },
    }
    compile_authority["compile_authority_sha256"] = canonical_sha256(compile_authority)
    return {
        "providers": providers,
        "materialized_files": sorted(
            all_materialized_rows,
            key=lambda row: (
                str(row.get("staged_path") or ""),
                str(row.get("remote_path") or ""),
                str(row.get("source_id") or ""),
            ),
        ),
        "compile_authority": compile_authority,
    }, blockers


def _vivado_export_cache_projection(authority: dict[str, Any]) -> dict[str, Any]:
    """Inputs that can change Vivado's official example/export result.

    Python projection code is intentionally absent: changing local classification
    must not invalidate an expensive, hash-complete Vivado export.
    """

    groups = []
    for group in authority.get("provider_groups", []):
        instances = []
        for instance in group.get("instances", []):
            configured_ip = instance.get("configured_ip", {})
            instances.append(
                {
                    "cell_id": instance.get("cell_id"),
                    "component_name": instance.get("component_name"),
                    "remote_path": configured_ip.get("remote_path"),
                    "sha256": configured_ip.get("sha256"),
                    "size_bytes": configured_ip.get("size_bytes"),
                    "selected_by_runtime_timing_authority": instance.get(
                        "selected_by_runtime_timing_authority"
                    ),
                }
            )
        groups.append(
            {
                "configuration_sha256": group.get("configuration_sha256"),
                "configuration": copy.deepcopy(group.get("configuration")),
                "representative_component_name": group.get("representative", {}).get(
                    "component_name"
                ),
                "instances": instances,
            }
        )
    tool = authority.get("vivado_tool", {})
    sample_project = authority.get("sample_project", {})
    return {
        "schema_version": "spatialaccagent.vivado_external_fixture_export_cache.v1",
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "sample_project": {
            key: sample_project.get(key)
            for key in (
                "remote_path",
                "sha256",
                "size_bytes",
                "part",
                "vivado_version",
            )
        },
        "vivado_tool": {
            key: tool.get(key) for key in ("host", "port", "executable", "role", "name")
        },
        "provider_groups": groups,
        "vivado_tcl_sha256": authority.get("implementation", {}).get(
            "vivado_tcl_sha256"
        ),
    }


def _vivado_export_cache_sha256(authority: dict[str, Any]) -> str:
    return canonical_sha256(_vivado_export_cache_projection(authority))


def _read_hash_valid_materialized_payloads(
    report: dict[str, Any],
) -> tuple[dict[str, bytes], list[str]]:
    payloads: dict[str, bytes] = {}
    blockers: list[str] = []
    rows = report.get("materialized_files", [])
    if not isinstance(rows, list) or not rows:
        return {}, ["cached Vivado export has no materialized payload rows"]
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            blockers.append(f"cached materialized payload row {index} is malformed")
            continue
        path = Path(str(row.get("path") or ""))
        remote_path = str(row.get("remote_path") or "")
        if (
            not remote_path
            or _is_forbidden_legacy_path(path)
            or not path.is_file()
            or row.get("sha256") != sha256_file(path)
            or row.get("size_bytes") != path.stat().st_size
        ):
            blockers.append(f"cached materialized payload is missing or hash-invalid: {remote_path}")
            continue
        raw = path.read_bytes()
        aliases = row.get("original_remote_paths", [])
        aliases = aliases if isinstance(aliases, list) else []
        for key in [remote_path, *(str(value) for value in aliases if str(value))]:
            existing = payloads.get(key)
            if existing is not None and existing != raw:
                blockers.append(f"cached materialized payload aliases conflict: {key}")
            payloads[key] = raw
    return payloads, blockers


def _reprojectable_vivado_export(
    report_path: Path,
    authority: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, bytes], dict[str, Any], list[str]]:
    """Return absent/changed/ready/invalid without invoking Vivado."""

    report = _read_json_if_exists(report_path)
    if not report:
        return "absent", {}, {}, {}, []
    expected_cache_sha = _vivado_export_cache_sha256(authority)
    snapshot = report.get("vivado_export_snapshot", {})
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    observed_cache_sha = str(
        snapshot.get("export_cache_sha256")
        or report.get("vivado_export_cache_sha256")
        or _vivado_export_cache_sha256(
            report.get("authority", {}) if isinstance(report.get("authority"), dict) else {}
        )
    )
    if observed_cache_sha != expected_cache_sha:
        return "changed", {}, {}, {}, []
    blockers: list[str] = []
    if report.get("contract_sha256") != _contract_sha256(report):
        blockers.append("matching cached Vivado export report has an invalid contract hash")
    raw_export = snapshot.get("raw_export")
    if not isinstance(raw_export, dict) or not raw_export.get("providers"):
        providers = report.get("providers")
        compile_authority = report.get("compile_authority", {})
        if isinstance(providers, list) and providers:
            raw_export = {
                "schema_version": EXPORT_SCHEMA_VERSION,
                "metadata": {
                    "vivado_version": compile_authority.get("vivado_version")
                    if isinstance(compile_authority, dict)
                    else None,
                    "export_status": "pass",
                },
                "providers": copy.deepcopy(providers),
            }
        else:
            raw_export = {}
            blockers.append("matching cache cannot reconstruct the official Vivado export manifest")
    payloads, payload_blockers = _read_hash_valid_materialized_payloads(report)
    blockers.extend(payload_blockers)
    official_payload_paths = {
        _normalized_remote_path(str(source.get("remote_path") or ""))
        for provider in raw_export.get("providers", [])
        for fileset in provider.get("filesets", [])
        for source in fileset.get("sources", [])
    } | {
        _normalized_remote_path(str(row.get("remote_path") or ""))
        for provider in raw_export.get("providers", [])
        for fileset in provider.get("filesets", [])
        for row in fileset.get("export_files", [])
    } | {
        _normalized_remote_path(
            str(instance.get("configured_ip", {}).get("remote_path") or "")
        )
        for group in authority.get("provider_groups", [])
        for instance in group.get("instances", [])
    }
    official_payload_paths.discard("")
    payloads = {
        path: raw
        for path, raw in payloads.items()
        if _normalized_remote_path(path) in official_payload_paths
    }
    transport = {
        "vivado_export_cache_reused": True,
        "local_projection_recomputed": True,
        "source_report": str(report_path),
        "export_cache_sha256": expected_cache_sha,
    }
    if blockers:
        return "invalid", raw_export, payloads, transport, blockers
    return "ready", raw_export, payloads, transport, []


def reusable_external_simulation_fixture(
    report_path: Path, authority: dict[str, Any]
) -> dict[str, Any]:
    report = _read_json_if_exists(report_path)
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("status") != "pass"
        or report.get("authority_sha256") != authority.get("authority_sha256")
        or report.get("authority") != authority
        or report.get("contract_sha256") != _contract_sha256(report)
    ):
        return {}
    for row in report.get("materialized_files", []):
        if not isinstance(row, dict):
            return {}
        path = Path(str(row.get("path") or ""))
        if (
            _is_forbidden_legacy_path(path)
            or not path.is_file()
            or row.get("sha256") != sha256_file(path)
            or row.get("size_bytes") != path.stat().st_size
        ):
            return {}
    return report


Exporter = Callable[
    [dict[str, Any], Path, int],
    tuple[dict[str, Any], dict[str, bytes], dict[str, Any]],
]


def materialize_external_simulation_fixture(
    run_dir: Path,
    out: Path | None = None,
    timeout: int = 0,
    *,
    exporter: Exporter | None = None,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    output_dir = run_dir / "verification" / "board_interface"
    report_path = (out or output_dir / "external_simulation_fixture.json").resolve()
    blockers: list[str] = []
    _path_guard([report_path, output_dir], "external fixture output", blockers)
    authority, authority_blockers = derive_external_fixture_authority(run_dir, timeout)
    blockers.extend(authority_blockers)
    if not blockers:
        cached = reusable_external_simulation_fixture(report_path, authority)
        if cached:
            return {**cached, "cache_reused": True}
    snapshot: dict[str, Any] = {}
    transport: dict[str, Any] = {}
    raw_export: dict[str, Any] = {}
    payloads: dict[str, bytes] = {}
    if not blockers:
        cache_state, cached_export, cached_payloads, cached_transport, cache_blockers = (
            _reprojectable_vivado_export(report_path, authority)
        )
        if cache_state == "ready":
            raw_export, payloads, transport = (
                cached_export,
                cached_payloads,
                cached_transport,
            )
        elif cache_state == "invalid":
            blockers.extend(cache_blockers)
            transport = cached_transport
            raw_export = cached_export
            previous = _read_json_if_exists(report_path)
            snapshot = {
                key: copy.deepcopy(previous[key])
                for key in ("providers", "materialized_files", "compile_authority")
                if key in previous
            }
        else:
            try:
                raw_export, payloads, transport = (exporter or _run_vivado_export)(
                    authority, output_dir, timeout
                )
            except Exception as exc:
                blockers.append(f"Vivado external simulation fixture materialization failed: {exc}")
    if not blockers and raw_export:
        try:
            snapshot, snapshot_blockers = _materialize_snapshot(
                raw_export, payloads, authority, output_dir, timeout
            )
            blockers.extend(snapshot_blockers)
        except Exception as exc:
            blockers.append(f"external simulation fixture local projection failed: {exc}")
    export_cache = _vivado_export_cache_projection(authority)
    export_cache_sha = canonical_sha256(export_cache)
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if not blockers else "fail",
        "run_dir": str(run_dir),
        "authority": authority,
        "authority_sha256": authority.get("authority_sha256"),
        "vivado_export_cache": export_cache,
        "vivado_export_cache_sha256": export_cache_sha,
        "vivado_export_snapshot": {
            "schema_version": "spatialaccagent.vivado_external_fixture_export_snapshot.v1",
            "status": "pass" if raw_export else "absent",
            "export_cache_sha256": export_cache_sha,
            "raw_export": raw_export,
        },
        **snapshot,
        "transport": transport,
        "blockers": blockers,
        "policy": {
            "legacy_case_fixture_inputs_read": False,
            "configured_ip_example_project_generated_by_vivado": True,
            "all_compile_and_export_payloads_hash_materialized": True,
            "cache_requires_exact_authority_and_every_payload_hash": True,
            "vivado_export_cache_excludes_local_projection_implementation": True,
            "matching_hash_valid_vivado_export_is_reprojected_without_export": True,
            "matching_but_incomplete_vivado_export_fails_without_rerun": True,
            "compile_order_missing_instances_are_decided_by_mandatory_real_vcs": True,
            "failure_is_closed": True,
        },
    }
    report["contract_sha256"] = _contract_sha256(report)
    write_json(report_path, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--remote-timeout-sec",
        type=int,
        default=0,
        help="Outer Vivado/transport timeout; 0 waits indefinitely during development",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = materialize_external_simulation_fixture(
        args.run_dir,
        args.out,
        args.remote_timeout_sec,
    )
    print(args.out or args.run_dir / "verification" / "board_interface" / "external_simulation_fixture.json")
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
