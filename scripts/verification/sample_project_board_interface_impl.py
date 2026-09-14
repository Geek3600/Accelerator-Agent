#!/usr/bin/env python3
"""Export and validate exact board-interface facts from a user Vivado project.

Vivado is the sole authority for project structure.  An LLM board-interface
specialist interprets those facts; deterministic code only verifies that every
selected object and contract value is backed by the exported object graph.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


IDENTITY_SCHEMA_VERSION = "spatialaccagent.exact_sample_board_source_identity.v2"
FACT_SCHEMA_VERSION = "spatialaccagent.vivado_sample_project_facts.v1"
INTERPRETATION_SCHEMA_VERSION = "spatialaccagent.board_interface_interpretation.v1"
SELECTION_MAP_SCHEMA_VERSION = "spatialaccagent.board_interface_selection_map.v1"
SELECTION_REDUCE_SCHEMA_VERSION = "spatialaccagent.board_interface_selection_reduce.v1"
DOMAIN_SOURCE_REVIEW_SCHEMA_VERSION = (
    "spatialaccagent.board_interface_source_review.v1"
)
DOMAIN_OUTPUT_CONTRACT_SCHEMA_VERSION = (
    "spatialaccagent.board_interface_domain_output_contract.v1"
)

SELECTOR_MAP_INPUT_BUDGET_BYTES = 320 * 1024
SELECTOR_REDUCE_INPUT_BUDGET_BYTES = 160 * 1024
DOMAIN_SOURCE_MAP_INPUT_BUDGET_BYTES = 480 * 1024
SELECTOR_MAP_CHECKPOINT_SCHEMA_VERSION = (
    "spatialaccagent.board_interface_selection_map_checkpoint.v1"
)
SELECTOR_MAP_CHECKPOINT_NAME = "exact_board_interface_selector_map_checkpoint.json"

SYNTHESIS_ONLY_ROLES = {
    "bd_synth",
    "synth",
    "synthesis",
    "synthesis_only",
    "synthesis_netlist",
    "synth_netlist",
}

AXI_CHANNEL_SIGNALS = {
    "aw": ("id", "addr", "len", "size", "burst", "lock", "cache", "prot", "qos", "region", "user", "valid", "ready"),
    "w": ("data", "strb", "last", "user", "valid", "ready"),
    "b": ("id", "resp", "user", "valid", "ready"),
    "ar": ("id", "addr", "len", "size", "burst", "lock", "cache", "prot", "qos", "region", "user", "valid", "ready"),
    "r": ("id", "data", "resp", "last", "user", "valid", "ready"),
}

AXI_WIDTH_FIELDS = (
    "address_width_bits",
    "data_width_bits",
    "id_width_bits",
    "strb_width_bits",
    "len_width_bits",
    "size_width_bits",
    "burst_width_bits",
    "lock_width_bits",
    "cache_width_bits",
    "prot_width_bits",
    "qos_width_bits",
    "region_width_bits",
    "awuser_width_bits",
    "wuser_width_bits",
    "buser_width_bits",
    "aruser_width_bits",
    "ruser_width_bits",
)

AXI_PARAMETER_EVIDENCE_FIELDS = (
    *AXI_WIDTH_FIELDS,
    "max_burst_length",
    "read_outstanding_limit",
    "write_outstanding_limit",
    "supports_narrow_bursts",
    "supports_unaligned_access",
    "byte_order",
)

CONTROL_SIGNAL_SEMANTICS = {
    "valid": {"pulse", "level"},
    "done": {"pulse", "level", "counter_nonzero", "status_predicate"},
    "start": {"pulse", "level"},
    "clear": {"pulse", "level"},
    "count": {"counter"},
    "status": {"status", "counter"},
}


BOARD_INTERFACE_INTERPRETATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "agent": {"type": "string"},
        "stage": {"type": "string"},
        "status": {"type": "string"},
        "summary": {"type": "string"},
        "wrapper_source_id": {"type": "string"},
        "compute_slot_abi": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "status": {"type": "string"},
                "selected_cell_id": {"type": "string"},
                "slot_module": {"type": "string"},
                "slot_instance_path": {"type": "string"},
                "replacement_module_identity": {"type": "string"},
                "replacement_instance_boundary": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "required_ports": {"type": "array", "items": {"type": "object"}},
                "port_bindings": {"type": "array", "items": {"type": "object"}},
                "interface_classifications": {"type": "array", "items": {"type": "object"}},
                "control_abi": {"type": "object"},
                "replaced_source_ids": {"type": "array", "items": {"type": "string"}},
                "replacement_boundary": {"type": "object"},
                "all_required_ports_bound": {"type": "boolean"},
                "no_behavioral_substitution": {"type": "boolean"},
            },
            "required": [
                "status",
                "selected_cell_id",
                "slot_module",
                "slot_instance_path",
                "replacement_module_identity",
                "replacement_instance_boundary",
                "evidence_refs",
                "required_ports",
                "port_bindings",
                "interface_classifications",
                "control_abi",
                "replaced_source_ids",
                "replacement_boundary",
                "all_required_ports_bound",
                "no_behavioral_substitution",
            ],
        },
        "wrapper_top_module": {"type": "string"},
        "timing_contract": {"type": "object"},
        "axi_interfaces": {"type": "array", "items": {"type": "object"}},
        "blockers": {"type": "array", "items": {"type": "string"}},
        "required_capabilities": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "capability_id": {"type": "string"},
                    "debug_layer": {"type": "string"},
                    "producer_scope": {"type": "string"},
                    "target_modules": {"type": "array", "items": {"type": "string"}},
                    "required_evidence": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "capability_id",
                    "debug_layer",
                    "producer_scope",
                    "target_modules",
                    "required_evidence",
                    "rationale",
                ],
            },
        },
    },
    "required": [
        "schema_version",
        "agent",
        "stage",
        "status",
        "summary",
        "wrapper_source_id",
        "wrapper_top_module",
        "compute_slot_abi",
        "timing_contract",
        "axi_interfaces",
        "blockers",
        "required_capabilities",
    ],
}


BOARD_INTERFACE_SELECTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "agent": {"type": "string"},
        "stage": {"type": "string"},
        "status": {"type": "string"},
        "summary": {"type": "string"},
        "selected_cell_id": {"type": "string"},
        "wrapper_source_id": {"type": "string"},
        "relevant_sample_source_ids": {"type": "array", "items": {"type": "string"}},
        "proposed_replaced_source_ids": {"type": "array", "items": {"type": "string"}},
        "blockers": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "schema_version",
        "agent",
        "stage",
        "status",
        "summary",
        "selected_cell_id",
        "wrapper_source_id",
        "relevant_sample_source_ids",
        "proposed_replaced_source_ids",
        "blockers",
    ],
}


BOARD_INTERFACE_SELECTION_MAP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {
            "type": "string",
            "enum": [SELECTION_MAP_SCHEMA_VERSION],
        },
        "agent": {"type": "string"},
        "stage": {"type": "string"},
        "status": {"type": "string"},
        "summary": {"type": "string"},
        "reviewed_object_ids": {"type": "array", "items": {"type": "string"}},
        "reviewed_source_ids": {"type": "array", "items": {"type": "string"}},
        "candidate_cells": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "cell_id": {"type": "string"},
                    "evidence_object_ids": {"type": "array", "items": {"type": "string"}},
                    "evidence_source_ids": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "cell_id",
                    "evidence_object_ids",
                    "evidence_source_ids",
                    "rationale",
                ],
            },
        },
        "candidate_wrapper_sources": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "source_id": {"type": "string"},
                    "evidence_object_ids": {"type": "array", "items": {"type": "string"}},
                    "evidence_source_ids": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "source_id",
                    "evidence_object_ids",
                    "evidence_source_ids",
                    "rationale",
                ],
            },
        },
        "candidate_relevant_sources": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "source_id": {"type": "string"},
                    "evidence_object_ids": {"type": "array", "items": {"type": "string"}},
                    "evidence_source_ids": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "source_id",
                    "evidence_object_ids",
                    "evidence_source_ids",
                    "rationale",
                ],
            },
        },
        "candidate_replacement_sources": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "source_id": {"type": "string"},
                    "evidence_object_ids": {"type": "array", "items": {"type": "string"}},
                    "evidence_source_ids": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "source_id",
                    "evidence_object_ids",
                    "evidence_source_ids",
                    "rationale",
                ],
            },
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "summary": {"type": "string"},
                    "evidence_object_ids": {"type": "array", "items": {"type": "string"}},
                    "evidence_source_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["summary", "evidence_object_ids", "evidence_source_ids"],
            },
        },
        "blockers": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "schema_version",
        "agent",
        "stage",
        "status",
        "summary",
        "reviewed_object_ids",
        "reviewed_source_ids",
        "candidate_cells",
        "candidate_wrapper_sources",
        "candidate_relevant_sources",
        "candidate_replacement_sources",
        "findings",
        "blockers",
    ],
}


BOARD_INTERFACE_SELECTION_REDUCE_SCHEMA: dict[str, Any] = {
    **BOARD_INTERFACE_SELECTION_MAP_SCHEMA,
    "properties": {
        key: value
        for key, value in BOARD_INTERFACE_SELECTION_MAP_SCHEMA["properties"].items()
        if key not in {"reviewed_object_ids", "reviewed_source_ids"}
    },
    "required": [
        key
        for key in BOARD_INTERFACE_SELECTION_MAP_SCHEMA["required"]
        if key not in {"reviewed_object_ids", "reviewed_source_ids"}
    ],
}


BOARD_INTERFACE_SOURCE_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {
            "type": "string",
            "enum": [DOMAIN_SOURCE_REVIEW_SCHEMA_VERSION],
        },
        "agent": {"type": "string"},
        "stage": {"type": "string"},
        "status": {"type": "string"},
        "summary": {"type": "string"},
        "reviewed_source_ids": {"type": "array", "items": {"type": "string"}},
        "reviewed_segment_ids": {"type": "array", "items": {"type": "string"}},
        "source_summaries": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "source_id": {"type": "string"},
                    "segment_id": {"type": "string"},
                    "sha256": {"type": "string"},
                    "segment_text_sha256": {"type": "string"},
                    "text_encoding": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                    "start_byte": {"type": "integer"},
                    "end_byte": {"type": "integer"},
                    "declared_modules": {"type": "array", "items": {"type": "string"}},
                    "semantic_roles": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": True,
                            "properties": {
                                "category": {"type": "string"},
                                "statement": {"type": "string"},
                                "exact_values": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "evidence_source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "category",
                                "statement",
                                "exact_values",
                                "evidence_source_ids",
                            ],
                        },
                    },
                },
                "required": [
                    "source_id",
                    "segment_id",
                    "sha256",
                    "segment_text_sha256",
                    "text_encoding",
                    "start_line",
                    "end_line",
                    "start_byte",
                    "end_byte",
                    "declared_modules",
                    "semantic_roles",
                    "summary",
                    "findings",
                ],
            },
        },
        "cross_source_findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "category": {"type": "string"},
                    "statement": {"type": "string"},
                    "exact_values": {"type": "array", "items": {"type": "string"}},
                    "evidence_source_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "category",
                    "statement",
                    "exact_values",
                    "evidence_source_ids",
                ],
            },
        },
        "blockers": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "schema_version",
        "agent",
        "stage",
        "status",
        "summary",
        "reviewed_source_ids",
        "reviewed_segment_ids",
        "source_summaries",
        "cross_source_findings",
        "blockers",
    ],
}


SELECTOR_MAP_TASK = (
    "Review every assigned hash-bound Vivado structural/source evidence unit and retain every "
    "plausible sample compute-slot, wrapper, relevant semantic source, and exclusive replacement "
    "source candidate for the global exact-board selector."
)

SELECTOR_MAP_PROMPT_RULES = [
    "You are one map worker in a lossless progressive board-interface selection. Inspect every evidence unit in this chunk; do not skip library/IP, shell, memory, interconnect, control, or user-logic evidence.",
    "Reason from Vivado object properties, interface metadata, net connectivity, compile ownership, hashes, and source provenance. Never select or discard by filename, module-name keyword, target-model name, or a static keyword list.",
    "Return every plausible candidate supported by this chunk, including alternatives. Do not force a global winner; the reduce agent compares all chunks.",
    "Copy assigned_coverage.object_ids and assigned_coverage.source_ids exactly into reviewed_object_ids and reviewed_source_ids after reviewing them. Missing, added, or duplicate IDs fail the deterministic coverage gate.",
    "Cite only IDs present in this chunk. Keep findings concise and evidence-bound; do not copy raw evidence into rationale.",
    "candidate_replacement_sources must be supported as exclusively owned compute-slot implementation sources. Shared shell, DDR, interconnect, testbench, and memory-model sources are not replaceable.",
    "When an assigned source record is a simulation source with owner_cell_ids containing exactly one plausible compute-slot cell, it may be nominated as a candidate_replacement_sources row when the assigned Vivado/source evidence supports an instance-boundary role; this is only a candidate for later full-source module/instance proof, not a final replacement decision. Do not require declared_modules metadata in the map stage when the source text is not assigned.",
    "Discovery stops at the existing sample compute-slot boundary. Never name or design future generated accelerator internals.",
    "Use status=pass after complete review even when this chunk contains no plausible candidate. Use blockers only when assigned evidence is malformed or impossible to review, not merely because the global decision needs other chunks.",
    f"Set schema_version exactly to {SELECTION_MAP_SCHEMA_VERSION}.",
    "Return one JSON object only.",
]


VIVADO_FACT_EXPORT_TCL = r'''# SpatialAccAgent read-only sample-project fact exporter.
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

proc emit_properties {fh bd kind object path} {
  if {[catch {set properties [lsort [list_property $object]]}]} { return }
  foreach property $properties {
    if {[catch {set value [get_property $property $object]}]} { continue }
    emit $fh PROPERTY $bd $kind $path $property $value
  }
}

proc emit_object {fh bd kind object owner} {
  set path [safe_prop $object PATH]
  if {$path eq ""} { set path $object }
  emit $fh OBJECT $bd $kind $path $owner
  emit_properties $fh $bd $kind $object $path
  if {$kind eq "interface_pin" || $kind eq "interface_port"} {
    foreach member [get_bd_pins -quiet -of_objects $object] {
      set member_path [safe_prop $member PATH]
      if {$member_path eq ""} { set member_path $member }
      emit $fh MEMBER $bd $kind $path pin $member_path
    }
    foreach net [get_bd_intf_nets -quiet -of_objects $object] {
      emit $fh NETREF $bd $kind $path interface_net $net
    }
  } else {
    foreach net [get_bd_nets -quiet -of_objects $object] {
      emit $fh NETREF $bd $kind $path net $net
    }
  }
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

if {$argc != 3} {
  error "usage: fact_export.tcl project.xpr manifest.tsv export_directory"
}
set project_path [lindex $argv 0]
set manifest_path [lindex $argv 1]
set export_dir [lindex $argv 2]
set fh [open $manifest_path w]
emit $fh META schema spatialaccagent.vivado_fact_stream.v1
emit $fh META vivado_version [version -short]
emit $fh META project_path $project_path

if {[catch {open_project -read_only $project_path} open_error]} {
  emit $fh META project_open_status fail
  emit $fh META project_open_error $open_error
  close $fh
  exit 2
}
emit $fh META project_open_status pass
emit $fh META part [safe_prop [current_project] PART]

set simsets [get_filesets -quiet -filter {FILESET_TYPE == SimulationSrcs}]
if {[llength $simsets] != 1} {
  emit $fh META simulation_fileset_status fail
  emit $fh META simulation_fileset_count [llength $simsets]
  close $fh
  exit 3
}
set simset [lindex $simsets 0]
emit $fh META simulation_fileset_status pass
emit $fh META simulation_fileset $simset
emit $fh META top_module [safe_prop $simset TOP]
foreach property [lsort [list_property $simset]] {
  if {[catch {set value [get_property $property $simset]}]} { continue }
  emit $fh FILESET_PROPERTY $property $value
}

if {[catch {update_compile_order -fileset $simset} compile_error]} {
  emit $fh META compile_order_status fail
  emit $fh META compile_order_error $compile_error
  close $fh
  exit 4
}
emit $fh META compile_order_status pass
set sources [get_files -compile_order sources -used_in simulation -of_objects $simset]
emit $fh META compile_source_count [llength $sources]
set order 0
foreach source $sources {
  emit $fh SOURCE $order $source
  foreach property [lsort [list_property $source]] {
    if {[catch {set value [get_property $property $source]}]} { continue }
    emit $fh SOURCE_PROPERTY $order $property $value
  }
  incr order
}

set compile_report ""
set compile_report_path "${manifest_path}.compile_order"
if {[catch {report_compile_order -sources -used_in simulation -of_objects $simset -file $compile_report_path} report_error]} {
  emit $fh META compile_report_status fail
  emit $fh META compile_report_error $report_error
} else {
  set report_fh [open $compile_report_path r]
  set compile_report [read $report_fh]
  close $report_fh
  file delete -force $compile_report_path
  emit $fh META compile_report_status pass
  emit $fh COMPILE_REPORT $compile_report
}
set missing_report ""
set missing_report_path "${manifest_path}.missing_instances"
if {[catch {report_compile_order -missing_instances -used_in simulation -of_objects $simset -file $missing_report_path} missing_error]} {
  emit $fh META missing_instance_report_status fail
  emit $fh META missing_instance_report_error $missing_error
} else {
  set report_fh [open $missing_report_path r]
  set missing_report [read $report_fh]
  close $report_fh
  file delete -force $missing_report_path
  emit $fh META missing_instance_report_status pass
  emit $fh MISSING_REPORT $missing_report
}

file mkdir $export_dir
if {[catch {export_simulation -simulator vcs -of_objects $simset -directory $export_dir -absolute_path -force} export_error]} {
  emit $fh META simulator_export_status fail
  emit $fh META simulator_export_error $export_error
} else {
  emit $fh META simulator_export_status pass
  foreach path [lsort [walk_files $export_dir]] {
    emit $fh EXPORT_FILE $path [file size $path]
  }
}

set bd_files [get_files -quiet -filter {FILE_TYPE == "Block Designs"}]
emit $fh META block_design_count [llength $bd_files]
foreach bd_file $bd_files {
  set open_error ""
  set open_code [catch {open_bd_design $bd_file} open_error]
  set design ""
  catch {set design [current_bd_design]}
  set cells [get_bd_cells -quiet -hier]
  set bd_status [expr {[llength $cells] > 0 ? "pass" : "fail"}]
  emit $fh BD $bd_file $design $bd_status $open_code $open_error

  foreach port [get_bd_ports -quiet] { emit_object $fh $bd_file port $port "" }
  foreach intf [get_bd_intf_ports -quiet] { emit_object $fh $bd_file interface_port $intf "" }
  foreach cell $cells {
    set cell_path [safe_prop $cell PATH]
    if {$cell_path eq ""} { set cell_path $cell }
    emit_object $fh $bd_file cell $cell ""
    foreach pin [get_bd_pins -quiet -of_objects $cell] {
      emit_object $fh $bd_file pin $pin $cell_path
    }
    foreach intf [get_bd_intf_pins -quiet -of_objects $cell] {
      emit_object $fh $bd_file interface_pin $intf $cell_path
    }

    set component [safe_prop $cell CONFIG.Component_Name]
    if {$component ne ""} {
      set ips [get_ips -all -quiet $component]
      foreach ip $ips {
        if {[catch {set ip_sources [get_files -compile_order sources -used_in simulation -of_objects $ip]}]} { continue }
        foreach source $ip_sources { emit $fh CELL_SOURCE $bd_file $cell_path $component $source }
      }
    }
  }
  foreach net [get_bd_nets -quiet] {
    emit_object $fh $bd_file net $net ""
    foreach endpoint [get_bd_pins -quiet -of_objects $net] {
      set endpoint_path [safe_prop $endpoint PATH]
      if {$endpoint_path eq ""} { set endpoint_path $endpoint }
      emit $fh NET_MEMBER $bd_file net $net pin $endpoint_path
    }
  }
  foreach net [get_bd_intf_nets -quiet] {
    emit_object $fh $bd_file interface_net $net ""
    foreach endpoint [get_bd_intf_pins -quiet -of_objects $net] {
      set endpoint_path [safe_prop $endpoint PATH]
      if {$endpoint_path eq ""} { set endpoint_path $endpoint }
      emit $fh NET_MEMBER $bd_file interface_net $net interface_pin $endpoint_path
    }
  }
  catch {close_bd_design $design}
}

emit $fh META fact_export_status pass
close $fh
close_project
exit 0
'''


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_bytes(payload.encode("utf-8"))


def board_interface_domain_output_contract() -> dict[str, Any]:
    """Describe the exact generic shape consumed by deterministic board gates."""

    signal_fact_map = {
        channel: {
            signal: "{port_id: Vivado member pin ID} or evidence-proved {constant: value}/{absent: true}"
            for signal in signals
        }
        for channel, signals in AXI_CHANNEL_SIGNALS.items()
    }
    return {
        "schema_version": DOMAIN_OUTPUT_CONTRACT_SCHEMA_VERSION,
        "top_level": {
            "required_fields": [
                "schema_version",
                "agent",
                "stage",
                "status",
                "summary",
                "wrapper_source_id",
                "wrapper_top_module",
                "compute_slot_abi",
                "timing_contract",
                "axi_interfaces",
                "blockers",
                "required_capabilities",
            ],
            "passing_values": {"status": ["pass", "ready"], "blockers": []},
            "wrapper_rule": (
                "wrapper_source_id is in the immutable sample closure and directly declares "
                "wrapper_top_module"
            ),
            "blocked_capability_handoff": {
                "rule": (
                    "status=blocked requires one nonempty request per missing immutable evidence class; "
                    "status=pass/ready requires an empty required_capabilities array"
                ),
                "item_required_fields": [
                    "capability_id",
                    "debug_layer",
                    "producer_scope",
                    "target_modules",
                    "required_evidence",
                    "rationale",
                ],
            },
        },
        "compute_slot_abi": {
            "required_fields": BOARD_INTERFACE_INTERPRETATION_SCHEMA["properties"]
            ["compute_slot_abi"]["required"],
            "identity_rules": {
                "selected_cell_id": "exact Vivado cell object_id",
                "slot_module": "exact selected-cell CONFIG.Component_Name",
                "slot_instance_path": "exact selected-cell Vivado path, not an HDL hierarchy path",
                "replacement_module_identity": "exactly slot_module",
                "replacement_instance_boundary": "exactly slot_instance_path",
                "status": "pass",
                "all_required_ports_bound": True,
                "no_behavioral_substitution": (
                    "true when the exclusive existing slot boundary is preserved and all real sample "
                    "wrapper/AXI/DDR/clock/reset/calibration behavior remains retained; discovery does "
                    "not require a future generated kernel to already be instantiated"
                ),
            },
            "required_ports": {
                "coverage": "exactly one item for every physical pin owned by the selected cell",
                "item_required_fields": [
                    "fact_port_id",
                    "name",
                    "direction",
                    "width_bits",
                    "semantic_role",
                    "evidence_refs",
                ],
            },
            "port_bindings": {
                "coverage": "exactly one item for every physical pin owned by the selected cell",
                "item_required_fields": [
                    "port_id",
                    "accelerator_port",
                    "direction",
                    "width_bits",
                    "evidence_refs",
                ],
                "accelerator_port_rule": (
                    "nonempty proposed external port name for the later generation agent; do not claim "
                    "that generated RTL already exists"
                ),
            },
            "interface_classifications": {
                "coverage": "exactly one item for every selected-cell interface pin",
                "item_required_fields": [
                    "interface_id",
                    "fact_protocol",
                    "contract_kind",
                    "evidence_refs",
                ],
                "axi4_contract_kind": "axi4_full",
            },
            "replacement_boundary": {
                "replaced_source_ids": (
                    "nonempty exclusive selected-cell source IDs from the immutable sample closure"
                ),
                "required_fields": [
                    "selected_cell_id",
                    "retained_source_ids",
                    "sample_closure_unchanged",
                    "generated_sources_excluded_from_sample_closure",
                    "source_module_evidence",
                ],
                "source_module_evidence_item_fields": [
                    "source_id",
                    "source_sha256",
                    "declared_modules",
                ],
                "retained_rule": "complete sample closure minus replaced_source_ids",
            },
        },
        "timing_contract": {
            "clock_domains": {
                "container": "list",
                "coverage": "exactly every selected-cell Vivado clock pin",
                "value_rules": {
                    "frequency_hz": "exact integer CONFIG.FREQ_HZ from the bound Vivado clock pin",
                    "period_ps": "round(1000000000000 / frequency_hz) as an integer",
                    "phase_ps": "round(period_ps * CONFIG.PHASE / 360) as an integer",
                    "source": {
                        "allowed_values": ["exact_sample_project", "exact_sample_ip"],
                        "rule": "source is a provenance class, not a Vivado object ID; cite IDs in evidence_refs",
                    },
                },
                "item_required_fields": [
                    "fact_port_id",
                    "name",
                    "frequency_hz",
                    "period_ps",
                    "phase_ps",
                    "source",
                    "duty_cycle_percent",
                    "evidence_refs",
                ],
            },
            "resets": {
                "container": "list",
                "coverage": "exactly every selected-cell Vivado reset pin",
                "value_rules": {
                    "source": {
                        "allowed_values": ["exact_sample_project", "exact_sample_ip"],
                        "rule": "source is a provenance class, not an evidence ID",
                    },
                    "deassertion_edge": {"allowed_values": ["rising", "falling"]},
                },
                "item_required_fields": [
                    "fact_port_id",
                    "name",
                    "active_level",
                    "clock_domain",
                    "minimum_assert_cycles",
                    "deassertion_edge",
                    "source",
                    "timing_source_id",
                    "evidence_refs",
                ],
            },
            "calibration": {
                "container": "nonempty list",
                "value_rules": {
                    "source": {
                        "allowed_values": ["exact_sample_memory_model", "exact_sample_ip"],
                        "rule": "source is a provenance class, not a Vivado object ID; cite the driver in driver_object_id",
                    }
                },
                "item_required_fields": [
                    "fact_port_id",
                    "name",
                    "driver_object_id",
                    "gates_axi_traffic",
                    "active_level",
                    "source",
                    "clock_domain",
                    "evidence_refs",
                ],
            },
            "startup_sequence": {
                "container": "ordered list",
                "required_events": [
                    "assert_reset",
                    "release_reset",
                    "wait_calibration",
                    "enable_axi_traffic",
                ],
                "item_required_fields": ["event", "order", "evidence_refs"],
            },
            "memory_timing_model_required_fields": [
                "source_ids",
                "parameters_bound_from_sample_project",
                "synthetic_fixed_latency",
            ],
            "other_required_fields": [
                "timescale",
                "timeprecision",
                "timescale_source_id",
                "exact_sample_timing",
            ],
        },
        "control_abi": {
            "required_fields": [
                "status",
                "all_non_interface_ports_classified",
                "clock_domain",
                "port_classifications",
                "control_ports",
                "configuration_buses",
                "configuration_fields",
                "signals",
                "timing",
                "control_sequence_enforcement",
                "control_sequence",
            ],
            "port_classifications": {
                "coverage": "exactly every selected-cell pin that is not an interface member",
                "item_required_fields": [
                    "fact_port_id",
                    "name",
                    "direction",
                    "width_bits",
                    "classification",
                    "semantic_role",
                    "pulse_or_level",
                    "clock_domain",
                    "evidence_object_ids",
                    "evidence_source_ids",
                ],
            },
            "control_ports": (
                "exact projection of configuration_bus/control/status/calibration classifications; "
                "each item repeats fact_port_id, semantic_role, direction, width_bits, pulse_or_level, "
                "and clock_domain, and every repeated value exactly equals the matching port_classifications item"
            ),
            "configuration_buses": {
                "coverage": "exactly the configuration_bus classifications",
                "item_required_fields": ["fact_port_id", "fields"],
                "field_required_fields": [
                    "lsb",
                    "msb",
                    "semantic_role",
                    "evidence_source_id",
                ],
            },
            "configuration_fields": {
                "coverage": "exact projection of every configuration_buses field",
                "item_required_fields": [
                    "fact_port_id",
                    "field_id",
                    "register",
                    "width_bits",
                    "bit_offset",
                    "access",
                    "reset_value",
                ],
            },
            "signals": {
                "required_roles": ["valid", "done", "start", "clear", "count", "status"],
                "physical_item_required_fields": [
                    "binding_kind",
                    "fact_port_id",
                    "name",
                    "direction",
                    "width_bits",
                    "semantic",
                    "clock_domain",
                ],
                "physical_binding_kind": "physical_port",
                "derived_done": {
                    "binding_kind": "derived_from_physical_port",
                    "allowed_semantics": ["counter_nonzero", "status_predicate"],
                    "required_fields": [
                        "fact_port_id",
                        "name",
                        "direction",
                        "width_bits",
                        "semantic",
                        "clock_domain",
                        "derived_from_role",
                        "predicate",
                        "evidence_object_ids",
                        "evidence_source_ids",
                    ],
                    "rule": (
                        "only done may be derived; derived_from_role is count or status, that physical "
                        "role uses the same fact_port_id, and predicate is proved by supplied sources"
                    ),
                },
            },
            "timing_required_fields": [
                "start_assertion_cycles",
                "clear_assertion_cycles",
                "start_sampling_edge",
                "clear_sampling_edge",
                "start_accept_condition",
                "done_relation_to_valid",
                "done_clear_condition",
                "count_update_event",
                "status_update_event",
                "evidence_refs",
            ],
            "control_sequence": {
                "container": "ordered list, never an object containing steps",
                "enforcement_values": ["hardware", "external_orchestrator", "mixed"],
                "required_events": [
                    "configure",
                    "start",
                    "observe_completion",
                    "clear_completion",
                ],
                "item_required_fields": [
                    "event",
                    "order",
                    "fact_port_ids",
                    "evidence_source_ids",
                ],
                "external_orchestrator_rule": (
                    "an exact software/testbench-controlled order is the real operational contract and "
                    "is not a blocker when every action and observation is source-evidenced"
                ),
            },
        },
        "axi_interfaces": {
            "coverage": "exactly every interface classified axi4_full",
            "item_required_fields": [
                "fact_interface_id",
                "name",
                "protocol",
                "role",
                "clock",
                "reset",
                "calibration",
                *AXI_WIDTH_FIELDS,
                "max_burst_length",
                "read_outstanding_limit",
                "write_outstanding_limit",
                "supports_narrow_bursts",
                "supports_unaligned_access",
                "byte_order",
                "parameter_evidence_refs",
                "signal_evidence_refs",
                "signal_fact_map",
            ],
            "byte_order_values": [
                "little",
                "big",
                "physical_byte_lane_order_preserved",
            ],
            "signal_fact_map": signal_fact_map,
        },
        "evidence_rule": (
            "Use only exact Vivado object_ids and hash-bound sample source_ids supplied in the request. "
            "Never invent an identifier or infer a value from a name alone."
        ),
    }


def command_timeout(timeout: int) -> int | None:
    return timeout if timeout > 0 else None


def ssh_prefix(host: str, port: int) -> list[str]:
    prefix = ["ssh"]
    if port and port != 22:
        prefix.extend(["-p", str(port)])
    prefix.append(host)
    return prefix


def scp_prefix(port: int) -> list[str]:
    prefix = ["scp"]
    if port and port != 22:
        prefix.extend(["-P", str(port)])
    return prefix


def run_checked(
    argv: list[str],
    timeout: int,
    *,
    input_bytes: bytes | None = None,
    stdout: Any = subprocess.PIPE,
) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(
        argv,
        input=input_bytes,
        stdout=stdout,
        stderr=subprocess.PIPE,
        timeout=command_timeout(timeout),
        check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")[-4000:]
        raise RuntimeError(f"command failed ({proc.returncode}): {shlex.join(argv)}: {stderr}")
    return proc


def remote_exec(host: str, port: int, argv: list[str], timeout: int) -> bytes:
    command = shlex.join(argv)
    return run_checked([*ssh_prefix(host, port), command], timeout).stdout


def remote_read(host: str, path: str, timeout: int, port: int = 22) -> bytes:
    return remote_exec(host, port, ["cat", path], timeout)


def source_bytes(host: str, path: str, timeout: int, port: int = 22) -> bytes:
    local = Path(path)
    return local.read_bytes() if local.is_file() else remote_read(host, path, timeout, port)


def _tool_profile_vivado(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "input" / "tool_profile.json"
    if not path.is_file():
        raise ValueError("current run does not contain input/tool_profile.json")
    profile = read_json(path)
    candidates = []
    for row in profile.get("tools", []):
        if not isinstance(row, dict) or not row.get("executable"):
            continue
        name = str(row.get("name") or "").strip().lower()
        role = str(row.get("role") or "").strip().lower()
        if name == "vivado" or role == "synthesis_implementation_bitstream_generation":
            candidates.append(row)
    if len(candidates) != 1:
        raise ValueError(f"current tool profile must identify exactly one Vivado tool, found {len(candidates)}")
    if not str(candidates[0].get("host") or "").strip():
        raise ValueError("current tool profile Vivado row does not declare its host")
    if not candidates[0].get("port"):
        raise ValueError("current tool profile Vivado row does not declare its port")
    return candidates[0]


def project_inputs(run_dir: Path) -> dict[str, Any]:
    profile = read_json(run_dir / "input" / "target_board_profile.json")
    index_path = run_dir / "input" / "sample_project_index.json"
    index = read_json(index_path) if index_path.is_file() else {}
    tool = _tool_profile_vivado(run_dir)
    shell = profile.get("shell", {}) if isinstance(profile.get("shell"), dict) else {}
    candidates: list[tuple[str, str, int]] = []
    for sample in index.get("samples", []):
        if not isinstance(sample, dict) or sample.get("status") != "ok":
            continue
        source_path = str(sample.get("source_path") or "").strip()
        if Path(source_path).suffix.lower() != ".xpr":
            continue
        candidates.append(
            (
                source_path,
                str(sample.get("host") or "").strip(),
                int(sample.get("port") or 0),
            )
        )
    unique: dict[str, tuple[str, str, int]] = {row[0]: row for row in candidates}
    if len(unique) != 1:
        raise ValueError(f"current board inputs must identify exactly one Vivado .xpr, found {sorted(unique)}")
    xpr_path, indexed_host, indexed_port = next(iter(unique.values()))
    profile_xpr = str(shell.get("vivado_project_path") or "").strip()
    if profile_xpr and profile_xpr != xpr_path:
        raise ValueError("target board profile XPR conflicts with the current sample-project index")
    host = str(tool.get("host") or "").strip()
    port = int(tool.get("port") or 0)
    if indexed_host and indexed_host != host:
        raise ValueError("Vivado tool host conflicts with the current sample-project host")
    if indexed_port and indexed_port != port:
        raise ValueError("Vivado tool port conflicts with the current sample-project port")
    return {
        "profile": profile,
        "index": index,
        "tool": tool,
        "host": host,
        "port": port,
        "xpr_path": xpr_path,
        "vivado_executable": str(tool["executable"]),
        "configured_vivado_version": tool.get("version"),
    }


def _decode_fact_field(value: str) -> str:
    try:
        return bytes.fromhex(value).decode("utf-8")
    except Exception as exc:
        raise ValueError("Vivado fact stream contains an invalid UTF-8 hex field") from exc


def _fact_id(kind: str, bd_path: str, object_path: str) -> str:
    return f"vivado:{kind}:{canonical_sha256([bd_path, object_path])[:24]}"


def _source_id(path: str, properties: dict[str, str]) -> str:
    identity = [path, properties.get("LIBRARY", ""), properties.get("PARENT_COMPOSITE_FILE", "")]
    return f"sample-source:{canonical_sha256(identity)[:24]}"


def _parse_missing_instances(report: str) -> tuple[list[dict[str, str]], list[str]]:
    lines = [line.rstrip() for line in report.splitlines()]
    separator = next((index for index, line in enumerate(lines) if line.strip() and set(line.replace(" ", "")) == {"-"}), None)
    if separator is None:
        return [], ["Vivado missing-instance report format was not recognized"]
    body = [line.strip() for line in lines[separator + 1 :] if line.strip()]
    if body == ["< empty >"]:
        return [], []
    if not body:
        return [], ["Vivado missing-instance report has no explicit empty marker or instance rows"]
    return [{"vivado_report_row": line} for line in body], []


def parse_vivado_fact_stream(raw: bytes) -> dict[str, Any]:
    metadata: dict[str, str] = {}
    fileset_properties: dict[str, str] = {}
    source_rows: dict[int, dict[str, Any]] = {}
    bd_rows: dict[str, dict[str, Any]] = {}
    objects: dict[tuple[str, str, str], dict[str, Any]] = {}
    cell_source_paths: dict[tuple[str, str], set[str]] = {}
    compile_report = ""
    missing_report = ""
    export_files: list[dict[str, Any]] = []

    for number, raw_line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        parts = raw_line.split("\t")
        tag = parts[0]
        values = [_decode_fact_field(value) for value in parts[1:]]
        try:
            if tag == "META":
                metadata[values[0]] = values[1]
            elif tag == "FILESET_PROPERTY":
                fileset_properties[values[0]] = values[1]
            elif tag == "SOURCE":
                order = int(values[0])
                source_rows[order] = {"compile_order": order, "remote_path": values[1], "properties": {}}
            elif tag == "SOURCE_PROPERTY":
                source_rows[int(values[0])]["properties"][values[1]] = values[2]
            elif tag == "COMPILE_REPORT":
                compile_report = values[0]
            elif tag == "MISSING_REPORT":
                missing_report = values[0]
            elif tag == "EXPORT_FILE":
                export_files.append({"remote_path": values[0], "size_bytes": int(values[1])})
            elif tag == "BD":
                bd_rows[values[0]] = {
                    "remote_path": values[0],
                    "design_name": values[1],
                    "status": values[2],
                    "open_returncode": int(values[3]),
                    "open_diagnostic": values[4],
                }
            elif tag == "OBJECT":
                bd_path, kind, path, owner = values
                objects[(bd_path, kind, path)] = {
                    "kind": kind,
                    "bd_path": bd_path,
                    "path": path,
                    "owner_path": owner,
                    "properties": {},
                    "connected_nets": [],
                    "members": [],
                }
            elif tag == "PROPERTY":
                bd_path, kind, path, prop, value = values
                objects[(bd_path, kind, path)]["properties"][prop] = value
            elif tag == "NETREF":
                bd_path, kind, path, net_kind, net_path = values
                objects[(bd_path, kind, path)]["connected_nets"].append(
                    {"kind": net_kind, "path": net_path}
                )
            elif tag == "MEMBER":
                bd_path, kind, path, member_kind, member_path = values
                objects[(bd_path, kind, path)]["members"].append(
                    {"kind": member_kind, "path": member_path}
                )
            elif tag == "NET_MEMBER":
                bd_path, net_kind, net_path, member_kind, member_path = values
                key = (bd_path, net_kind, net_path)
                if key in objects:
                    objects[key]["members"].append({"kind": member_kind, "path": member_path})
            elif tag == "CELL_SOURCE":
                bd_path, cell_path, _component, source_path = values
                cell_source_paths.setdefault((bd_path, cell_path), set()).add(source_path)
            else:
                raise ValueError(f"unknown record type {tag}")
        except (IndexError, KeyError, ValueError) as exc:
            raise ValueError(f"malformed Vivado fact record at line {number}: {tag}") from exc

    if metadata.get("schema") != "spatialaccagent.vivado_fact_stream.v1":
        raise ValueError("Vivado fact stream schema is missing or unsupported")
    normalized_sources: list[dict[str, Any]] = []
    source_by_path: dict[str, dict[str, Any]] = {}
    for order in sorted(source_rows):
        row = source_rows[order]
        props = row["properties"]
        normalized = {
            "source_id": _source_id(row["remote_path"], props),
            "remote_path": row["remote_path"],
            "compile_order": order,
            "library": props.get("LIBRARY", ""),
            "file_type": props.get("FILE_TYPE", ""),
            "file_set": props.get("FILESET_NAME", ""),
            "used_in": props.get("USED_IN", "").split(),
            "is_generated": props.get("IS_GENERATED", "").lower() in {"1", "true"},
            "is_global_include": props.get("IS_GLOBAL_INCLUDE", "").lower() in {"1", "true"},
            "parent_composite_file": props.get("PARENT_COMPOSITE_FILE", ""),
            "properties": props,
            "owner_cell_ids": [],
        }
        normalized_sources.append(normalized)
        source_by_path[row["remote_path"]] = normalized

    normalized_objects = []
    object_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for key in sorted(objects):
        row = objects[key]
        row["connected_nets"] = sorted(
            row.get("connected_nets", []),
            key=lambda value: (str(value.get("kind") or ""), str(value.get("path") or "")),
        )
        row["members"] = sorted(
            row.get("members", []),
            key=lambda value: (str(value.get("kind") or ""), str(value.get("path") or "")),
        )
        row["object_id"] = _fact_id(row["kind"], row["bd_path"], row["path"])
        object_by_key[key] = row
        normalized_objects.append(row)
    for (bd_path, cell_path), paths in cell_source_paths.items():
        cell = object_by_key.get((bd_path, "cell", cell_path))
        if not cell:
            continue
        source_ids = []
        for path in sorted(paths):
            source = source_by_path.get(path)
            if not source:
                continue
            source_ids.append(source["source_id"])
            source["owner_cell_ids"].append(cell["object_id"])
        cell["simulation_source_ids"] = source_ids
    for source in normalized_sources:
        source["owner_cell_ids"] = sorted(set(source["owner_cell_ids"]))

    unresolved, missing_parse_blockers = _parse_missing_instances(missing_report)
    blockers = list(missing_parse_blockers)
    required_meta = {
        "project_open_status": "pass",
        "simulation_fileset_status": "pass",
        "compile_order_status": "pass",
        "compile_report_status": "pass",
        "missing_instance_report_status": "pass",
        "simulator_export_status": "pass",
        "fact_export_status": "pass",
    }
    for field, expected in required_meta.items():
        if metadata.get(field) != expected:
            blockers.append(f"Vivado fact export {field} is not {expected}: {metadata.get(field)!r}")
    if not metadata.get("top_module"):
        blockers.append("Vivado simulation fileset does not declare a top module")
    if not normalized_sources:
        blockers.append("Vivado returned an empty simulation compile order")
    if not bd_rows or not any(row.get("status") == "pass" for row in bd_rows.values()):
        blockers.append("Vivado did not export a readable block-design object graph")
    if unresolved:
        blockers.append(f"Vivado reports unresolved module instances: {unresolved}")

    return {
        "schema_version": FACT_SCHEMA_VERSION,
        "status": "pass" if not blockers else "fail",
        "project": {
            "path": metadata.get("project_path"),
            "part": metadata.get("part"),
            "top_module": metadata.get("top_module"),
            "vivado_version": metadata.get("vivado_version"),
            "simulation_fileset": metadata.get("simulation_fileset"),
        },
        "simulation": {
            "source_files": normalized_sources,
            "fileset_properties": fileset_properties,
            "compile_order_report": compile_report,
            "missing_instances_report": missing_report,
            "unresolved_dependencies": unresolved,
            "recursive_dependency_scan_complete": not blockers and not unresolved,
            "duplicate_module_definitions": [],
            "external_library_dependencies": [],
            "simulator_export_files": export_files,
        },
        "block_designs": list(bd_rows.values()),
        "objects": normalized_objects,
        "metadata": metadata,
        "blockers": blockers,
    }


def _read_export_contexts(
    facts: dict[str, Any], host: str, port: int, timeout: int
) -> list[dict[str, Any]]:
    contexts = []
    text_suffixes = {".sh", ".tcl", ".do", ".f", ".prj", ".setup", ".cfg"}
    for row in facts.get("simulation", {}).get("simulator_export_files", []):
        path = str(row.get("remote_path") or "")
        size = int(row.get("size_bytes") or 0)
        if Path(path).suffix.lower() not in text_suffixes or size > 2 * 1024 * 1024:
            continue
        try:
            raw = source_bytes(host, path, timeout, port)
        except Exception as exc:
            row["read_error"] = str(exc)
            continue
        row["sha256"] = sha256_bytes(raw)
        contexts.append(
            {
                "remote_path": path,
                "sha256": row["sha256"],
                "text": raw.decode("utf-8", errors="replace"),
            }
        )
    return contexts


def run_vivado_fact_export(inputs: dict[str, Any], out_dir: Path, timeout: int) -> dict[str, Any]:
    host = str(inputs["host"])
    port = int(inputs["port"])
    xpr_path = str(inputs["xpr_path"])
    executable = str(inputs["vivado_executable"])
    out_dir.mkdir(parents=True, exist_ok=True)
    local_tcl = out_dir / "vivado_board_fact_export.tcl"
    local_tcl.write_text(VIVADO_FACT_EXPORT_TCL, encoding="utf-8")
    stdout_path = out_dir / "vivado_board_fact_export.stdout.log"

    if host:
        token = canonical_sha256([xpr_path, os.getpid()])[:16]
        remote_dir = remote_exec(
            host,
            port,
            ["mktemp", "-d", f"/tmp/spatialaccagent_board_{token}_XXXXXX"],
            timeout,
        ).decode("utf-8", errors="replace").strip()
        if not remote_dir:
            raise RuntimeError("remote mktemp returned an empty directory")
        remote_tcl = f"{remote_dir}/fact_export.tcl"
        remote_manifest = f"{remote_dir}/facts.tsv"
        remote_export = f"{remote_dir}/vcs_export"
        try:
            run_checked(
                [*scp_prefix(port), str(local_tcl), f"{host}:{remote_tcl}"],
                timeout,
            )
            proc = subprocess.run(
                [
                    *ssh_prefix(host, port),
                    shlex.join(
                        [
                            executable,
                            "-mode",
                            "batch",
                            "-notrace",
                            "-nolog",
                            "-nojournal",
                            "-source",
                            remote_tcl,
                            "-tclargs",
                            xpr_path,
                            remote_manifest,
                            remote_export,
                        ]
                    ),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=command_timeout(timeout),
                check=False,
            )
            stdout_path.write_bytes(proc.stdout)
            manifest_raw = remote_read(host, remote_manifest, timeout, port)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"Vivado fact export failed ({proc.returncode}); log={stdout_path}; "
                    f"tail={proc.stdout.decode('utf-8', errors='replace')[-4000:]}"
                )
            facts = parse_vivado_fact_stream(manifest_raw)
            facts["simulation"]["simulator_export_contexts"] = _read_export_contexts(
                facts, host, port, timeout
            )
            return facts
        finally:
            try:
                remote_exec(host, port, ["rm", "-rf", remote_dir], timeout)
            except Exception:
                pass

    with tempfile.TemporaryDirectory(prefix="spatialaccagent_board_") as temp_dir:
        manifest = Path(temp_dir) / "facts.tsv"
        export_dir = Path(temp_dir) / "vcs_export"
        proc = subprocess.run(
            [
                executable,
                "-mode",
                "batch",
                "-notrace",
                "-nolog",
                "-nojournal",
                "-source",
                str(local_tcl),
                "-tclargs",
                xpr_path,
                str(manifest),
                str(export_dir),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=command_timeout(timeout),
            check=False,
        )
        stdout_path.write_bytes(proc.stdout)
        if not manifest.is_file() or proc.returncode != 0:
            raise RuntimeError(f"local Vivado fact export failed ({proc.returncode}); log={stdout_path}")
        facts = parse_vivado_fact_stream(manifest.read_bytes())
        facts["simulation"]["simulator_export_contexts"] = _read_export_contexts(
            facts, "", port, timeout
        )
        return facts


def _fetch_source_payloads(
    host: str, port: int, paths: Iterable[str], timeout: int
) -> dict[str, bytes]:
    requested = list(dict.fromkeys(str(path) for path in paths))
    result: dict[str, bytes] = {}
    remote_paths = []
    for path in requested:
        local = Path(path)
        if local.is_file():
            result[path] = local.read_bytes()
        else:
            remote_paths.append(path)
    if not remote_paths:
        return result
    if not host:
        raise RuntimeError(f"simulation sources are not local: {remote_paths[:3]}")

    with tempfile.NamedTemporaryFile(prefix="spatialaccagent_sources_", suffix=".tar") as archive:
        proc = subprocess.run(
            [*ssh_prefix(host, port), shlex.join(["tar", "--dereference", "--null", "-T", "-", "-c", "-f", "-"])],
            input=b"\0".join(path.encode("utf-8") for path in remote_paths) + b"\0",
            stdout=archive,
            stderr=subprocess.PIPE,
            timeout=command_timeout(timeout),
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "cannot snapshot Vivado simulation closure: "
                + proc.stderr.decode("utf-8", errors="replace")[-4000:]
            )
        archive.flush()
        archive.seek(0)
        with tarfile.open(fileobj=archive, mode="r:") as stream:
            by_name = {member.name.lstrip("/"): member for member in stream.getmembers() if member.isfile()}
            for path in remote_paths:
                member = by_name.get(path.lstrip("/"))
                if member is None:
                    raise RuntimeError(f"remote source snapshot omitted {path}")
                extracted = stream.extractfile(member)
                if extracted is None:
                    raise RuntimeError(f"remote source snapshot cannot read {path}")
                result[path] = extracted.read()
    return result


def _source_role(row: dict[str, Any]) -> str:
    if row.get("is_global_include"):
        return "global_include"
    return "simulation_source"


def _safe_staged_name(order: int, source_id: str, remote_path: str) -> str:
    name = Path(remote_path).name or "source"
    return f"{order:04d}_{source_id.rsplit(':', 1)[-1][:12]}_{name}"


def materialize_simulation_sources(
    facts: dict[str, Any], host: str, port: int, out_dir: Path, timeout: int
) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    source_facts = facts.get("simulation", {}).get("source_files", [])
    paths = [str(row.get("remote_path") or "") for row in source_facts]
    if any(not path for path in paths):
        return [], ["Vivado compile order contains a source without a path"]
    try:
        payloads = _fetch_source_payloads(host, port, paths, timeout)
    except Exception as exc:
        return [], [str(exc)]

    staged_dir = out_dir / "sample_project_sources"
    rows = []
    for source in source_facts:
        remote_path = str(source["remote_path"])
        raw = payloads[remote_path]
        source_id = str(source["source_id"])
        local_path = staged_dir / _safe_staged_name(
            int(source.get("compile_order") or 0), source_id, remote_path
        )
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(raw)
        digest = sha256_bytes(raw)
        local_digest = sha256_bytes(local_path.read_bytes())
        role = _source_role(source)
        used_in = [str(value).lower() for value in source.get("used_in", [])]
        if role in SYNTHESIS_ONLY_ROLES or (used_in and "simulation" not in used_in):
            blockers.append(f"Vivado selected a synthesis-only file in the simulation closure: {remote_path}")
        rows.append(
            {
                "source_id": source_id,
                "role": role,
                "source_set": "simulation",
                "remote_path": remote_path,
                "local_path": str(local_path),
                "path": str(local_path),
                "staged_path": str(local_path.relative_to(out_dir)),
                "sha256": digest,
                "remote_sha256": digest,
                "local_sha256": local_digest,
                "hashes_match": digest == local_digest,
                "size_bytes": len(raw),
                "compile_order": source.get("compile_order"),
                "library": source.get("library"),
                "language": source.get("file_type"),
                "file_type": source.get("file_type"),
                "file_set": source.get("file_set"),
                "used_in": source.get("used_in", []),
                "parent_composite_file": source.get("parent_composite_file"),
                "owner_cell_ids": source.get("owner_cell_ids", []),
                "dependencies": [],
                "declared_modules": [],
            }
        )
        if digest != local_digest:
            blockers.append(f"source changed during materialization: {remote_path}")
    return rows, blockers


def recover_staged_simulation_sources(
    facts: dict[str, Any], out_dir: Path
) -> tuple[list[dict[str, Any]], list[str]]:
    """Rebuild source metadata only from an intact hash-bound staging area."""

    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for source in facts.get("simulation", {}).get("source_files", []):
        if not isinstance(source, dict):
            blockers.append("Vivado simulation closure contains a malformed source fact")
            continue
        source_id = str(source.get("source_id") or "")
        remote_path = str(source.get("remote_path") or "")
        if not source_id or not remote_path:
            blockers.append("Vivado simulation closure contains a source without stable identity/path")
            continue
        local_path = out_dir / "sample_project_sources" / _safe_staged_name(
            int(source.get("compile_order") or 0), source_id, remote_path
        )
        if not local_path.is_file():
            blockers.append(f"staged simulation source is missing: {source_id}")
            continue
        digest = sha256_file(local_path)
        role = _source_role(source)
        used_in = [str(value).lower() for value in source.get("used_in", [])]
        if role in SYNTHESIS_ONLY_ROLES or (used_in and "simulation" not in used_in):
            blockers.append(
                f"Vivado selected a synthesis-only file in the simulation closure: {remote_path}"
            )
        rows.append(
            {
                "source_id": source_id,
                "role": role,
                "source_set": "simulation",
                "remote_path": remote_path,
                "local_path": str(local_path),
                "path": str(local_path),
                "staged_path": str(local_path.relative_to(out_dir)),
                "sha256": digest,
                "remote_sha256": digest,
                "local_sha256": digest,
                "hashes_match": True,
                "size_bytes": local_path.stat().st_size,
                "compile_order": source.get("compile_order"),
                "library": source.get("library"),
                "language": source.get("file_type"),
                "file_type": source.get("file_type"),
                "file_set": source.get("file_set"),
                "used_in": source.get("used_in", []),
                "parent_composite_file": source.get("parent_composite_file"),
                "owner_cell_ids": source.get("owner_cell_ids", []),
                "dependencies": [],
                "declared_modules": [],
            }
        )
    expected_ids = {
        str(row.get("source_id") or "")
        for row in facts.get("simulation", {}).get("source_files", [])
        if isinstance(row, dict)
    }
    recovered_ids = {str(row.get("source_id") or "") for row in rows}
    if len(rows) != len(recovered_ids) or recovered_ids != expected_ids:
        blockers.append("staged simulation source recovery does not exactly cover Vivado compile order")
    return rows, blockers


def _source_closure_fingerprint(rows: Iterable[dict[str, Any]]) -> str:
    normalized = sorted(
        [
            {
                "source_id": str(row.get("source_id") or ""),
                "role": str(row.get("role") or "").lower(),
                "sha256": str(row.get("sha256") or "").lower(),
                "dependencies": sorted(str(value) for value in row.get("dependencies", [])),
                "declared_modules": sorted(str(value) for value in row.get("declared_modules", [])),
            }
            for row in rows
        ],
        key=lambda row: row["source_id"],
    )
    return canonical_sha256(normalized)


def _bounded_text(raw: bytes, limit: int) -> tuple[str, bool]:
    return raw[:limit].decode("utf-8", errors="replace"), len(raw) > limit


def sample_source_contexts(rows: list[dict[str, Any]], sim_fileset: str) -> list[dict[str, Any]]:
    selected = [row for row in rows if str(row.get("file_set") or "") == sim_fileset]
    if rows:
        selected.append(max(rows, key=lambda row: int(row.get("compile_order") or 0)))
    contexts = []
    total = 0
    for row in sorted({str(item["source_id"]): item for item in selected}.values(), key=lambda item: int(item.get("compile_order") or 0)):
        if len(contexts) >= 32 or total >= 512 * 1024:
            break
        raw = Path(str(row["local_path"])).read_bytes()
        text, truncated = _bounded_text(raw, min(32 * 1024, 512 * 1024 - total))
        total += len(text.encode("utf-8"))
        contexts.append(
            {
                "source_id": row["source_id"],
                "sha256": row["sha256"],
                "remote_path": row["remote_path"],
                "selection_basis": "Vivado simulation fileset membership or compile-order root boundary",
                "text": text,
                "truncated": truncated,
            }
        )
    return contexts


def _full_context(
    rows: list[dict[str, Any]],
    selected_ids: Iterable[str],
    *,
    max_total_bytes: int | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    by_id = _source_index(rows)
    contexts = []
    blockers = []
    total = 0
    for source_id in dict.fromkeys(str(value) for value in selected_ids if str(value)):
        row = by_id.get(source_id)
        if not row:
            blockers.append(f"LLM requested unknown source context ID: {source_id}")
            continue
        path = Path(str(row.get("local_path") or row.get("path") or ""))
        if not path.is_file():
            blockers.append(f"LLM-requested source context is missing: {source_id}")
            continue
        raw = path.read_bytes()
        remaining = max_total_bytes - total if max_total_bytes is not None else None
        if remaining is not None and (remaining <= 0 or len(raw) > remaining):
            blockers.append(
                f"LLM-selected source context exceeds the exact-context budget; narrow the evidence set: {source_id}"
            )
            continue
        total += len(raw)
        try:
            text = raw.decode("utf-8")
            text_encoding = "utf-8"
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
            text_encoding = "latin-1"
        contexts.append(
            {
                "source_id": source_id,
                "sha256": row.get("sha256"),
                "path": str(path),
                "remote_path": row.get("remote_path"),
                "text": text,
                "text_encoding": text_encoding,
                "text_sha256": sha256_bytes(raw),
                "truncated": False,
            }
        )
    return contexts, blockers


def _source_review_segments(
    contexts: list[dict[str, Any]], budget_bytes: int
) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for context in contexts:
        source_id = str(context.get("source_id") or "")
        text = str(context.get("text") or "")
        text_encoding = str(context.get("text_encoding") or "utf-8")
        base = {key: value for key, value in context.items() if key != "text"}
        probe = {
            **base,
            "text_encoding": text_encoding,
            "segment_id": f"{source_id}#segment:0000-of-0001",
            "segment_index": 0,
            "segment_count": 1,
            "start_line": 1,
            "end_line": max(1, text.count("\n") + (0 if text.endswith("\n") else 1)),
            "start_char": 0,
            "end_char": len(text),
            "start_byte": 0,
            "end_byte": len(text.encode(text_encoding)),
            "segment_text_sha256": sha256_bytes(text.encode(text_encoding)),
            "text": text,
        }
        if _compact_size(probe) <= budget_bytes:
            pieces = [
                {
                    "text": text,
                    "start_line": 1,
                    "end_line": probe["end_line"],
                    "start_char": 0,
                    "end_char": len(text),
                    "start_byte": 0,
                    "end_byte": len(text.encode(text_encoding)),
                }
            ]
        else:
            overhead = _compact_size({**probe, "text": ""})
            margin = min(8192, max(256, budget_bytes // 8))
            max_chars = max(1, budget_bytes - overhead - margin)
            pieces = []
            start = 0
            start_line = 1
            while start < len(text):
                end = min(len(text), start + max_chars)
                if end < len(text):
                    newline = text.rfind("\n", start, end)
                    if newline > start:
                        end = newline + 1
                while end > start:
                    candidate = text[start:end]
                    candidate_probe = {
                        **probe,
                        "start_line": start_line,
                        "start_char": start,
                        "end_char": end,
                        "start_byte": len(text[:start].encode(text_encoding)),
                        "end_byte": len(text[:end].encode(text_encoding)),
                        "segment_text_sha256": sha256_bytes(
                            candidate.encode(text_encoding)
                        ),
                        "text": candidate,
                    }
                    if _compact_size(candidate_probe) <= budget_bytes:
                        break
                    end = start + max(1, (end - start) // 2)
                if end <= start:
                    raise ValueError(
                        f"source review cannot fit one character for {source_id} within {budget_bytes} bytes"
                    )
                candidate = text[start:end]
                newline_count = candidate.count("\n")
                end_line = start_line + newline_count - (
                    1 if candidate.endswith("\n") and newline_count else 0
                )
                pieces.append(
                    {
                        "text": candidate,
                        "start_line": start_line,
                        "end_line": max(start_line, end_line),
                        "start_char": start,
                        "end_char": end,
                        "start_byte": len(text[:start].encode(text_encoding)),
                        "end_byte": len(text[:end].encode(text_encoding)),
                    }
                )
                start = end
                start_line += newline_count
        segment_count = len(pieces)
        for index, piece in enumerate(pieces):
            segment = {
                **base,
                "text_encoding": text_encoding,
                "segment_id": (
                    f"{source_id}#segment:{index:04d}-of-{segment_count:04d}"
                ),
                "segment_index": index,
                "segment_count": segment_count,
                "start_line": piece["start_line"],
                "end_line": piece["end_line"],
                "start_char": piece["start_char"],
                "end_char": piece["end_char"],
                "start_byte": piece["start_byte"],
                "end_byte": piece["end_byte"],
                "segment_text_sha256": sha256_bytes(
                    str(piece["text"]).encode(text_encoding)
                ),
                "text": piece["text"],
            }
            if _compact_size(segment) > budget_bytes:
                raise ValueError(
                    f"source review segment exceeds budget for {segment['segment_id']}"
                )
            segments.append(segment)
    return segments


def _source_review_finding_errors(
    findings: Any, expected_source_ids: set[str], label: str
) -> list[str]:
    errors: list[str] = []
    if not isinstance(findings, list):
        return [f"{label} is not a list"]
    for row in findings:
        if not isinstance(row, dict):
            errors.append(f"{label} contains a malformed finding")
            continue
        refs = {
            str(value)
            for value in row.get("evidence_source_ids", [])
            if str(value)
        }
        if not refs or not refs.issubset(expected_source_ids):
            errors.append(f"{label} cites evidence outside its assigned source chunk")
    return errors


def _validate_source_review_record(
    record: dict[str, Any], contexts: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if record.get("error") or record.get("used_fallback") is True:
        errors.append(f"board source-review LLM failed: {record.get('error')}")
    output = record.get("output") if isinstance(record.get("output"), dict) else {}
    if output.get("schema_version") != DOMAIN_SOURCE_REVIEW_SCHEMA_VERSION:
        errors.append("board source-review agent returned an unsupported schema")
    if output.get("status") not in {"pass", "ready"}:
        errors.append(
            f"board source-review agent status is not ready/pass: {output.get('status')}"
        )
    errors.extend(
        f"board source-review blocker: {value}"
        for value in output.get("blockers", [])
    )

    expected_ids = list(
        dict.fromkeys(str(row.get("source_id") or "") for row in contexts)
    )
    expected_set = set(expected_ids)
    expected_segments = {
        str(row.get("segment_id") or ""): row for row in contexts
    }
    reviewed_ids = [
        str(value) for value in output.get("reviewed_source_ids", []) if str(value)
    ]
    if (
        len(reviewed_ids) != len(set(reviewed_ids))
        or set(reviewed_ids) != expected_set
    ):
        errors.append(
            "board source-review agent did not review exactly its assigned source IDs"
        )
    reviewed_segments = [
        str(value) for value in output.get("reviewed_segment_ids", []) if str(value)
    ]
    if (
        len(reviewed_segments) != len(set(reviewed_segments))
        or set(reviewed_segments) != set(expected_segments)
    ):
        errors.append(
            "board source-review agent did not review exactly its assigned source segments"
        )

    summaries = [
        row for row in output.get("source_summaries", []) if isinstance(row, dict)
    ]
    summary_segments = [str(row.get("segment_id") or "") for row in summaries]
    if (
        len(summary_segments) != len(set(summary_segments))
        or set(summary_segments) != set(expected_segments)
    ):
        errors.append(
            "board source-review summaries do not exactly cover the assigned source segments"
        )
    for row in summaries:
        source_id = str(row.get("source_id") or "")
        segment_id = str(row.get("segment_id") or "")
        expected = expected_segments.get(segment_id, {})
        if source_id != str(expected.get("source_id") or ""):
            errors.append(
                f"board source-review summary {segment_id} cites the wrong source"
            )
        if str(row.get("sha256") or "").lower() != str(
            expected.get("sha256") or ""
        ).lower():
            errors.append(f"board source-review summary {source_id} is not hash-bound")
        if str(row.get("segment_text_sha256") or "").lower() != str(
            expected.get("segment_text_sha256") or ""
        ).lower():
            errors.append(
                f"board source-review summary {segment_id} is not segment-hash-bound"
            )
        if row.get("start_line") != expected.get("start_line") or row.get(
            "end_line"
        ) != expected.get("end_line"):
            errors.append(
                f"board source-review summary {segment_id} has the wrong line range"
            )
        if row.get("start_byte") != expected.get("start_byte") or row.get(
            "end_byte"
        ) != expected.get("end_byte"):
            errors.append(
                f"board source-review summary {segment_id} has the wrong byte range"
            )
        if str(row.get("text_encoding") or "") != str(
            expected.get("text_encoding") or ""
        ):
            errors.append(
                f"board source-review summary {segment_id} has the wrong text encoding"
            )
        errors.extend(
            _source_review_finding_errors(
                row.get("findings", []), expected_set, f"source summary {source_id}"
            )
        )
        for finding in row.get("findings", []):
            if isinstance(finding, dict) and source_id not in {
                str(value)
                for value in finding.get("evidence_source_ids", [])
                if str(value)
            }:
                errors.append(
                    f"source summary {source_id} contains a finding that does not cite itself"
                )
    errors.extend(
        _source_review_finding_errors(
            output.get("cross_source_findings", []),
            expected_set,
            "cross-source finding",
        )
    )
    return output, errors


def _source_review_context(
    profile: dict[str, Any], selection: dict[str, Any]
) -> dict[str, Any]:
    return {
        "target_board_profile": profile,
        "validated_board_selection": {
            key: selection.get(key)
            for key in (
                "selected_cell_id",
                "wrapper_source_id",
                "relevant_sample_source_ids",
                "proposed_replaced_source_ids",
            )
        },
    }


def _prompt_tag_json(prompt: str, tag: str) -> dict[str, Any] | None:
    opening = f"<{tag}>\n"
    closing = f"\n</{tag}>"
    start = prompt.find(opening)
    if start < 0:
        return None
    start += len(opening)
    end = prompt.find(closing, start)
    if end < 0:
        return None
    try:
        value = json.loads(prompt[start:end])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _source_review_record_has_context(
    record: dict[str, Any],
    llm_dir: Path,
    context: dict[str, Any],
    context_sha256: str,
) -> bool:
    if record.get("source_review_context_sha256") == context_sha256:
        return True
    # Migration for pre-context-bound records: require a hash-matched persisted
    # prompt with the exact structured profile and selection blocks.
    request_path = Path(str(record.get("request_path") or ""))
    try:
        request_path.resolve(strict=True).relative_to(llm_dir)
    except (FileNotFoundError, ValueError):
        return False
    try:
        prompt = request_path.read_text(encoding="utf-8")
    except OSError:
        return False
    if record.get("prompt_hash") != sha256_bytes(prompt.encode("utf-8")):
        return False
    return (
        _prompt_tag_json(prompt, "target_board_profile")
        == context["target_board_profile"]
        and _prompt_tag_json(prompt, "validated_board_selection")
        == context["validated_board_selection"]
    )


def run_progressive_board_source_review(
    run_stage_agent: Any,
    out_dir: Path,
    profile: dict[str, Any],
    selection: dict[str, Any],
    source_contexts: list[dict[str, Any]],
    *,
    map_budget_bytes: int = DOMAIN_SOURCE_MAP_INPUT_BUDGET_BYTES,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    try:
        segments = _source_review_segments(source_contexts, map_budget_bytes)
        chunks = _partition_by_size(segments, map_budget_bytes)
    except ValueError as exc:
        return [], {}, [str(exc)]
    all_ids = list(
        dict.fromkeys(str(row.get("source_id") or "") for row in source_contexts)
    )
    all_segment_ids = [str(row.get("segment_id") or "") for row in segments]
    all_ids_sha256 = canonical_sha256(sorted(all_ids))
    segment_descriptors = [
        {
            "segment_id": row.get("segment_id"),
            "source_id": row.get("source_id"),
            "sha256": row.get("sha256"),
            "segment_text_sha256": row.get("segment_text_sha256"),
            "text_encoding": row.get("text_encoding"),
            "start_line": row.get("start_line"),
            "end_line": row.get("end_line"),
            "start_char": row.get("start_char"),
            "end_char": row.get("end_char"),
            "start_byte": row.get("start_byte"),
            "end_byte": row.get("end_byte"),
        }
        for row in segments
    ]
    ledger_path = (
        out_dir / "llm" / "exact_board_interface_source_review_coverage.json"
    )
    review_context = _source_review_context(profile, selection)
    review_context_sha256 = canonical_sha256(review_context)
    reusable_records: dict[int, tuple[dict[str, Any], dict[str, Any]]] = {}
    if ledger_path.is_file():
        ledger = read_json(ledger_path)
        ledger_records = [
            row for row in ledger.get("records", []) if isinstance(row, dict)
        ]
        # A completed review is bound to the source/segment provenance, not to
        # the transient batching budget used to send those segments to the LLM.
        # Reuse it directly when every hash-bound segment is still covered.  In
        # particular, do not re-review a complete source solely because a later
        # caller chooses a different prompt packing size.
        complete_checkpoint_matches = (
            ledger.get("status") == "pass"
            and ledger.get("source_ids") == all_ids
            and ledger.get("source_ids_sha256") == all_ids_sha256
            and ledger.get("segment_ids") == all_segment_ids
            and ledger.get("segment_ids_sha256")
            == canonical_sha256(sorted(all_segment_ids))
            and canonical_sha256(ledger.get("segments", []))
            == canonical_sha256(segment_descriptors)
            and ledger.get("source_review_context_sha256") == review_context_sha256
        )
        if complete_checkpoint_matches:
            llm_dir = (out_dir / "llm").resolve()
            current_segments = {
                str(row.get("segment_id") or ""): row for row in segments
            }
            checkpoint_outputs: list[dict[str, Any]] = []
            checkpoint_records: list[dict[str, Any]] = []
            reviewed_segment_ids: list[str] = []
            for ledger_record in ledger_records:
                record_path = Path(str(ledger_record.get("path") or ""))
                try:
                    record_path.resolve(strict=True).relative_to(llm_dir)
                except (FileNotFoundError, ValueError):
                    complete_checkpoint_matches = False
                    break
                if sha256_file(record_path) != ledger_record.get("sha256"):
                    complete_checkpoint_matches = False
                    break
                record = read_json(record_path)
                if not _source_review_record_has_context(
                    record, llm_dir, review_context, review_context_sha256
                ):
                    complete_checkpoint_matches = False
                    break
                assigned_segment_ids = [
                    str(value)
                    for value in ledger_record.get("reviewed_segment_ids", [])
                    if str(value)
                ]
                if (
                    not assigned_segment_ids
                    or len(assigned_segment_ids) != len(set(assigned_segment_ids))
                    or any(
                        segment_id not in current_segments
                        for segment_id in assigned_segment_ids
                    )
                ):
                    complete_checkpoint_matches = False
                    break
                checkpoint_contexts = [
                    current_segments[segment_id]
                    for segment_id in assigned_segment_ids
                ]
                output, record_errors = _validate_source_review_record(
                    record, checkpoint_contexts
                )
                if record_errors:
                    complete_checkpoint_matches = False
                    break
                checkpoint_records.append(record)
                checkpoint_outputs.append(output)
                reviewed_segment_ids.extend(assigned_segment_ids)
            if (
                complete_checkpoint_matches
                and len(reviewed_segment_ids) == len(set(reviewed_segment_ids))
                and set(reviewed_segment_ids) == set(all_segment_ids)
            ):
                print(
                    "[stage:verification.layer3.board_interface_source_review.map:semantic-checkpoint] "
                    "reuse complete source-review coverage under current segment provenance",
                    file=sys.stderr,
                    flush=True,
                )
                return checkpoint_outputs, {
                    "path": str(ledger_path.resolve()),
                    "sha256": sha256_file(ledger_path),
                }, []
        checkpoint_matches = (
            ledger.get("status") in {"pass", "partial"}
            and ledger.get("source_ids") == all_ids
            and ledger.get("source_ids_sha256") == all_ids_sha256
            and ledger.get("segment_ids") == all_segment_ids
            and ledger.get("segment_ids_sha256")
            == canonical_sha256(sorted(all_segment_ids))
            and canonical_sha256(ledger.get("segments", []))
            == canonical_sha256(segment_descriptors)
            and ledger.get("source_review_context_sha256") == review_context_sha256
            and len(ledger_records) <= len(chunks)
        )
        if checkpoint_matches:
            llm_dir = (out_dir / "llm").resolve()
            current_segments = {
                str(row.get("segment_id") or ""): row for row in segments
            }
            seen_chunk_indices: set[int] = set()
            for record_index, ledger_record in enumerate(ledger_records):
                chunk_index = int(ledger_record.get("chunk_index", record_index))
                if (
                    chunk_index < 0
                    or chunk_index >= len(chunks)
                    or chunk_index in seen_chunk_indices
                ):
                    checkpoint_matches = False
                    break
                seen_chunk_indices.add(chunk_index)
                record_path = Path(str(ledger_record.get("path") or ""))
                try:
                    record_path.resolve(strict=True).relative_to(llm_dir)
                except (FileNotFoundError, ValueError):
                    checkpoint_matches = False
                    break
                if sha256_file(record_path) != ledger_record.get("sha256"):
                    checkpoint_matches = False
                    break
                record = read_json(record_path)
                if not _source_review_record_has_context(
                    record, llm_dir, review_context, review_context_sha256
                ):
                    checkpoint_matches = False
                    break
                assigned_segment_ids = [
                    str(value)
                    for value in ledger_record.get("reviewed_segment_ids", [])
                    if str(value)
                ]
                expected_segment_ids = [
                    str(row.get("segment_id") or "") for row in chunks[chunk_index]
                ]
                if (
                    len(assigned_segment_ids) != len(set(assigned_segment_ids))
                    or set(assigned_segment_ids) != set(expected_segment_ids)
                    or any(
                        segment_id not in current_segments
                        for segment_id in assigned_segment_ids
                    )
                ):
                    checkpoint_matches = False
                    break
                checkpoint_contexts = [
                    current_segments[segment_id]
                    for segment_id in assigned_segment_ids
                ]
                output, record_errors = _validate_source_review_record(
                    record, checkpoint_contexts
                )
                if record_errors:
                    checkpoint_matches = False
                    break
                reusable_records[chunk_index] = (record, output)
        if not checkpoint_matches:
            reusable_records = {}

    # Recover successfully written per-chunk records if a previous process
    # stopped before refreshing its partial ledger. Every candidate is checked
    # against the current structured prompt context and exact segment hashes.
    if not reusable_records:
        llm_dir = (out_dir / "llm").resolve()
        for record_path in sorted(
            llm_dir.glob("exact_board_interface_source_map_*_agent_result.json")
        ):
            try:
                record = read_json(record_path)
            except (OSError, json.JSONDecodeError):
                continue
            if not _source_review_record_has_context(
                record, llm_dir, review_context, review_context_sha256
            ):
                continue
            for chunk_index, chunk in enumerate(chunks):
                if chunk_index in reusable_records:
                    continue
                output, record_errors = _validate_source_review_record(record, chunk)
                if not record_errors:
                    reusable_records[chunk_index] = (record, output)
                    break

    outputs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    record_chunk_indices: list[int] = []
    errors: list[str] = []

    def write_review_ledger(status: str) -> None:
        ledger = {
            "schema_version": "spatialaccagent.board_interface_source_review_coverage.v1",
            "status": status,
            "source_count": len(all_ids),
            "source_ids": all_ids,
            "source_ids_sha256": all_ids_sha256,
            "segment_count": len(all_segment_ids),
            "segment_ids": all_segment_ids,
            "segment_ids_sha256": canonical_sha256(sorted(all_segment_ids)),
            "segments": segment_descriptors,
            "source_review_context_sha256": review_context_sha256,
            "chunk_count": len(chunks),
            "records": [
                {
                    "chunk_index": chunk_index,
                    "agent": record.get("agent"),
                    "path": str(record.get("result_path") or ""),
                    "sha256": sha256_file(Path(str(record.get("result_path")))),
                    "reviewed_source_ids": output.get("reviewed_source_ids", []),
                    "reviewed_segment_ids": output.get("reviewed_segment_ids", []),
                }
                for chunk_index, (record, output) in zip(
                    record_chunk_indices, zip(records, outputs)
                )
            ],
        }
        write_json(ledger_path, ledger)

    for index, chunk in enumerate(chunks):
        assigned_ids = list(
            dict.fromkeys(str(row.get("source_id") or "") for row in chunk)
        )
        assigned_segment_ids = [
            str(row.get("segment_id") or "") for row in chunk
        ]
        if index in reusable_records:
            record, output = reusable_records[index]
            records.append(record)
            outputs.append(output)
            record_chunk_indices.append(index)
            print(
                f"[stage:verification.layer3.board_interface_source_review.map:semantic-checkpoint] reuse "
                f"{record.get('agent')}",
                file=sys.stderr,
                flush=True,
            )
            continue

        source_review_request = {
            "agent": f"exact_board_interface_source_map_{index:03d}_agent",
            "stage": "verification.layer3.board_interface_source_review.map",
            "task": (
                "Review every byte of the assigned hash-bound sample-project sources and extract the exact "
                "module-boundary, control, timing, AXI, DDR, reset, calibration, and backpressure semantics "
                "needed by the final exact-board domain agent."
            ),
            "inputs": {
                "target_board_profile": profile,
                "validated_board_selection": {
                    key: selection.get(key)
                    for key in (
                        "selected_cell_id",
                        "wrapper_source_id",
                        "relevant_sample_source_ids",
                        "proposed_replaced_source_ids",
                    )
                },
                "chunk": {
                    "chunk_index": index,
                    "chunk_count": len(chunks),
                    "assigned_source_ids": assigned_ids,
                    "assigned_segment_ids": assigned_segment_ids,
                    "source_contexts": chunk,
                },
                "complete_selected_source_coverage": {
                    "source_count": len(all_ids),
                    "source_ids_sha256": all_ids_sha256,
                    "segment_count": len(all_segment_ids),
                    "segment_ids_sha256": canonical_sha256(
                        sorted(all_segment_ids)
                    ),
                    "all_selected_sources_assigned_across_chunks": True,
                },
            },
            "out_dir": out_dir,
            "fallback_summary": "Exact board source semantics require the configured LLM agent.",
            "output_schema": BOARD_INTERFACE_SOURCE_REVIEW_SCHEMA,
            "prompt_rules": [
                "Read every assigned source segment in full. Copy chunk.assigned_source_ids and chunk.assigned_segment_ids exactly into reviewed_source_ids and reviewed_segment_ids, and return exactly one source_summaries row per assigned segment.",
                "For every summary, echo source_id, segment_id, full-source sha256, segment_text_sha256, text_encoding, start_line, end_line, start_byte, and end_byte exactly. Treat all segments of one source as a continuous hash-bound source; never infer omitted text between segments.",
                "Reason from the supplied source text and provenance, not from filename or module-name keyword rules. Do not infer semantics that the source does not establish.",
                "Preserve every exact constant, parameter, field range, reset/access value, clock edge, pulse/level rule, cycle relation, state transition, handshake, burst, backpressure, address, data-order, and calibration gate needed to reconstruct the selected slot contract.",
                "Explicitly cover declared modules and instantiations, the selected module replacement boundary, all non-interface control/status/configuration behavior, configure/start/observe/clear ordering, AXI sidebands and limits, DDR timing/roundtrip behavior, clocks, resets, and calibration dependencies when present.",
                "For vendor or shared sources, retain the exact behavior relevant to the selected board path while identifying that the source remains shared; never propose replacing a shared source.",
                "Every finding must cite only source IDs assigned to this chunk. A per-source finding must cite its own source ID. Keep summaries concise but lossless for the final domain contract.",
                "Use status=pass after complete review even when a source has no selected-path semantic finding. Use blockers only for malformed or unreadable supplied evidence.",
                f"Set schema_version exactly to {DOMAIN_SOURCE_REVIEW_SCHEMA_VERSION}.",
                "Return one JSON object only.",
            ],
        }
        record = run_stage_agent(**source_review_request)
        repair_attempt = 0
        while True:
            output, record_errors = _validate_source_review_record(record, chunk)
            if not record_errors:
                break
            original_error = record.get("error")
            record["deterministic_validation_errors"] = list(record_errors)
            record["error"] = (
                "deterministic board source-review validation failed: "
                + "; ".join(record_errors)
            )
            record_path = Path(str(record.get("result_path") or ""))
            try:
                record_path.resolve().relative_to((out_dir / "llm").resolve())
            except ValueError:
                pass
            else:
                write_json(record_path, record)
                write_json(
                    record_path.with_name(
                        f"{record_path.stem}_deterministic_invalid_{repair_attempt:03d}.json"
                    ),
                    record,
                )
            if original_error or record.get("used_fallback") is True:
                errors.extend(record_errors)
                break
            repair_attempt += 1
            record = run_stage_agent(
                **{
                    **source_review_request,
                    "task": (
                        f"{source_review_request['task']} Repair the preceding source-review output "
                        "using the deterministic diagnostics while preserving every assigned segment."
                    ),
                    "inputs": {
                        **source_review_request["inputs"],
                        "candidate_output": output,
                        "deterministic_validation_errors": record_errors,
                        "deterministic_repair_attempt": repair_attempt,
                    },
                    "prompt_rules": [
                        *source_review_request["prompt_rules"],
                        "Repair every deterministic_validation_errors entry. Echo hash and range fields from the assigned source_contexts exactly; never retype or recompute them from memory. Return the complete corrected source-review object, not a patch or explanation.",
                    ],
                }
            )
        if record_errors:
            break
        record["source_review_context_sha256"] = review_context_sha256
        record_path = Path(str(record.get("result_path") or ""))
        try:
            record_path.resolve().relative_to((out_dir / "llm").resolve())
        except ValueError:
            pass
        else:
            write_json(record_path, record)
        outputs.append(output)
        records.append(record)
        record_chunk_indices.append(index)
        write_review_ledger("partial" if len(records) < len(chunks) else "pass")
    if errors:
        if records:
            write_review_ledger("partial")
        return outputs, {}, errors
    write_review_ledger("pass")
    return outputs, {
        "path": str(ledger_path.resolve()),
        "sha256": sha256_file(ledger_path),
    }, []


def _validate_selector_record(
    record: dict[str, Any], facts: dict[str, Any], sample_rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    errors = []
    if record.get("error") or record.get("used_fallback") is True:
        errors.append(f"board-interface selector LLM failed: {record.get('error')}")
    output = record.get("output") if isinstance(record.get("output"), dict) else {}
    # The final selector has a distinct terminal state: ``selected`` records
    # an intentional choice after the progressive evidence review.  Worker
    # records still use ``pass``/``ready``; accepting the selector's own
    # schema state prevents a valid choice from being rejected downstream.
    if output.get("status") not in {"pass", "ready", "selected"}:
        errors.append(
            f"board-interface selector status is not ready/pass/selected: {output.get('status')}"
        )
    errors.extend(f"board-interface selector blocker: {value}" for value in output.get("blockers", []))
    objects = _object_index(facts)
    cell = objects.get(str(output.get("selected_cell_id") or ""))
    if not cell or cell.get("kind") != "cell":
        errors.append("board-interface selector did not choose a Vivado cell object ID")
    sample_ids = set(_source_index(sample_rows))
    wrapper_id = str(output.get("wrapper_source_id") or "")
    relevant_sample = {str(value) for value in output.get("relevant_sample_source_ids", []) if str(value)}
    replaced = {str(value) for value in output.get("proposed_replaced_source_ids", []) if str(value)}
    if wrapper_id not in sample_ids:
        errors.append("selector wrapper_source_id is not in the sample simulation closure")
    if not relevant_sample or not relevant_sample.issubset(sample_ids) or wrapper_id not in relevant_sample:
        errors.append("selector relevant_sample_source_ids are empty, unknown, or omit the wrapper")
    if not replaced or not replaced.issubset(relevant_sample):
        errors.append("selector proposed replacement sources are empty or outside its sample evidence set")
    return output, errors


def llm_fact_projection(
    facts: dict[str, Any], *, selection_view: bool = False, include_source_catalog: bool = True
) -> dict[str, Any]:
    """Keep all structural objects while dropping GUI/default-value bulk."""

    structural_properties = {
        "CLASS",
        "TYPE",
        "NAME",
        "PATH",
        "DIR",
        "LEFT",
        "RIGHT",
        "INTF",
        "MODE",
        "VLNV",
        "SELECTED_SIM_MODEL",
        "COMBINED_SIM_MODEL",
    }
    objects = []
    for row in facts.get("objects", []):
        if not isinstance(row, dict):
            continue
        if (
            selection_view
            and row.get("kind") == "pin"
            and str(row.get("properties", {}).get("INTF") or "").upper() == "TRUE"
        ):
            continue
        props = {
            key: (
                value
                if len(str(value).encode("utf-8")) <= 2048
                else {
                    "omitted_value_sha256": sha256_bytes(str(value).encode("utf-8")),
                    "size_bytes": len(str(value).encode("utf-8")),
                }
            )
            for key, value in row.get("properties", {}).items()
            if key in structural_properties
            or (
                key.startswith("CONFIG.")
                and not (
                    selection_view
                    and row.get("kind") == "cell"
                    and key != "CONFIG.Component_Name"
                )
            )
        }
        objects.append(
            {
                "object_id": row.get("object_id"),
                "kind": row.get("kind"),
                "bd_path": row.get("bd_path"),
                "path": row.get("path"),
                "owner_path": row.get("owner_path"),
                "properties": props,
                "connected_nets": row.get("connected_nets", []),
                "members": (
                    []
                    if selection_view and row.get("kind") in {"interface_pin", "interface_port"}
                    else row.get("members", [])
                ),
                "simulation_source_ids": row.get("simulation_source_ids", []),
            }
        )
    simulation = facts.get("simulation", {})
    sources = []
    for row in simulation.get("source_files", []):
        if not isinstance(row, dict):
            continue
        sources.append({key: value for key, value in row.items() if key != "properties"})
    return {
        "schema_version": facts.get("schema_version"),
        "status": facts.get("status"),
        "project": facts.get("project"),
        "simulation": {
            "source_files": sources if include_source_catalog and not selection_view else [],
            "source_catalog_supplied_separately": selection_view or not include_source_catalog,
            "fileset_properties": simulation.get("fileset_properties", {}),
            "unresolved_dependencies": simulation.get("unresolved_dependencies", []),
            "recursive_dependency_scan_complete": simulation.get("recursive_dependency_scan_complete"),
            "external_library_dependencies": simulation.get("external_library_dependencies", []),
            "simulator_export_contexts": (
                [
                    {key: value for key, value in row.items() if key != "text"}
                    for row in simulation.get("simulator_export_contexts", [])
                ]
                if selection_view
                else simulation.get("simulator_export_contexts", [])
            ),
        },
        "block_designs": facts.get("block_designs", []),
        "objects": objects,
        "raw_fact_sha256": canonical_sha256(facts),
        "blockers": facts.get("blockers", []),
    }


def llm_sample_source_manifest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "source_id",
        "role",
        "remote_path",
        "sha256",
        "size_bytes",
        "compile_order",
        "library",
        "language",
        "file_type",
        "file_set",
        "used_in",
        "parent_composite_file",
        "owner_cell_ids",
    )
    return [{field: row.get(field) for field in fields} for row in rows]


def llm_selection_fact_projection(facts: dict[str, Any]) -> dict[str, Any]:
    flat = llm_fact_projection(
        facts, selection_view=True, include_source_catalog=False
    )
    objects = [row for row in flat.get("objects", []) if isinstance(row, dict)]
    cells = []
    for cell in (row for row in objects if row.get("kind") == "cell"):
        children = [
            row
            for row in objects
            if row.get("bd_path") == cell.get("bd_path")
            and row.get("owner_path") == cell.get("path")
            and row.get("kind") in {"pin", "interface_pin"}
        ]
        cells.append(
            {
                **cell,
                "standalone_pins": [row for row in children if row.get("kind") == "pin"],
                "interfaces": [row for row in children if row.get("kind") == "interface_pin"],
            }
        )
    return {
        "schema_version": flat.get("schema_version"),
        "status": flat.get("status"),
        "project": flat.get("project"),
        "simulation": flat.get("simulation"),
        "block_designs": flat.get("block_designs"),
        "cells": cells,
        "top_level_ports": [
            row
            for row in objects
            if row.get("kind") in {"port", "interface_port"}
        ],
        "nets": [
            row
            for row in objects
            if row.get("kind") in {"net", "interface_net"}
        ],
        "raw_fact_sha256": flat.get("raw_fact_sha256"),
        "selection_projection_policy": {
            "all_cells_included": True,
            "all_standalone_cell_pins_included": True,
            "all_cell_interfaces_included": True,
            "interface_member_pins_deferred_until_selected_cell_subgraph": True,
            "full_raw_fact_artifact_hash_bound": True,
        },
        "blockers": flat.get("blockers", []),
    }


def _compact_size(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _nested_object_ids(value: Any) -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        object_id = str(value.get("object_id") or "")
        if object_id:
            result.append(object_id)
        for child in value.values():
            result.extend(_nested_object_ids(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(_nested_object_ids(child))
    return list(dict.fromkeys(result))


def selection_evidence_units(
    facts: dict[str, Any], sample_rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    projection = llm_selection_fact_projection(facts)
    full_projection = llm_fact_projection(facts, include_source_catalog=False)
    full_objects = [
        row for row in full_projection.get("objects", []) if isinstance(row, dict)
    ]
    units: list[dict[str, Any]] = []
    assigned_object_ids: set[str] = set()
    for cell in (row for row in full_objects if row.get("kind") == "cell"):
        children = [
            row
            for row in full_objects
            if row.get("bd_path") == cell.get("bd_path")
            and row.get("owner_path") == cell.get("path")
            and row.get("kind") in {"pin", "interface_pin"}
        ]
        cell_unit = {
            **cell,
            "standalone_pins": [row for row in children if row.get("kind") == "pin"],
            "interfaces": [row for row in children if row.get("kind") == "interface_pin"],
        }
        object_ids = _nested_object_ids(cell_unit)
        assigned_object_ids.update(object_ids)
        units.append(
            {
                "unit_kind": "vivado_cell_with_all_owned_ports",
                "object_ids": object_ids,
                "source_ids": [],
                "evidence": cell_unit,
            }
        )
    for row in full_objects:
        object_id = str(row.get("object_id") or "")
        if not object_id or object_id in assigned_object_ids:
            continue
        units.append(
            {
                "unit_kind": f"vivado_{str(row.get('kind') or 'object')}",
                "object_ids": [object_id],
                "source_ids": [],
                "evidence": row,
            }
        )
    for row in llm_sample_source_manifest(sample_rows):
        source_id = str(row.get("source_id") or "")
        units.append(
            {
                "unit_kind": "sample_simulation_source",
                "object_ids": [],
                "source_ids": [source_id] if source_id else [],
                "evidence": row,
            }
        )
    common = {
        "schema_version": projection.get("schema_version"),
        "status": projection.get("status"),
        "project": projection.get("project"),
        "simulation": {
            key: value
            for key, value in projection.get("simulation", {}).items()
            if key != "source_files"
        },
        "block_designs": projection.get("block_designs"),
        "raw_fact_sha256": projection.get("raw_fact_sha256"),
        "selection_projection_policy": {
            **projection.get("selection_projection_policy", {}),
            "all_vivado_objects_included_across_map_chunks": True,
            "interface_member_pins_deferred_until_selected_cell_subgraph": False,
        },
        "blockers": projection.get("blockers", []),
    }
    return common, units


def _partition_by_size(rows: list[Any], budget_bytes: int) -> list[list[Any]]:
    if budget_bytes <= 0:
        raise ValueError("selector partition budget must be positive")
    groups: list[list[Any]] = []
    current: list[Any] = []
    current_bytes = 2
    for row in rows:
        row_bytes = _compact_size(row) + (1 if current else 0)
        if row_bytes + 2 > budget_bytes:
            raise ValueError(
                f"one exact selector evidence unit exceeds the configured context budget: {row_bytes} > {budget_bytes}"
            )
        if current and current_bytes + row_bytes > budget_bytes:
            groups.append(current)
            current = []
            current_bytes = 2
            row_bytes = _compact_size(row)
        current.append(row)
        current_bytes += row_bytes
    if current:
        groups.append(current)
    return groups


def _coverage_from_units(units: Iterable[dict[str, Any]]) -> dict[str, list[str]]:
    object_ids: list[str] = []
    source_ids: list[str] = []
    for unit in units:
        object_ids.extend(str(value) for value in unit.get("object_ids", []) if str(value))
        source_ids.extend(str(value) for value in unit.get("source_ids", []) if str(value))
    return {
        "object_ids": list(dict.fromkeys(object_ids)),
        "source_ids": list(dict.fromkeys(source_ids)),
    }


def _merge_coverages(coverages: Iterable[dict[str, list[str]]]) -> dict[str, list[str]]:
    object_ids: list[str] = []
    source_ids: list[str] = []
    for coverage in coverages:
        object_ids.extend(str(value) for value in coverage.get("object_ids", []) if str(value))
        source_ids.extend(str(value) for value in coverage.get("source_ids", []) if str(value))
    return {
        "object_ids": list(dict.fromkeys(object_ids)),
        "source_ids": list(dict.fromkeys(source_ids)),
    }


def _selector_map_request(
    out_dir: Path,
    common: dict[str, Any],
    profile: dict[str, Any],
    chunk: list[dict[str, Any]],
    index: int,
    chunk_count: int,
    full_coverage: dict[str, list[str]],
) -> dict[str, Any]:
    coverage = _coverage_from_units(chunk)
    return {
        "agent": f"exact_board_interface_selector_map_{index:03d}_agent",
        "stage": "verification.layer3.board_interface_selection.map",
        "task": SELECTOR_MAP_TASK,
        "inputs": {
            "global_vivado_context": common,
            "target_board_profile": profile,
            "chunk": {
                "chunk_index": index,
                "chunk_count": chunk_count,
                "assigned_coverage": coverage,
                "evidence_units": chunk,
            },
            "global_coverage_commitment": {
                "object_count": len(full_coverage["object_ids"]),
                "source_count": len(full_coverage["source_ids"]),
                "object_ids_sha256": canonical_sha256(
                    sorted(full_coverage["object_ids"])
                ),
                "source_ids_sha256": canonical_sha256(
                    sorted(full_coverage["source_ids"])
                ),
            },
        },
        "out_dir": out_dir,
        "fallback_summary": "Exact board selection map review requires the configured LLM agent.",
        "output_schema": BOARD_INTERFACE_SELECTION_MAP_SCHEMA,
        "prompt_rules": SELECTOR_MAP_PROMPT_RULES,
    }


_SELECTOR_MAP_NON_SEMANTIC_POLICY_KEYS = {
    "api_key_configured",
    "configured_model",
    "endpoint_configured",
    "http_transport",
    "locked_model",
    "max_output_tokens",
    "model_override_approval_path",
    "model_selection_policy",
    "requested_model_override",
}


def _selector_map_semantic_llm_policy(policy: Any) -> dict[str, Any] | None:
    if not isinstance(policy, dict):
        return None
    return {
        str(key): value
        for key, value in policy.items()
        if str(key) not in _SELECTOR_MAP_NON_SEMANTIC_POLICY_KEYS
    }


def _selector_map_llm_contract() -> dict[str, Any]:
    from accagent.framework.llm_config import resolved_llm_cfg
    from accagent.framework.llm_io import PROMPT_PROTOCOL
    from accagent.framework.stage_llm import (
        ACTION_CONTRACT_EXAMPLES,
        ACTION_GROUNDING_REGISTRY,
        SYSTEM,
        llm_policy_summary,
        stage_worker_reasoning_effort,
    )

    cfg = resolved_llm_cfg()
    reasoning_effort = stage_worker_reasoning_effort() or cfg.reasoning_effort
    policy = llm_policy_summary()
    return {
        "model": cfg.model,
        "reasoning_effort": reasoning_effort,
        "mode": cfg.mode,
        "stream": cfg.stream,
        "transport": "responses_sse_stream" if cfg.stream else "responses_json",
        "prompt_protocol": PROMPT_PROTOCOL,
        "system_sha256": sha256_bytes(SYSTEM.encode("utf-8")),
        "action_grounding_registry_sha256": canonical_sha256(
            ACTION_GROUNDING_REGISTRY
        ),
        "action_contract_examples_sha256": canonical_sha256(
            ACTION_CONTRACT_EXAMPLES
        ),
        "semantic_llm_policy_sha256": canonical_sha256(
            _selector_map_semantic_llm_policy(policy)
        ),
        "llm_policy_provenance_sha256": canonical_sha256(policy),
    }


def _selector_map_semantic_llm_contract(
    llm_contract: dict[str, Any],
) -> dict[str, Any]:
    """Return only fields that can change a selector decision.

    SSE versus JSON and the local HTTP implementation serialize the same
    schema-bound model request. They remain auditable in worker records but
    must not invalidate a prior semantic review of unchanged board evidence.
    """

    return {
        key: value
        for key, value in llm_contract.items()
        if key
        not in {
            "stream",
            "transport",
            "http_transport",
            "llm_policy_provenance_sha256",
        }
    }


def _selector_map_contract_without_policy(
    llm_contract: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in llm_contract.items()
        if key
        not in {
            "stream",
            "transport",
            "http_transport",
            "llm_policy_sha256",
            "llm_policy_provenance_sha256",
            "semantic_llm_policy_sha256",
        }
    }


def _selector_map_transport_provenance(
    llm_contract: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: llm_contract.get(key)
        for key in ("stream", "transport", "http_transport")
        if key in llm_contract
    }


def _normalize_selector_export_contexts(facts: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = []
    generated_line = re.compile(r"^# Generated by Vivado on .*$", re.MULTILINE)
    marker = "/vcs_export/"
    for row in facts.get("simulation", {}).get("simulator_export_contexts", []):
        if not isinstance(row, dict):
            continue
        remote_path = str(row.get("remote_path") or "")
        export_root = ""
        normalized_path = remote_path
        if marker in remote_path:
            export_root, suffix = remote_path.split(marker, 1)
            normalized_path = f"<VIVADO_EXPORT_ROOT>{marker}{suffix}"
        text = str(row.get("text") or "")
        if export_root:
            text = text.replace(export_root, "<VIVADO_EXPORT_ROOT>")
        text = generated_line.sub(
            "# Generated by Vivado on <NORMALIZED_TIMESTAMP>", text
        )
        normalized.append(
            {
                "normalized_path": normalized_path,
                "normalized_text": text,
                "normalized_text_sha256": sha256_bytes(text.encode("utf-8")),
            }
        )
    return normalized


def _stable_selector_map_common(
    common: dict[str, Any], normalized_export_contexts: list[dict[str, Any]]
) -> dict[str, Any]:
    stable = json.loads(json.dumps(common))
    stable.pop("raw_fact_sha256", None)
    simulation = stable.get("simulation")
    if isinstance(simulation, dict):
        simulation["simulator_export_contexts"] = normalized_export_contexts
    return stable


def _selector_map_semantic_descriptor(
    request: dict[str, Any],
    llm_contract: dict[str, Any],
    normalized_export_contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    inputs = request["inputs"]
    payload = {
        "schema_version": SELECTOR_MAP_CHECKPOINT_SCHEMA_VERSION,
        "agent": request["agent"],
        "stage": request["stage"],
        "task": request["task"],
        "prompt_rules": request["prompt_rules"],
        "output_schema": request["output_schema"],
        "fallback_summary": request["fallback_summary"],
        "llm_contract": _selector_map_semantic_llm_contract(llm_contract),
        "stable_inputs": {
            "global_vivado_context": _stable_selector_map_common(
                inputs["global_vivado_context"], normalized_export_contexts
            ),
            "target_board_profile": inputs["target_board_profile"],
            "chunk": inputs["chunk"],
            "global_coverage_commitment": inputs[
                "global_coverage_commitment"
            ],
        },
        "excluded_ephemeral_inputs": [
            "global_vivado_context.raw_fact_sha256",
            "simulator_export_contexts path prefix before /vcs_export/",
            "simulator_export_contexts '# Generated by Vivado on ...' line",
        ],
    }
    return {"fingerprint": canonical_sha256(payload), "payload": payload}


def _validate_selection_map_record(
    record: dict[str, Any],
    expected_coverage: dict[str, list[str]],
    known_cell_ids: set[str],
    known_object_ids: set[str],
    known_source_ids: set[str],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if record.get("error") or record.get("used_fallback") is True:
        errors.append(f"progressive selector LLM failed: {record.get('error')}")
    output = record.get("output") if isinstance(record.get("output"), dict) else {}
    if output.get("schema_version") != SELECTION_MAP_SCHEMA_VERSION:
        errors.append("progressive selector returned an unsupported map schema")
    if output.get("status") not in {"pass", "ready"}:
        errors.append(f"progressive selector map status is not ready/pass: {output.get('status')}")
    errors.extend(f"progressive selector map blocker: {value}" for value in output.get("blockers", []))

    expected_objects = list(expected_coverage.get("object_ids", []))
    expected_sources = list(expected_coverage.get("source_ids", []))
    reviewed_objects = [str(value) for value in output.get("reviewed_object_ids", []) if str(value)]
    reviewed_sources = [str(value) for value in output.get("reviewed_source_ids", []) if str(value)]
    if len(reviewed_objects) != len(set(reviewed_objects)) or set(reviewed_objects) != set(expected_objects):
        errors.append("progressive selector map did not review exactly its assigned Vivado object IDs")
    if len(reviewed_sources) != len(set(reviewed_sources)) or set(reviewed_sources) != set(expected_sources):
        errors.append("progressive selector map did not review exactly its assigned sample source IDs")

    evidence_objects = set(expected_objects)
    evidence_sources = set(expected_sources)
    for row in output.get("candidate_cells", []):
        if not isinstance(row, dict) or str(row.get("cell_id") or "") not in known_cell_ids:
            errors.append("progressive selector map cited an unknown candidate cell")
            continue
        if not set(str(value) for value in row.get("evidence_object_ids", []) if str(value)).issubset(evidence_objects):
            errors.append("progressive selector map candidate cell cites out-of-chunk Vivado evidence")
        if not set(str(value) for value in row.get("evidence_source_ids", []) if str(value)).issubset(evidence_sources):
            errors.append("progressive selector map candidate cell cites out-of-chunk source evidence")
    for key in (
        "candidate_wrapper_sources",
        "candidate_relevant_sources",
        "candidate_replacement_sources",
    ):
        for row in output.get(key, []):
            if not isinstance(row, dict) or str(row.get("source_id") or "") not in known_source_ids:
                errors.append(f"progressive selector map {key} cites an unknown source")
                continue
            if not set(str(value) for value in row.get("evidence_object_ids", []) if str(value)).issubset(evidence_objects):
                errors.append(f"progressive selector map {key} cites out-of-chunk Vivado evidence")
            if not set(str(value) for value in row.get("evidence_source_ids", []) if str(value)).issubset(evidence_sources):
                errors.append(f"progressive selector map {key} cites out-of-chunk source evidence")
    for row in output.get("findings", []):
        if not isinstance(row, dict):
            errors.append("progressive selector map returned a malformed finding")
            continue
        object_refs = {str(value) for value in row.get("evidence_object_ids", []) if str(value)}
        source_refs = {str(value) for value in row.get("evidence_source_ids", []) if str(value)}
        if not object_refs.issubset(evidence_objects) or not source_refs.issubset(evidence_sources):
            errors.append("progressive selector map finding cites evidence outside its assigned chunk")
    if not set(reviewed_objects).issubset(known_object_ids):
        errors.append("progressive selector map coverage contains an unknown Vivado object ID")
    if not set(reviewed_sources).issubset(known_source_ids):
        errors.append("progressive selector map coverage contains an unknown source ID")
    return output, errors


def _bind_framework_map_coverage(
    record: dict[str, Any], coverage: dict[str, list[str]]
) -> dict[str, Any]:
    """Bind framework-owned chunk coverage without asking the LLM to echo it.

    The map worker's semantic responsibility is candidate/finding selection.  The
    exact assigned object/source sets are already constructed, hashed, and
    supplied by the framework, so repeating hundreds of IDs in model output is
    a lossy transport burden rather than additional evidence.
    """

    output = record.get("output") if isinstance(record.get("output"), dict) else {}
    output = json.loads(json.dumps(output))
    output["reviewed_object_ids"] = list(coverage.get("object_ids", []))
    output["reviewed_source_ids"] = list(coverage.get("source_ids", []))
    record["output"] = output
    record["framework_coverage_overlay"] = {
        "object_ids": list(coverage.get("object_ids", [])),
        "source_ids": list(coverage.get("source_ids", [])),
    }
    return record


def _selector_map_checkpoint_path(out_dir: Path) -> Path:
    return out_dir / "llm" / SELECTOR_MAP_CHECKPOINT_NAME


def _checkpoint_artifact_path(
    llm_dir: Path,
    canonical_name: str,
    artifact_path: str,
    expected_sha256: str,
) -> Path | None:
    """Resolve a hash-bound checkpoint artifact after normal result archival.

    Worker results are deliberately moved into ``llm/history`` when a new live
    prompt supersedes them. A semantic checkpoint must retain its authority
    through that provenance move instead of forcing the LLM to repeat the same
    review. Only an artifact with the recorded digest is accepted.
    """

    name = Path(canonical_name)
    if name.name != canonical_name or not re.fullmatch(
        r"[0-9a-f]{64}", expected_sha256
    ):
        return None
    candidates: list[Path] = []
    if artifact_path:
        relative = Path(artifact_path)
        if not relative.is_absolute() and ".." not in relative.parts:
            candidates.append(llm_dir / relative)
    candidates.append(llm_dir / name)
    history = llm_dir / "history"
    if history.is_dir():
        candidates.extend(
            sorted(history.glob(f"{name.stem}.*{name.suffix}"))
        )
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(llm_dir.resolve())
        except (FileNotFoundError, ValueError):
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file() and sha256_file(resolved) == expected_sha256:
            return resolved
    return None


def _selector_map_fingerprint_components(
    descriptor: dict[str, Any], llm_contract: dict[str, Any]
) -> dict[str, str]:
    payload = descriptor["payload"]
    stable_inputs = payload["stable_inputs"]
    chunk = stable_inputs["chunk"]
    return {
        "stable_global_vivado_context_sha256": canonical_sha256(
            stable_inputs["global_vivado_context"]
        ),
        "target_board_profile_sha256": canonical_sha256(
            stable_inputs["target_board_profile"]
        ),
        "evidence_units_sha256": canonical_sha256(chunk["evidence_units"]),
        "assigned_coverage_sha256": canonical_sha256(chunk["assigned_coverage"]),
        "global_coverage_commitment_sha256": canonical_sha256(
            stable_inputs["global_coverage_commitment"]
        ),
        "map_schema_sha256": canonical_sha256(payload["output_schema"]),
        "map_task_sha256": sha256_bytes(payload["task"].encode("utf-8")),
        "map_prompt_rules_sha256": canonical_sha256(payload["prompt_rules"]),
        "llm_contract_sha256": canonical_sha256(
            _selector_map_semantic_llm_contract(llm_contract)
        ),
    }


def _selector_map_prompt_semantic_policy(prompt_path: Path) -> dict[str, Any] | None:
    try:
        text = prompt_path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"<llm_policy>\n(.*?)\n</llm_policy>", text, re.DOTALL)
    if not match:
        return None
    try:
        policy = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return _selector_map_semantic_llm_policy(policy)


def _selector_map_checkpoint_semantics_match(
    entry: dict[str, Any],
    manifest: dict[str, Any],
    descriptor: dict[str, Any],
    llm_contract: dict[str, Any],
    prompt_path: Path,
) -> bool:
    """Accept legacy checkpoints only when all decision-relevant fields match."""

    if entry.get("semantic_fingerprint") == descriptor["fingerprint"]:
        return True
    historical_components = entry.get("fingerprint_components")
    if not isinstance(historical_components, dict):
        return False
    current_components = _selector_map_fingerprint_components(
        descriptor, llm_contract
    )
    for key, value in current_components.items():
        if key == "llm_contract_sha256":
            continue
        if historical_components.get(key) != value:
            return False
    historical_contract = manifest.get("llm_contract")
    if not isinstance(historical_contract, dict):
        return False
    if _selector_map_contract_without_policy(
        historical_contract
    ) != _selector_map_contract_without_policy(llm_contract):
        return False
    from accagent.framework.stage_llm import llm_policy_summary

    return _selector_map_prompt_semantic_policy(
        prompt_path
    ) == _selector_map_semantic_llm_policy(llm_policy_summary())


def _selector_map_record_errors(
    record: dict[str, Any],
    request: dict[str, Any],
    llm_contract: dict[str, Any],
) -> list[str]:
    expected = {
        "agent": request["agent"],
        "stage": request["stage"],
        "model": llm_contract["model"],
        "reasoning_effort": llm_contract["reasoning_effort"],
        "mode": llm_contract["mode"],
        "prompt_protocol": llm_contract["prompt_protocol"],
    }
    errors = [
        f"selector map record {key} does not match the current LLM contract"
        for key, value in expected.items()
        if record.get(key) != value
    ]
    if record.get("schema_version") != "spatialaccagent.stage_worker_record.v0":
        errors.append("selector map record schema_version is invalid")
    if record.get("error") or record.get("used_fallback") is not False:
        errors.append("selector map record is an error/fallback result")
    output = record.get("output") if isinstance(record.get("output"), dict) else {}
    if output.get("schema_version") != SELECTION_MAP_SCHEMA_VERSION:
        errors.append("selector map record output schema_version is invalid")
    if output.get("status") not in {"pass", "ready"}:
        errors.append("selector map record output status is not pass/ready")
    return errors


def _selector_map_checkpoint_manifest_errors(
    manifest: dict[str, Any], expected_chunk_count: int
) -> list[str]:
    errors: list[str] = []
    chunks = manifest.get("chunks") if isinstance(manifest.get("chunks"), list) else []
    status = str(manifest.get("status") or "")
    if manifest.get("chunk_count") != expected_chunk_count:
        errors.append("selector map checkpoint chunk_count is inconsistent")
        return errors
    if status not in {"pass", "partial"}:
        errors.append("selector map checkpoint status is invalid")
        return errors
    indices = [row.get("chunk_index") for row in chunks if isinstance(row, dict)]
    if (
        len(indices) != len(chunks)
        or len(indices) != len(set(indices))
        or indices != sorted(indices)
        or any(not isinstance(index, int) or index < 0 or index >= expected_chunk_count for index in indices)
    ):
        errors.append("selector map checkpoint chunk indices are invalid or duplicated")
    if status == "pass" and indices != list(range(expected_chunk_count)):
        errors.append("complete selector map checkpoint does not cover every chunk")
    if status == "partial" and len(indices) >= expected_chunk_count:
        errors.append("partial selector map checkpoint incorrectly claims complete coverage")
    agents = []
    for row in chunks:
        if not isinstance(row, dict):
            errors.append("selector map checkpoint contains a malformed chunk")
            continue
        index = row.get("chunk_index")
        if not isinstance(index, int):
            continue
        expected_agent = f"exact_board_interface_selector_map_{index:03d}_agent"
        agent = str(row.get("agent") or "")
        agents.append(agent)
        if row.get("chunk_count") != expected_chunk_count or agent != expected_agent:
            errors.append(
                f"selector map checkpoint chunk {index} agent/count binding is invalid"
            )
        if row.get("record_file") != f"{expected_agent}_result.json":
            errors.append(
                f"selector map checkpoint chunk {index} record_file binding is invalid"
            )
        if row.get("prompt_file") != f"{expected_agent}_prompt.md":
            errors.append(
                f"selector map checkpoint chunk {index} prompt_file binding is invalid"
            )
        for field in ("record_artifact_path", "prompt_artifact_path"):
            value = row.get(field)
            if value in {None, ""}:
                continue
            relative = Path(str(value))
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(
                    f"selector map checkpoint chunk {index} {field} is outside the LLM directory"
                )
        for field in (
            "semantic_fingerprint",
            "record_sha256",
            "output_sha256",
            "origin_prompt_sha256",
        ):
            if not re.fullmatch(r"[0-9a-f]{64}", str(row.get(field) or "")):
                errors.append(
                    f"selector map checkpoint chunk {index} {field} is invalid"
                )
    if len(agents) != len(set(agents)):
        errors.append("selector map checkpoint agents are duplicated")
    return errors


def _reuse_selector_map_checkpoint(
    out_dir: Path,
    request: dict[str, Any],
    descriptor: dict[str, Any],
    coverage: dict[str, list[str]],
    known_cell_ids: set[str],
    known_object_ids: set[str],
    known_source_ids: set[str],
    llm_contract: dict[str, Any],
) -> tuple[dict[str, Any] | None, str]:
    path = _selector_map_checkpoint_path(out_dir)
    if not path.is_file():
        return None, "checkpoint_missing"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, "checkpoint_unreadable"
    if (
        manifest.get("schema_version") != SELECTOR_MAP_CHECKPOINT_SCHEMA_VERSION
        or manifest.get("status") not in {"pass", "partial"}
    ):
        return None, "checkpoint_contract_invalid"
    expected_chunk_count = int(request["inputs"]["chunk"]["chunk_count"])
    if _selector_map_checkpoint_manifest_errors(
        manifest, expected_chunk_count
    ):
        return None, "checkpoint_chunk_manifest_invalid"
    index = int(request["inputs"]["chunk"]["chunk_index"])
    entries = manifest.get("chunks") if isinstance(manifest.get("chunks"), list) else []
    entry = next(
        (
            row
            for row in entries
            if isinstance(row, dict) and row.get("chunk_index") == index
        ),
        None,
    )
    if not entry:
        return None, "checkpoint_chunk_missing"
    if entry.get("agent") != request["agent"]:
        return None, "checkpoint_agent_binding_changed"
    if entry.get("origin_exact_prompt_validated") is not True:
        return None, "origin_prompt_not_validated"
    llm_dir = (out_dir / "llm").resolve()
    record_path = _checkpoint_artifact_path(
        llm_dir,
        str(entry.get("record_file") or ""),
        str(entry.get("record_artifact_path") or ""),
        str(entry.get("record_sha256") or ""),
    )
    prompt_path = _checkpoint_artifact_path(
        llm_dir,
        str(entry.get("prompt_file") or ""),
        str(entry.get("prompt_artifact_path") or ""),
        str(entry.get("origin_prompt_sha256") or ""),
    )
    if record_path is None or prompt_path is None:
        return None, "checkpoint_artifact_missing"
    if not _selector_map_checkpoint_semantics_match(
        entry, manifest, descriptor, llm_contract, prompt_path
    ):
        return None, "semantic_fingerprint_changed"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except Exception:
        return None, "checkpoint_record_unreadable"
    if record.get("prompt_hash") != entry.get("origin_prompt_sha256"):
        return None, "checkpoint_prompt_hash_mismatch"
    if canonical_sha256(record.get("output")) != entry.get("output_sha256"):
        return None, "checkpoint_output_changed"
    contract_errors = _selector_map_record_errors(
        record, request, llm_contract
    )
    record = _bind_framework_map_coverage(record, coverage)
    _, validation_errors = _validate_selection_map_record(
        record,
        coverage,
        known_cell_ids,
        known_object_ids,
        known_source_ids,
    )
    if contract_errors or validation_errors:
        return None, "checkpoint_record_validation_failed"
    record = {
        **record,
        "result_path": str(record_path),
        "request_path": str(prompt_path),
    }
    return record, "semantic_checkpoint_reuse"


def _write_selector_map_checkpoint(
    out_dir: Path,
    requests: list[dict[str, Any]],
    descriptors: list[dict[str, Any]],
    records: list[dict[str, Any]],
    reused: list[bool],
    llm_contract: dict[str, Any],
) -> dict[str, Any]:
    if not requests:
        raise ValueError("selector map checkpoint has no validated records")
    llm_dir = (out_dir / "llm").resolve()
    chunks = []
    for request, descriptor, record, was_reused in zip(
        requests, descriptors, records, reused, strict=True
    ):
        record_path = Path(str(record.get("result_path") or ""))
        prompt_path = Path(str(record.get("request_path") or ""))
        try:
            record_path.resolve(strict=True).relative_to(llm_dir)
            prompt_path.resolve(strict=True).relative_to(llm_dir)
        except (FileNotFoundError, ValueError) as exc:
            raise ValueError(
                f"selector map checkpoint artifact is missing/outside LLM directory: {exc}"
            ) from exc
        prompt_digest = sha256_file(prompt_path)
        if record.get("prompt_hash") != prompt_digest:
            raise ValueError(
                f"selector map checkpoint prompt/result hash mismatch: {request['agent']}"
            )
        contract_errors = _selector_map_record_errors(
            record, request, llm_contract
        )
        if contract_errors:
            raise ValueError("; ".join(contract_errors))
        payload = descriptor["payload"]
        stable_inputs = payload["stable_inputs"]
        chunk = stable_inputs["chunk"]
        global_coverage_commitment = stable_inputs[
            "global_coverage_commitment"
        ]
        chunks.append(
            {
                "chunk_index": chunk["chunk_index"],
                "chunk_count": chunk["chunk_count"],
                "agent": request["agent"],
                "semantic_fingerprint": descriptor["fingerprint"],
                "fingerprint_components": _selector_map_fingerprint_components(
                    descriptor, llm_contract
                ),
                "record_file": f"{request['agent']}_result.json",
                "record_artifact_path": str(
                    record_path.resolve().relative_to(llm_dir)
                ),
                "record_sha256": sha256_file(record_path),
                "output_sha256": canonical_sha256(record.get("output")),
                "prompt_file": f"{request['agent']}_prompt.md",
                "prompt_artifact_path": str(
                    prompt_path.resolve().relative_to(llm_dir)
                ),
                "origin_prompt_sha256": prompt_digest,
                "origin_exact_prompt_validated": True,
                "last_materialization_source": (
                    "semantic_checkpoint" if was_reused else "exact_prompt"
                ),
            }
        )
    expected_chunk_count = int(
        requests[0]["inputs"]["chunk"]["chunk_count"]
    )
    path = _selector_map_checkpoint_path(out_dir)
    existing_chunks: list[dict[str, Any]] = []
    if path.is_file():
        try:
            existing = read_json(path)
        except Exception:
            existing = {}
        if (
            existing.get("schema_version") == SELECTOR_MAP_CHECKPOINT_SCHEMA_VERSION
            and not _selector_map_checkpoint_manifest_errors(
                existing, expected_chunk_count
            )
        ):
            existing_chunks = [
                row
                for row in existing.get("chunks", [])
                if isinstance(row, dict)
            ]
    by_index = {
        int(row["chunk_index"]): row
        for row in existing_chunks
        if isinstance(row.get("chunk_index"), int)
    }
    by_index.update({int(row["chunk_index"]): row for row in chunks})
    chunks = [by_index[index] for index in sorted(by_index)]
    complete = [row["chunk_index"] for row in chunks] == list(
        range(expected_chunk_count)
    )
    manifest = {
        "schema_version": SELECTOR_MAP_CHECKPOINT_SCHEMA_VERSION,
        "status": "pass" if complete else "partial",
        "purpose": "reuse validated map semantics across nonsemantic Vivado export churn",
        "stable_fingerprint_includes": [
            "all projected Vivado structural evidence units and properties",
            "all sample simulation source manifest rows and source hashes",
            "normalized simulator export context relative paths, complete text, and normalized text hashes preserving VCS libraries/includes/defines/options/SW build/real source paths",
            "target board profile",
            "chunk index/count and exact assigned/global coverage commitments",
            "map agent/stage/task/prompt rules/output schema/fallback contract",
            "model/reasoning/prompt protocol/system/action registry/LLM policy contract",
        ],
        "excluded_only_as_proven_ephemeral": [
            "raw Vivado fact byte hash containing export-script churn",
            "simulator export path prefix before /vcs_export/",
            "the '# Generated by Vivado on ...' timestamp line",
        ],
        "llm_contract": _selector_map_semantic_llm_contract(llm_contract),
        "transport_provenance": _selector_map_transport_provenance(llm_contract),
        "chunk_count": expected_chunk_count,
        "chunks": chunks,
    }
    write_json(path, manifest)
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def _semantic_selection_review(output: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in output.items()
        if key not in {"reviewed_object_ids", "reviewed_source_ids"}
    }


def _lossless_reduce_candidates(
    output: dict[str, Any], child_reviews: list[dict[str, Any]]
) -> dict[str, Any]:
    """Retain validated map candidates when a reducer omits redundant rows."""

    merged = json.loads(json.dumps(output))
    for key, id_key in (
        ("candidate_cells", "cell_id"),
        ("candidate_wrapper_sources", "source_id"),
        ("candidate_relevant_sources", "source_id"),
        ("candidate_replacement_sources", "source_id"),
    ):
        rows = merged.get(key)
        if not isinstance(rows, list):
            rows = []
        seen = {
            str(row.get(id_key) or "")
            for row in rows
            if isinstance(row, dict) and str(row.get(id_key) or "")
        }
        for review in child_reviews:
            for row in review.get(key, []):
                if not isinstance(row, dict):
                    continue
                identifier = str(row.get(id_key) or "")
                if identifier and identifier not in seen:
                    rows.append(json.loads(json.dumps(row)))
                    seen.add(identifier)
        merged[key] = rows
    return merged


def _validate_selection_reduce_record(
    record: dict[str, Any],
    expected_coverage: dict[str, list[str]],
    child_reviews: list[dict[str, Any]],
    known_cell_ids: set[str],
    known_source_ids: set[str],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if record.get("error") or record.get("used_fallback") is True:
        errors.append(f"progressive selector reduction LLM failed: {record.get('error')}")
    output = record.get("output") if isinstance(record.get("output"), dict) else {}
    if output.get("schema_version") != SELECTION_REDUCE_SCHEMA_VERSION:
        errors.append("progressive selector returned an unsupported reduction schema")
    if output.get("status") not in {"pass", "ready"}:
        errors.append(
            f"progressive selector reduction status is not ready/pass: {output.get('status')}"
        )
    errors.extend(
        f"progressive selector reduction blocker: {value}"
        for value in output.get("blockers", [])
    )

    evidence_objects = set(expected_coverage.get("object_ids", []))
    evidence_sources = set(expected_coverage.get("source_ids", []))
    child_cell_ids = {
        str(row.get("cell_id") or "")
        for review in child_reviews
        for row in review.get("candidate_cells", [])
        if isinstance(row, dict) and str(row.get("cell_id") or "")
    }
    child_source_ids = {
        key: {
            str(row.get("source_id") or "")
            for review in child_reviews
            for row in review.get(key, [])
            if isinstance(row, dict) and str(row.get("source_id") or "")
        }
        for key in (
            "candidate_wrapper_sources",
            "candidate_relevant_sources",
            "candidate_replacement_sources",
        )
    }
    child_evidence_objects: set[str] = set()
    child_evidence_sources: set[str] = set()
    for review in child_reviews:
        for key in (
            "candidate_cells",
            "candidate_wrapper_sources",
            "candidate_relevant_sources",
            "candidate_replacement_sources",
            "findings",
        ):
            for row in review.get(key, []):
                if not isinstance(row, dict):
                    continue
                child_evidence_objects.update(
                    str(value)
                    for value in row.get("evidence_object_ids", [])
                    if str(value)
                )
                child_evidence_sources.update(
                    str(value)
                    for value in row.get("evidence_source_ids", [])
                    if str(value)
                )
    for row in output.get("candidate_cells", []):
        if not isinstance(row, dict) or str(row.get("cell_id") or "") not in known_cell_ids:
            errors.append("progressive selector reduction cited an unknown candidate cell")
            continue
        if str(row.get("cell_id") or "") not in child_cell_ids:
            errors.append("progressive selector reduction invented a candidate cell absent from its children")
        object_refs = {
            str(value) for value in row.get("evidence_object_ids", []) if str(value)
        }
        source_refs = {
            str(value) for value in row.get("evidence_source_ids", []) if str(value)
        }
        if not object_refs.issubset(evidence_objects) or not source_refs.issubset(
            evidence_sources
        ):
            errors.append(
                "progressive selector reduction candidate cell cites evidence outside its child coverage"
            )
        if not object_refs.issubset(child_evidence_objects) or not source_refs.issubset(
            child_evidence_sources
        ):
            errors.append(
                "progressive selector reduction candidate cell cites evidence absent from child semantics"
            )
    for key in (
        "candidate_wrapper_sources",
        "candidate_relevant_sources",
        "candidate_replacement_sources",
    ):
        for row in output.get(key, []):
            if not isinstance(row, dict) or str(row.get("source_id") or "") not in known_source_ids:
                errors.append(f"progressive selector reduction {key} cites an unknown source")
                continue
            if str(row.get("source_id") or "") not in child_source_ids[key]:
                errors.append(
                    f"progressive selector reduction {key} invented a source absent from its children"
                )
            object_refs = {
                str(value) for value in row.get("evidence_object_ids", []) if str(value)
            }
            source_refs = {
                str(value) for value in row.get("evidence_source_ids", []) if str(value)
            }
            if not object_refs.issubset(evidence_objects) or not source_refs.issubset(
                evidence_sources
            ):
                errors.append(
                    f"progressive selector reduction {key} cites evidence outside its child coverage"
                )
            if not object_refs.issubset(child_evidence_objects) or not source_refs.issubset(
                child_evidence_sources
            ):
                errors.append(
                    f"progressive selector reduction {key} cites evidence absent from child semantics"
                )
    for row in output.get("findings", []):
        if not isinstance(row, dict):
            errors.append("progressive selector reduction returned a malformed finding")
            continue
        object_refs = {
            str(value) for value in row.get("evidence_object_ids", []) if str(value)
        }
        source_refs = {
            str(value) for value in row.get("evidence_source_ids", []) if str(value)
        }
        if not object_refs.issubset(evidence_objects) or not source_refs.issubset(
            evidence_sources
        ):
            errors.append(
                "progressive selector reduction finding cites evidence outside its child coverage"
            )
        if not object_refs.issubset(child_evidence_objects) or not source_refs.issubset(
            child_evidence_sources
        ):
            errors.append(
                "progressive selector reduction finding cites evidence absent from child semantics"
            )
    return output, errors


def _validate_progressive_final_selection(
    selector: dict[str, Any],
    reviews: list[dict[str, Any]],
    human_approval: dict[str, Any] | None = None,
) -> list[str]:
    output = selector.get("output") if isinstance(selector.get("output"), dict) else {}
    if output.get("status") not in {"pass", "ready"}:
        return []
    candidate_cells = {
        str(row.get("cell_id") or "")
        for review in reviews
        for row in review.get("candidate_cells", [])
        if isinstance(row, dict) and str(row.get("cell_id") or "")
    }
    wrapper_sources = {
        str(row.get("source_id") or "")
        for review in reviews
        for row in review.get("candidate_wrapper_sources", [])
        if isinstance(row, dict) and str(row.get("source_id") or "")
    }
    relevant_sources = {
        str(row.get("source_id") or "")
        for review in reviews
        for key in (
            "candidate_wrapper_sources",
            "candidate_relevant_sources",
            "candidate_replacement_sources",
        )
        for row in review.get(key, [])
        if isinstance(row, dict) and str(row.get("source_id") or "")
    }
    errors: list[str] = []
    if human_approval:
        decision = (
            human_approval.get("decision")
            if isinstance(human_approval.get("decision"), dict)
            else {}
        )
        approved_cells = {
            str(value)
            for value in decision.get("approved_candidate_cell_ids", [])
            if str(value)
        }
        if decision.get("status") != "approved":
            errors.append("board-selection human approval status is not approved")
        if decision.get("action_id") != "repair.board_target_selection_with_bounded_approval":
            errors.append("board-selection human approval does not match the pending repair action")
        if decision.get("decision") != "agent_select_exactly_one_of_approved_candidates":
            errors.append("board-selection human approval does not delegate one bounded candidate choice")
        if not approved_cells or not approved_cells.issubset(candidate_cells):
            errors.append("board-selection human approval cites cells outside current progressive evidence")
        if str(output.get("selected_cell_id") or "") not in approved_cells:
            errors.append("final selector chose a cell outside the bounded human approval")
    if str(output.get("selected_cell_id") or "") not in candidate_cells:
        errors.append("final selector chose a cell absent from progressive LLM candidate evidence")
    if str(output.get("wrapper_source_id") or "") not in wrapper_sources:
        errors.append("final selector chose a wrapper absent from progressive LLM candidate evidence")
    selected_relevant = {
        str(value) for value in output.get("relevant_sample_source_ids", []) if str(value)
    }
    if not selected_relevant.issubset(relevant_sources):
        errors.append("final selector added relevant sources absent from progressive LLM candidate evidence")
    selected_replacement = {
        str(value) for value in output.get("proposed_replaced_source_ids", []) if str(value)
    }
    if not selected_replacement.issubset(relevant_sources):
        errors.append(
            "final selector added replacement sources absent from progressive LLM source-candidate evidence"
        )
    return errors


def _reuse_domain_validated_selector_checkpoint(
    out_dir: Path,
    facts: dict[str, Any],
    profile: dict[str, Any],
    sample_rows: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    human_approval: dict[str, Any] | None,
) -> dict[str, Any] | None:
    checkpoint_path = (
        out_dir / "llm" / "exact_board_interface_domain_repair_agent_result.json"
    )
    if not checkpoint_path.is_file():
        return None
    checkpoint = read_json(checkpoint_path)
    checkpoint_output = (
        checkpoint.get("output")
        if isinstance(checkpoint.get("output"), dict)
        else {}
    )
    selection = (
        checkpoint.get("validated_selection")
        if isinstance(checkpoint.get("validated_selection"), dict)
        else {}
    )
    if (
        checkpoint.get("error")
        or checkpoint.get("used_fallback") is True
        or checkpoint_output.get("status") not in {"pass", "ready"}
        or not selection
    ):
        return None
    _, interpretation_errors = validate_interpretation(
        checkpoint, facts, profile, [dict(row) for row in sample_rows]
    )
    if interpretation_errors:
        return None
    selector_path = (
        out_dir / "llm" / "exact_board_interface_selector_agent_result.json"
    )
    selector = {
        "schema_version": "spatialaccagent.stage_worker_record.v0",
        "agent": "exact_board_interface_selector_agent",
        "stage": "verification.layer3.board_interface_selection",
        "result_path": str(selector_path.resolve()),
        "prompt_hash": canonical_sha256(
            {
                "checkpoint_sha256": sha256_file(checkpoint_path),
                "selection": selection,
            }
        ),
        "used_fallback": False,
        "error": None,
        "output": json.loads(json.dumps(selection)),
        "semantic_checkpoint_reuse": True,
        "semantic_checkpoint_source": {
            "path": str(checkpoint_path.resolve()),
            "sha256": sha256_file(checkpoint_path),
            "domain_prompt_hash": checkpoint.get("prompt_hash"),
        },
    }
    _, selector_errors = _validate_selector_record(selector, facts, sample_rows)
    selector_errors.extend(
        _validate_progressive_final_selection(selector, reviews, human_approval)
    )
    if selector_errors:
        return None
    print(
        "[stage:verification.layer3.board_interface_selection:semantic-checkpoint] "
        "reuse domain-validated final selector output under current evidence and approval",
        file=sys.stderr,
        flush=True,
    )
    return selector


def _blocked_selector_record(
    errors: list[str], records: list[dict[str, Any]], coverage: dict[str, list[str]]
) -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.stage_worker_record.v0",
        "agent": "exact_board_interface_selector_agent",
        "stage": "verification.layer3.board_interface_selection",
        "used_fallback": False,
        "error": "; ".join(errors),
        "result_path": next(
            (str(record.get("result_path")) for record in reversed(records) if record.get("result_path")),
            "",
        ),
        "progressive_selection": {
            "status": "blocked",
            "record_paths": [str(record.get("result_path")) for record in records if record.get("result_path")],
            "reviewed_object_count": len(coverage.get("object_ids", [])),
            "reviewed_source_count": len(coverage.get("source_ids", [])),
        },
        "output": {
            "schema_version": "spatialaccagent.board_interface_selection.v1",
            "agent": "exact_board_interface_selector_agent",
            "stage": "verification.layer3.board_interface_selection",
            "status": "blocked",
            "summary": "Progressive exact-board evidence review did not satisfy its fail-closed contract",
            "selected_cell_id": "",
            "wrapper_source_id": "",
            "relevant_sample_source_ids": [],
            "proposed_replaced_source_ids": [],
            "blockers": errors,
        },
    }


def _write_progressive_coverage_ledger(
    out_dir: Path,
    common: dict[str, Any],
    full_coverage: dict[str, list[str]],
    map_records: list[dict[str, Any]],
    reduction_records: list[dict[str, Any]],
    map_checkpoint: dict[str, Any],
    map_budget_bytes: int,
    reduce_budget_bytes: int,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    llm_dir = (out_dir / "llm").resolve()
    checkpoint_path = Path(str(map_checkpoint.get("path") or ""))
    if (
        not checkpoint_path.is_file()
        or sha256_file(checkpoint_path) != map_checkpoint.get("sha256")
    ):
        return {}, ["selector map semantic checkpoint path/hash is invalid"]
    checkpoint_manifest = read_json(checkpoint_path)
    checkpoint_chunks = (
        checkpoint_manifest.get("chunks")
        if isinstance(checkpoint_manifest.get("chunks"), list)
        else []
    )
    checkpoint_by_agent = {
        str(row.get("agent") or ""): row
        for row in checkpoint_chunks
        if isinstance(row, dict)
    }
    record_rows = []
    for phase, records in (("map", map_records), ("reduce", reduction_records)):
        for record in records:
            path = Path(str(record.get("result_path") or ""))
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(llm_dir)
            except (FileNotFoundError, ValueError):
                errors.append(
                    f"progressive selector {phase} record is missing or outside its LLM artifact directory: {path}"
                )
                continue
            output = record.get("output") if isinstance(record.get("output"), dict) else {}
            coverage = (
                {
                    "object_ids": output.get("reviewed_object_ids", []),
                    "source_ids": output.get("reviewed_source_ids", []),
                }
                if phase == "map"
                else record.get("framework_coverage_overlay", {})
            )
            reviewed_objects = [
                str(value) for value in coverage.get("object_ids", []) if str(value)
            ]
            reviewed_sources = [
                str(value) for value in coverage.get("source_ids", []) if str(value)
            ]
            if len(reviewed_objects) != len(set(reviewed_objects)) or len(
                reviewed_sources
            ) != len(set(reviewed_sources)):
                errors.append(
                    f"progressive selector {phase} record has duplicate framework coverage IDs: {path}"
                )
                continue
            row = {
                "phase": phase,
                "agent": record.get("agent"),
                "path": str(resolved),
                "sha256": sha256_file(resolved),
                "reviewed_object_count": len(reviewed_objects),
                "reviewed_source_count": len(reviewed_sources),
                "reviewed_object_ids_sha256": canonical_sha256(
                    sorted(reviewed_objects)
                ),
                "reviewed_source_ids_sha256": canonical_sha256(
                    sorted(reviewed_sources)
                ),
            }
            if phase == "map":
                checkpoint_chunk = checkpoint_by_agent.get(
                    str(record.get("agent") or "")
                )
                checkpoint_record_path = (
                    _checkpoint_artifact_path(
                        llm_dir,
                        str(checkpoint_chunk.get("record_file") or ""),
                        str(checkpoint_chunk.get("record_artifact_path") or ""),
                        str(checkpoint_chunk.get("record_sha256") or ""),
                    )
                    if isinstance(checkpoint_chunk, dict)
                    else None
                )
                if (
                    not isinstance(checkpoint_chunk, dict)
                    or checkpoint_record_path is None
                    or checkpoint_record_path.resolve() != resolved
                    or checkpoint_chunk.get("record_sha256") != row["sha256"]
                ):
                    errors.append(
                        f"selector map worker is not bound to its semantic checkpoint chunk: {resolved}"
                    )
                    continue
                fingerprint = str(
                    checkpoint_chunk.get("semantic_fingerprint") or ""
                )
                row.update(
                    {
                        "chunk_index": checkpoint_chunk.get("chunk_index"),
                        "semantic_fingerprint": fingerprint,
                        "reuse_authority": {
                            "checkpoint_chunk_index": checkpoint_chunk.get(
                                "chunk_index"
                            ),
                            "checkpoint_semantic_fingerprint": fingerprint,
                            "materialization_source": checkpoint_chunk.get(
                                "last_materialization_source"
                            ),
                        },
                    }
                )
            record_rows.append(row)
    if errors:
        return {}, errors
    object_ids = list(full_coverage.get("object_ids", []))
    source_ids = list(full_coverage.get("source_ids", []))
    ledger = {
        "schema_version": "spatialaccagent.board_interface_selection_coverage.v1",
        "status": "pass",
        "input_vivado_fact_canonical_sha256": common.get("raw_fact_sha256"),
        "map_semantic_checkpoint": map_checkpoint,
        "map_input_budget_bytes": map_budget_bytes,
        "reduce_input_budget_bytes": reduce_budget_bytes,
        "complete_coverage": {
            "reviewed_object_ids": object_ids,
            "reviewed_source_ids": source_ids,
            "reviewed_object_count": len(object_ids),
            "reviewed_source_count": len(source_ids),
            "reviewed_object_ids_sha256": canonical_sha256(sorted(object_ids)),
            "reviewed_source_ids_sha256": canonical_sha256(sorted(source_ids)),
            "all_fact_and_source_units_reviewed": True,
        },
        "worker_records": record_rows,
    }
    path = out_dir / "llm" / "exact_board_interface_selector_progressive_coverage.json"
    write_json(path, ledger)
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}, []


def run_progressive_board_selector(
    run_stage_agent: Any,
    out_dir: Path,
    facts: dict[str, Any],
    profile: dict[str, Any],
    sample_rows: list[dict[str, Any]],
    *,
    human_approval: dict[str, Any] | None = None,
    map_budget_bytes: int = SELECTOR_MAP_INPUT_BUDGET_BYTES,
    reduce_budget_bytes: int = SELECTOR_REDUCE_INPUT_BUDGET_BYTES,
) -> dict[str, Any]:
    common, units = selection_evidence_units(facts, sample_rows)
    full_coverage = _coverage_from_units(units)
    object_ids = full_coverage["object_ids"]
    source_ids = full_coverage["source_ids"]
    known_object_ids = set(object_ids)
    known_source_ids = set(source_ids)
    known_cell_ids = {
        str(unit.get("evidence", {}).get("object_id") or "")
        for unit in units
        if unit.get("unit_kind") == "vivado_cell_with_all_owned_ports"
    }
    known_cell_ids.discard("")
    object_occurrences = [
        str(value)
        for unit in units
        for value in unit.get("object_ids", [])
        if str(value)
    ]
    source_occurrences = [
        str(value)
        for unit in units
        for value in unit.get("source_ids", [])
        if str(value)
    ]
    if len(object_occurrences) != len(set(object_occurrences)) or len(source_occurrences) != len(set(source_occurrences)):
        return _blocked_selector_record(
            ["progressive selector evidence partition contains duplicate object/source ownership"],
            [],
            full_coverage,
        )
    try:
        chunks = _partition_by_size(units, map_budget_bytes)
    except ValueError as exc:
        return _blocked_selector_record([str(exc)], [], full_coverage)

    map_records: list[dict[str, Any]] = []
    review_nodes: list[dict[str, Any]] = []
    map_requests: list[dict[str, Any]] = []
    map_descriptors: list[dict[str, Any]] = []
    map_reused: list[bool] = []
    llm_contract = _selector_map_llm_contract()
    normalized_export_contexts = _normalize_selector_export_contexts(facts)
    for index, chunk in enumerate(chunks):
        coverage = _coverage_from_units(chunk)
        request = _selector_map_request(
            out_dir,
            common,
            profile,
            chunk,
            index,
            len(chunks),
            full_coverage,
        )
        descriptor = _selector_map_semantic_descriptor(
            request, llm_contract, normalized_export_contexts
        )
        record, reuse_reason = _reuse_selector_map_checkpoint(
            out_dir,
            request,
            descriptor,
            coverage,
            known_cell_ids,
            known_object_ids,
            known_source_ids,
            llm_contract,
        )
        was_reused = record is not None
        origin_request = request
        if record is None:
            record = run_stage_agent(**request)
        else:
            print(
                f"[stage:{request['stage']}:semantic-checkpoint] reuse "
                f"{request['agent']}: {reuse_reason}",
                file=sys.stderr,
                flush=True,
            )
        repair_attempt = 0
        while True:
            record = _bind_framework_map_coverage(record, coverage)
            output, errors = _validate_selection_map_record(
                record,
                coverage,
                known_cell_ids,
                known_object_ids,
                known_source_ids,
            )
            if not errors:
                break
            original_error = record.get("error")
            record["deterministic_validation_errors"] = list(errors)
            record["error"] = (
                "deterministic progressive-map validation failed: "
                + "; ".join(errors)
            )
            record_path = Path(str(record.get("result_path") or ""))
            try:
                record_path.resolve().relative_to((out_dir / "llm").resolve())
            except ValueError:
                pass
            else:
                write_json(record_path, record)
                archive_path = record_path.with_name(
                    f"{record_path.stem}_deterministic_invalid_{repair_attempt:03d}.json"
                )
                write_json(archive_path, record)
            if original_error or record.get("used_fallback") is True:
                return _blocked_selector_record(
                    errors, [*map_records, record], full_coverage
                )
            repair_attempt += 1
            origin_request = {
                **request,
                "task": (
                    f"{SELECTOR_MAP_TASK} Repair the preceding candidate output so it satisfies "
                    "the exact assigned-coverage contract without dropping supported in-chunk evidence."
                ),
                "inputs": {
                    **request["inputs"],
                    "candidate_output": output,
                    "deterministic_validation_errors": errors,
                    "deterministic_repair_attempt": repair_attempt,
                },
                "prompt_rules": [
                    *SELECTOR_MAP_PROMPT_RULES,
                    "Repair every deterministic_validation_errors entry. candidate_output is only the previous attempt, not authoritative evidence.",
                    "For every candidate source row, both source_id and every evidence_source_ids entry must belong to chunk.assigned_coverage.source_ids. simulation_source_ids embedded inside an assigned Vivado object are cross-references, not source evidence owned by this chunk; leave those source nominations to the chunk that owns their source records.",
                    "Do not hide an in-chunk candidate merely to pass validation. Preserve all supportable candidates and findings using assigned object/source IDs, and defer only claims whose required evidence belongs to another chunk.",
                ],
            }
            record = run_stage_agent(**origin_request)
            was_reused = False
        record["deterministic_validation_status"] = "pass"
        record["deterministic_validation_errors"] = []
        record["deterministic_repair_attempt"] = repair_attempt
        record_path = Path(str(record.get("result_path") or ""))
        try:
            record_path.resolve().relative_to((out_dir / "llm").resolve())
        except ValueError:
            pass
        else:
            write_json(record_path, record)
        map_requests.append(origin_request)
        map_descriptors.append(descriptor)
        map_reused.append(was_reused)
        map_records.append(record)
        review_nodes.append(
            {
                "semantic_output": _semantic_selection_review(output),
                "coverage": coverage,
            }
        )
        try:
            _write_selector_map_checkpoint(
                out_dir,
                map_requests,
                map_descriptors,
                map_records,
                map_reused,
                llm_contract,
            )
        except ValueError as exc:
            return _blocked_selector_record(
                [str(exc)], map_records, full_coverage
            )

    try:
        map_checkpoint = _write_selector_map_checkpoint(
            out_dir,
            map_requests,
            map_descriptors,
            map_records,
            map_reused,
            llm_contract,
        )
    except ValueError as exc:
        return _blocked_selector_record(
            [str(exc)], map_records, full_coverage
        )

    reduction_records: list[dict[str, Any]] = []
    reduction_level = 0
    while _compact_size(
        [node["semantic_output"] for node in review_nodes]
    ) > reduce_budget_bytes:
        semantic_outputs = [node["semantic_output"] for node in review_nodes]
        node_by_output_id = {id(node["semantic_output"]): node for node in review_nodes}
        try:
            groups = _partition_by_size(semantic_outputs, reduce_budget_bytes)
        except ValueError as exc:
            return _blocked_selector_record(
                [str(exc)], [*map_records, *reduction_records], full_coverage
            )
        reduced_nodes: list[dict[str, Any]] = []
        previous_size = _compact_size(semantic_outputs)
        for group_index, group in enumerate(groups):
            child_nodes = [node_by_output_id[id(output)] for output in group]
            coverage = _merge_coverages(
                node["coverage"] for node in child_nodes
            )
            record = run_stage_agent(
                agent=(
                    f"exact_board_interface_selector_reduce_{reduction_level:02d}_{group_index:03d}_agent"
                ),
                stage="verification.layer3.board_interface_selection.reduce",
                task=(
                    "Losslessly merge evidence-bound candidates from progressive selector map/reduce workers "
                    "without choosing the final board interface yet."
                ),
                inputs={
                    "global_vivado_context": common,
                    "target_board_profile": profile,
                    "child_coverage_commitment": {
                        "object_count": len(coverage["object_ids"]),
                        "source_count": len(coverage["source_ids"]),
                        "object_ids_sha256": canonical_sha256(
                            sorted(coverage["object_ids"])
                        ),
                        "source_ids_sha256": canonical_sha256(
                            sorted(coverage["source_ids"])
                        ),
                        "coverage_owned_by_framework": True,
                    },
                    "semantic_map_or_reduce_outputs": group,
                },
                out_dir=out_dir,
                fallback_summary="Exact board selection reduction requires the configured LLM agent.",
                output_schema=BOARD_INTERFACE_SELECTION_REDUCE_SCHEMA,
                prompt_rules=[
                    "Merge duplicate findings, but retain every evidence-supported alternative needed by the final selector. Never invent or silently discard a plausible cell or source candidate.",
                    "The child workers already reviewed their raw evidence. Reason only from their cited findings and preserve the union of their evidence provenance.",
                    "Merge semantic candidates and findings only. The deterministic framework owns the exact child coverage ledger; do not return reviewed_object_ids or reviewed_source_ids.",
                    "Cite only evidence IDs already present in child semantic outputs. The framework validates every citation against the exact child coverage outside this prompt.",
                    "Do not use filename or module-name keyword rules and do not choose future generated accelerator internals.",
                    "Keep the merged output substantially smaller than the inputs while retaining decision-relevant distinctions and blockers.",
                    f"Set schema_version exactly to {SELECTION_REDUCE_SCHEMA_VERSION}.",
                    "Return one JSON object only.",
                ],
            )
            reduction_records.append(record)
            output, errors = _validate_selection_reduce_record(
                record,
                coverage,
                group,
                known_cell_ids,
                known_source_ids,
            )
            if errors:
                return _blocked_selector_record(
                    errors, [*map_records, *reduction_records], full_coverage
                )
            output = _lossless_reduce_candidates(output, group)
            record["output"] = output
            record["framework_coverage_overlay"] = coverage
            record["semantic_output_sha256"] = canonical_sha256(output)
            record_path = Path(str(record.get("result_path") or ""))
            try:
                record_path.resolve().relative_to((out_dir / "llm").resolve())
            except ValueError:
                return _blocked_selector_record(
                    ["progressive selector reduction record path is outside its LLM artifact directory"],
                    [*map_records, *reduction_records],
                    full_coverage,
                )
            write_json(record_path, record)
            reduced_nodes.append(
                {
                    "semantic_output": output,
                    "coverage": coverage,
                }
            )
        reduced_semantic_outputs = [
            node["semantic_output"] for node in reduced_nodes
        ]
        reduced_size = _compact_size(reduced_semantic_outputs)
        if len(reduced_nodes) >= len(review_nodes) and reduced_size >= previous_size:
            return _blocked_selector_record(
                ["LLM progressive selector reduction did not reduce the context payload"],
                [*map_records, *reduction_records],
                full_coverage,
            )
        review_nodes = reduced_nodes
        reduction_level += 1

    semantic_reviews = [node["semantic_output"] for node in review_nodes]

    coverage_ledger, ledger_errors = _write_progressive_coverage_ledger(
        out_dir,
        common,
        full_coverage,
        map_records,
        reduction_records,
        map_checkpoint,
        map_budget_bytes,
        reduce_budget_bytes,
    )
    if ledger_errors:
        return _blocked_selector_record(
            ledger_errors, [*map_records, *reduction_records], full_coverage
        )

    selector = _reuse_domain_validated_selector_checkpoint(
        out_dir,
        facts,
        profile,
        sample_rows,
        semantic_reviews,
        human_approval,
    )
    selector_request = {
        "agent": "exact_board_interface_selector_agent",
        "stage": "verification.layer3.board_interface_selection",
        "task": (
            "Select the exact sample-wrapper source, replaceable compute-slot cell, minimal exclusive slot "
            "instance-boundary sources, relevant control/timing/memory sample sources, and exact replacement "
            "boundary from the complete progressive Vivado/source evidence review."
        ),
        "inputs": {
            "global_vivado_context": common,
            "target_board_profile": profile,
            "progressive_evidence_reviews": semantic_reviews,
            **(
                {"human_board_selection_approval": human_approval}
                if human_approval
                else {}
            ),
            "complete_coverage": {
                "object_count": len(object_ids),
                "source_count": len(source_ids),
                "object_ids_sha256": canonical_sha256(sorted(object_ids)),
                "source_ids_sha256": canonical_sha256(sorted(source_ids)),
                "all_fact_and_source_units_reviewed": True,
                "coverage_ledger": coverage_ledger,
                "map_semantic_checkpoint": map_checkpoint,
            },
        },
        "out_dir": out_dir,
        "fallback_summary": "Exact compute-slot selection requires the configured LLM agent.",
        "output_schema": BOARD_INTERFACE_SELECTION_SCHEMA,
        "prompt_rules": [
            "You are the final adaptive board-interface selector. Every selection-projection Vivado object and every hash-bound sample source has been reviewed by the supplied map/reduce agents; compare all evidence-bound alternatives before selecting.",
            "Select by cited Vivado properties, interface metadata, connectivity, ownership, hashes, and source provenance. Never use a filename/module-name keyword rule, target-model name, hardcoded board name, or static keyword list.",
            "Return IDs only when they appear in the progressive evidence reviews. If the reviews do not support exactly one compute-slot/wrapper boundary and no bounded human approval resolves that exact candidate tie, return status=blocked; never guess.",
            "When human_board_selection_approval is supplied with an approved decision delegating one choice, select exactly one approved_candidate_cell_id yourself. That approval resolves only the cited candidate multiplicity; every wrapper, source, ABI, timing, AXI, and replacement-boundary claim must still be proved by the supplied evidence.",
            "relevant_sample_source_ids must include the wrapper and every cited source needed by the downstream domain agent to prove slot exclusivity, control semantics/field layout, clock/reset/calibration, and DDR timing/backpressure.",
            "proposed_replaced_source_ids is the minimal evidence-bounded candidate handoff for full-source review. When map evidence proves a source is exclusively owned by the selected cell and is a simulator-fa\u00e7ade candidate, emit it here with status=selected and no blocker even though module/instance proof is pending; the following full-source review and domain agent must prove or reject that boundary. Do not claim that this handoff is final proof. A selected-cell simulation wrapper that exclusively declares CONFIG.Component_Name is a valid compile-delta boundary even when it instantiates shared legacy compute RTL.",
            "Retain shared compute RTL for other sample instances. Do not require the exclusive instance-boundary wrapper to contain the complete legacy implementation, and never replace shared shell, DDR, interconnect, testbench, memory-model, or compute sources.",
            "Discovery ends at the existing sample compute-slot boundary. Do not select or name future generated accelerator modules, instances, or sources.",
            "Return one JSON object only.",
        ],
    }
    if selector is None:
        selector = run_stage_agent(**selector_request)
    final_selection_errors = _validate_progressive_final_selection(
        selector, semantic_reviews, human_approval
    )
    if (
        final_selection_errors
        and not selector.get("error")
        and selector.get("used_fallback") is not True
    ):
        correction_request = {
            **selector_request,
            "task": (
                f"{selector_request['task']} Repair the previous selector output using only "
                "the supplied progressive evidence reviews."
            ),
            "inputs": {
                **selector_request["inputs"],
                "candidate_output": selector.get("output", {}),
                "deterministic_validation_errors": final_selection_errors,
            },
            "prompt_rules": [
                *selector_request["prompt_rules"],
                "The previous output failed deterministic evidence binding. Repair every listed error; do not add any ID that is absent from the progressive reviews, and return status=blocked if the reviews do not support the required claim.",
            ],
        }
        selector = run_stage_agent(**correction_request)
        final_selection_errors = _validate_progressive_final_selection(
            selector, semantic_reviews, human_approval
        )
    if final_selection_errors:
        selector["error"] = "; ".join(
            [str(selector.get("error") or ""), *final_selection_errors]
        ).strip("; ")
    selector["progressive_selection"] = {
        "status": "pass" if not final_selection_errors else "blocked",
        "map_chunk_count": len(chunks),
        "reduction_record_count": len(reduction_records),
        "reviewed_object_count": len(object_ids),
        "reviewed_source_count": len(source_ids),
        "object_ids_sha256": canonical_sha256(sorted(object_ids)),
        "source_ids_sha256": canonical_sha256(sorted(source_ids)),
        "coverage_ledger": coverage_ledger,
        "map_semantic_checkpoint": map_checkpoint,
        "validation_errors": final_selection_errors,
        "record_paths": [
            str(record.get("result_path"))
            for record in [*map_records, *reduction_records]
            if record.get("result_path")
        ],
    }
    selector_path = Path(str(selector.get("result_path") or ""))
    try:
        selector_path.resolve().relative_to((out_dir / "llm").resolve())
    except ValueError:
        return _blocked_selector_record(
            ["final selector record path is outside its LLM artifact directory"],
            [*map_records, *reduction_records, selector],
            full_coverage,
        )
    write_json(selector_path, selector)
    return selector


def selected_fact_subgraph(facts: dict[str, Any], selected_cell_id: str) -> dict[str, Any]:
    projection = llm_fact_projection(facts, include_source_catalog=False)
    simulation = projection.get("simulation")
    if isinstance(simulation, dict):
        simulation["simulator_export_contexts"] = [
            {
                key: value
                for key, value in row.items()
                if key != "text"
            }
            for row in simulation.get("simulator_export_contexts", [])
            if isinstance(row, dict)
        ]
        simulation["domain_prompt_projection"] = {
            "compile_script_text_retained_in_raw_vivado_facts": True,
            "compile_script_text_consumed_by_compile_authority_not_domain_abi_agent": True,
        }
    objects = {
        str(row.get("object_id")): row
        for row in projection.get("objects", [])
        if isinstance(row, dict)
    }
    selected = objects.get(selected_cell_id)
    if not selected:
        return {**projection, "objects": []}
    included_ids = {selected_cell_id}
    selected_children = [
        row
        for row in objects.values()
        if row.get("bd_path") == selected.get("bd_path")
        and row.get("owner_path") == selected.get("path")
    ]
    included_ids.update(str(row.get("object_id")) for row in selected_children)
    net_keys = {
        (str(net.get("kind")), str(net.get("path")))
        for row in selected_children
        for net in row.get("connected_nets", [])
    }
    net_objects = [
        row
        for row in objects.values()
        if row.get("bd_path") == selected.get("bd_path")
        and (str(row.get("kind")), str(row.get("path"))) in net_keys
    ]
    included_ids.update(str(row.get("object_id")) for row in net_objects)
    endpoint_paths = {
        str(member.get("path"))
        for row in net_objects
        for member in row.get("members", [])
    }
    endpoints = [
        row
        for row in objects.values()
        if row.get("bd_path") == selected.get("bd_path") and str(row.get("path")) in endpoint_paths
    ]
    included_ids.update(str(row.get("object_id")) for row in endpoints)
    endpoint_owners = {str(row.get("owner_path")) for row in endpoints if row.get("owner_path")}
    included_ids.update(
        str(row.get("object_id"))
        for row in objects.values()
        if row.get("kind") == "cell"
        and row.get("bd_path") == selected.get("bd_path")
        and str(row.get("path")) in endpoint_owners
    )
    return {
        **projection,
        "objects": [row for object_id, row in objects.items() if object_id in included_ids],
        "subgraph": {
            "selected_cell_id": selected_cell_id,
            "scope": "selected cell, all owned ports/interfaces, directly connected nets/endpoints, and endpoint owner cells",
            "object_count": len(included_ids),
        },
    }


def selected_cell_pin_index(facts: dict[str, Any], selected_cell_id: str) -> list[dict[str, Any]]:
    """Expose an unambiguous compact pin index for the domain Agent."""
    objects = _object_index(facts)
    cell = objects.get(str(selected_cell_id))
    if not cell:
        return []
    rows = [
        row for row in objects.values()
        if row.get("owner_path") == cell.get("path")
        and row.get("kind") in {"pin", "interface_pin"}
    ]
    return [
        {
            "object_id": str(row.get("object_id")),
            "kind": row.get("kind"),
            "path": row.get("path"),
            "name": row.get("properties", {}).get("NAME"),
            "direction": _direction(str(row.get("properties", {}).get("DIR") or "")),
            "width_bits": _width(row),
            "interface": row.get("properties", {}).get("INTF"),
            "type": row.get("properties", {}).get("TYPE"),
            "config_properties": {
                key: value
                for key, value in row.get("properties", {}).items()
                if str(key).startswith("CONFIG.")
            },
            "default_driver": row.get("properties", {}).get("DEFAULT_DRIVER"),
        }
        for row in sorted(rows, key=lambda item: str(item.get("path")))
    ]


def materialize_existing_selector_map_checkpoint(
    run_dir: Path, out_dir: Path
) -> dict[str, Any]:
    facts_path = out_dir / "vivado_board_facts.json"
    identity_path = out_dir / "board_source_identity.json"
    profile_path = run_dir / "input" / "target_board_profile.json"
    facts = read_json(facts_path)
    identity = read_json(identity_path)
    profile = read_json(profile_path)
    sample_rows = [
        row
        for row in identity.get("materialized_sources", [])
        if isinstance(row, dict)
    ]
    if not facts or not profile or not sample_rows:
        raise ValueError(
            "selector map checkpoint bootstrap requires current Vivado facts, target profile, and materialized sources"
        )
    common, units = selection_evidence_units(facts, sample_rows)
    full_coverage = _coverage_from_units(units)
    chunks = _partition_by_size(units, SELECTOR_MAP_INPUT_BUDGET_BYTES)
    known_object_ids = set(full_coverage["object_ids"])
    known_source_ids = set(full_coverage["source_ids"])
    known_cell_ids = {
        str(unit.get("evidence", {}).get("object_id") or "")
        for unit in units
        if unit.get("unit_kind") == "vivado_cell_with_all_owned_ports"
    }
    known_cell_ids.discard("")
    llm_contract = _selector_map_llm_contract()
    normalized_export_contexts = _normalize_selector_export_contexts(facts)
    requests: list[dict[str, Any]] = []
    descriptors: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        request = _selector_map_request(
            out_dir,
            common,
            profile,
            chunk,
            index,
            len(chunks),
            full_coverage,
        )
        record_path = out_dir / "llm" / f"{request['agent']}_result.json"
        record = read_json(record_path)
        coverage = _coverage_from_units(chunk)
        contract_errors = _selector_map_record_errors(
            record, request, llm_contract
        )
        _, validation_errors = _validate_selection_map_record(
            record,
            coverage,
            known_cell_ids,
            known_object_ids,
            known_source_ids,
        )
        if contract_errors or validation_errors:
            raise ValueError(
                f"selector map checkpoint bootstrap rejected {request['agent']}: "
                + "; ".join([*contract_errors, *validation_errors])
            )
        requests.append(request)
        descriptors.append(
            _selector_map_semantic_descriptor(
                request, llm_contract, normalized_export_contexts
            )
        )
        records.append(record)
    ref = _write_selector_map_checkpoint(
        out_dir,
        requests,
        descriptors,
        records,
        [False] * len(records),
        llm_contract,
    )
    return {
        "status": "pass",
        "checkpoint": ref,
        "chunk_count": len(chunks),
        "reviewed_object_count": len(full_coverage["object_ids"]),
        "reviewed_source_count": len(full_coverage["source_ids"]),
    }


def load_board_selection_approval(run_dir: Path) -> dict[str, Any] | None:
    configured = os.environ.get("SPATIALACC_BOARD_SELECTION_APPROVAL_ARTIFACT", "").strip()
    path = (
        Path(configured).expanduser()
        if configured
        else run_dir / "input" / "board_selection_approval.json"
    )
    if not path.is_file():
        return None
    return {
        "artifact": {
            "path": str(path.resolve()),
            "sha256": sha256_file(path),
        },
        "decision": read_json(path),
    }


def run_board_interface_domain_repair_loop(
    run_stage_agent: Any,
    out_dir: Path,
    facts: dict[str, Any],
    profile: dict[str, Any],
    sample_rows: list[dict[str, Any]],
    domain_inputs: dict[str, Any],
    domain_rules: list[str],
    candidate: dict[str, Any],
    candidate_errors: list[str],
    annotate_and_persist: Any,
    *,
    starting_attempt: int = 0,
) -> dict[str, Any]:
    repair_attempt = starting_attempt
    previous_fingerprint: str | None = None
    stalled_repair_count = 0
    best_candidate = candidate
    best_errors = list(candidate_errors)
    while candidate_errors:
        # A schema-valid blocked contract is an evidence request, not a
        # representation error. Preserve it for Stage-8 capability routing
        # instead of spending unbounded LLM turns trying to format facts that
        # the reviewed sources do not prove.
        blocked_output = candidate.get("output")
        if (
            isinstance(blocked_output, dict)
            and blocked_output.get("status") == "blocked"
            and blocked_output.get("blockers")
            and not blocked_capability_handoff_errors(blocked_output)
        ):
            candidate["deterministic_validation_status"] = "blocked_by_evidence"
            candidate["deterministic_validation_errors"] = list(candidate_errors)
            annotate_and_persist(candidate)
            return candidate
        current_fingerprint = canonical_sha256(
            {
                "candidate": candidate.get("output"),
                "errors": candidate_errors,
            }
        )
        if current_fingerprint == previous_fingerprint:
            stalled_repair_count += 1
        else:
            stalled_repair_count = 0
        previous_fingerprint = current_fingerprint
        if stalled_repair_count >= 2:
            candidate["error"] = (
                "deterministic board-interface repair made no progress after "
                f"{stalled_repair_count + 1} identical candidate(s)"
            )
            candidate["deterministic_validation_status"] = "fail"
            candidate["deterministic_validation_errors"] = list(candidate_errors)
            annotate_and_persist(candidate)
            return candidate
        repair_attempt += 1
        repair = run_stage_agent(
            agent="exact_board_interface_domain_repair_agent",
            stage="verification.layer3.board_interface_discovery.repair",
            task=(
                "Repair the candidate exact board-interface interpretation using the deterministic gate "
                "diagnostics. Preserve every evidence-backed semantic conclusion, change incorrect field "
                "representations or unsupported conclusions, and return the complete corrected contract."
            ),
            inputs={
                **domain_inputs,
                "candidate_interpretation": candidate.get("output"),
                "candidate_prompt_sha256": candidate.get("prompt_hash"),
                "deterministic_validation_errors": candidate_errors,
                "deterministic_repair_attempt": repair_attempt,
            },
            out_dir=out_dir,
            fallback_summary=(
                "Exact board-interface deterministic validation repair requires the configured LLM agent."
            ),
            output_schema=BOARD_INTERFACE_INTERPRETATION_SCHEMA,
            prompt_rules=[
                *domain_rules,
                "Address every deterministic_validation_errors entry. These diagnostics define representation or evidence failures; they do not authorize invented facts, dropped physical ports, synthetic timing, or behavioral substitution.",
                "candidate_interpretation contains useful source-grounded analysis. Preserve correct semantic findings while translating every field, list, ID, width, timing relation, AXI member, and replacement boundary into deterministic_output_contract exactly.",
                "Use the exact enum spellings and scalar/list containers in deterministic_output_contract. In particular AXI clock/reset/calibration fields reference timing-domain names as strings; configuration_fields.register is the exact physical Vivado configuration-bus pin name; access is ro/rw/wo; count is counter; status is status; sampling edges are rising/falling.",
                "Return the entire repaired top-level interpretation, not a patch or an explanation.",
            ],
        )
        repair["repair_source_record_path"] = candidate.get("result_path")
        repair["repair_source_prompt_hash"] = candidate.get("prompt_hash")
        repair["deterministic_repair_attempt"] = repair_attempt
        repair = annotate_and_persist(repair)
        transport_error = repair.get("error") or repair.get("used_fallback") is True
        _, repair_errors = validate_interpretation(
            repair, facts, profile, [dict(row) for row in sample_rows]
        )
        repair["deterministic_validation_status"] = (
            "pass" if not repair_errors else "fail"
        )
        repair["deterministic_validation_errors"] = repair_errors
        if not repair_errors:
            annotate_and_persist(repair)
            return repair
        if transport_error:
            annotate_and_persist(repair)
            return repair
        repair["error"] = (
            f"deterministic board-interface validation failed with {len(repair_errors)} error(s)"
        )
        repair_path = Path(str(repair.get("result_path") or ""))
        try:
            repair_path.resolve().relative_to((out_dir / "llm").resolve())
        except ValueError:
            pass
        else:
            write_json(
                repair_path.with_name(
                    f"{repair_path.stem}_deterministic_invalid_{repair_attempt:03d}.json"
                ),
                repair,
            )
        annotate_and_persist(repair)
        # Keep the best deterministic contract as the next repair input. A
        # complete LLM response can regress previously correct ABI fields;
        # retaining it would make the loop oscillate between representations.
        if len(repair_errors) <= len(best_errors):
            best_candidate = repair
            best_errors = list(repair_errors)
        candidate = best_candidate
        candidate_errors = list(best_errors)
    return candidate


def board_interface_domain_prompt_rules() -> list[str]:
    return [
        "Use only object IDs, properties, connections, compile-order ownership, source hashes, and source context supplied in this request; never rely on module-name or signal-name keyword heuristics.",
        "deterministic_output_contract is the exact machine-readable field and container contract consumed by the generic acceptance gate. Follow it literally while deriving all values and semantics from current evidence.",
        "sample_source_semantic_reviews are deterministic-coverage-checked LLM reviews of every byte of every selector-chosen hash-bound source. Use their exact findings as source evidence and cite only their source IDs; do not claim the source text was omitted.",
        "sample_simulation_source_manifest.complete_source_ids is the immutable complete closure used to construct replacement_boundary.retained_source_ids. relevant_source_records retain detailed provenance for every reviewed source.",
        "The LLM is the adaptive domain expert: select and explain the compute slot and semantic roles. Static framework code will only cross-check your claims against Vivado facts.",
        "Return status=blocked when evidence is genuinely ambiguous or incomplete. Never guess a cell, port role, timing value, source boundary, or generated internal implementation.",
        "required_capabilities is a required top-level field. Return [] for pass/ready. A blocked result without a complete nonempty required_capabilities handoff is invalid and will be returned to you for repair; do not use blocked to avoid binding supplied evidence.",
        "required_capabilities is a required top-level field. Return [] for pass/ready. A blocked result without a complete nonempty required_capabilities handoff is invalid and will be returned to you for repair; do not use blocked to avoid binding supplied evidence.",
        "Select exactly one Vivado cell object. required_ports and port_bindings must cover every physical pin owned by that cell, including full interface members, clocks, resets, calibration, control, and status. accelerator_port denotes the later generated boundary port and may preserve the exact physical boundary name; it does not claim generated RTL already exists.",
        "interface_classifications must cover every interface pin owned by the selected cell. Classify from Vivado VLNV/CONFIG.PROTOCOL properties and connectivity, not names.",
        "For each AXI semantic signal, provide signal_fact_map entries referring to the exact physical pin object ID; use an explicit constant/absent binding only when Vivado properties prove the sideband is disabled.",
        "Every clock/reset/calibration and memory timing claim must cite exact Vivado object/property or hash-bound sample-source evidence. Preserve exact frequencies, phases, reset polarities, calibration traffic gating, latency/backpressure behavior, and startup ordering.",
        "Inside compute_slot_abi return control_abi in exactly the deterministic_output_contract shape, including exact non-interface pin coverage, physical configuration-field projection, six canonical lifecycle roles, timing relations, and an ordered control_sequence list.",
        "An evidence-proved software, testbench, or scheduler sequence is the exact real board operational contract. Set control_sequence_enforcement=external_orchestrator or mixed as appropriate; lack of a hardware total-order FSM is not a blocker.",
        "A dedicated operation-done pin is not required. When completion is exactly observable as a predicate on a physical count/status port, represent done as derived_from_physical_port with the exact predicate and evidence required by deterministic_output_contract; never invent a done pin.",
        "For asynchronous crossings, preserve the exact variable handshake/CDC relation. Report source-domain assertion cycles proved by the source and encode variable acceptance/completion in the canonical timing strings; do not invent a fixed cross-domain latency and do not block merely because absolute phase varies.",
        "compute_slot_abi.control_abi.control_sequence must encode configure -> start -> observe_completion -> clear_completion ordering from current sample sources. If any field access/reset value, lifecycle action, clock domain, event relation, or ordering cannot be proved, return status=blocked.",
        "When status=blocked because immutable evidence is missing, include a required_capabilities array with one explicit producer request per missing evidence class. Each request must contain capability_id, debug_layer, producer_scope, target_modules, required_evidence, and rationale. The producer_scope must identify a real executor-supported read-only evidence producer; do not request RTL edits, infer facts, or omit this handoff.",
        "When status=blocked because immutable evidence is missing, include a required_capabilities array with one explicit producer request per missing evidence class. Each request must contain capability_id, debug_layer, producer_scope, target_modules, required_evidence, and rationale. The producer_scope must identify a real executor-supported read-only evidence producer; do not request RTL edits, infer facts, or omit this handoff.",
        "Every canonical ABI, port, binding, control, timing, AXI interface, parameter and signal claim must carry the evidence fields requested by deterministic_output_contract using only exact Vivado object_ids or sample source_ids supplied in this request. Do not invent semantic evidence identifiers.",
        "Return wrapper_top_module only when it is declared by the selected wrapper source and is the exact sample top instantiated by the simulator flow; do not assume the simulation fileset TOP is the wrapper when it is a testbench.",
                "For every AXI interface return parameter_evidence_refs for all width/burst/alignment/outstanding/byte-order fields and signal_evidence_refs for every AW/W/B/AR/R member. Cite the interface/member Vivado objects and sample source IDs that actually prove each value.",
                "parameter_evidence_refs must be an object mapping every required AXI field name to a non-empty evidence-reference list (for example {\"byte_order\": [\"<object-or-source-id>\"], \"supports_unaligned_access\": [\"<object-or-source-id>\"]}); do not return one flat list. signal_evidence_refs must likewise be the field/channel mapping required by deterministic_output_contract.",
        "selected_simulation_source_closure is immutable and is not your output. replaced_source_ids is only a later compile delta: select the exclusively owned source that declares the selected cell's existing slot_module boundary. It may be a simulation instance wrapper around shared legacy compute RTL; retain that shared RTL for every unselected sample instance.",
        "replacement_boundary.retained_source_ids must be the complete sample closure minus replaced_source_ids; set sample_closure_unchanged=true and generated_sources_excluded_from_sample_closure=true.",
        "Set replacement_module_identity equal to the selected existing slot_module and replacement_instance_boundary equal to the selected existing Vivado cell path. Do not choose or name future generated accelerator internals; the later generation agent owns them.",
        "Set no_behavioral_substitution=true when the exclusive replacement boundary preserves the real sample wrapper, DDR model, AXI path, clocks, resets, calibration behavior, and immutable retained closure. Discovery does not require the future generated scheduler/kernel to already be connected; generation and VCS validate that later binding.",
        "Return one JSON object only.",
    ]


def run_board_interface_agent(
    run_dir: Path,
    out_dir: Path,
    facts: dict[str, Any],
    profile: dict[str, Any],
    sample_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    from accagent.framework.stage_llm import run_stage_agent

    selector = run_progressive_board_selector(
        run_stage_agent,
        out_dir,
        facts,
        profile,
        sample_rows,
        human_approval=load_board_selection_approval(run_dir),
    )
    selection, selector_errors = _validate_selector_record(selector, facts, sample_rows)
    sample_context, sample_context_errors = _full_context(
        sample_rows, selection.get("relevant_sample_source_ids", [])
    )
    selection_errors = [*selector_errors, *sample_context_errors]
    if selection_errors:
        return {
            "schema_version": "spatialaccagent.stage_worker_record.v0",
            "agent": "exact_board_interface_domain_agent",
            "stage": "verification.layer3.board_interface_discovery",
            "used_fallback": False,
            "error": "; ".join(selection_errors),
            "selector_record_path": selector.get("result_path"),
            "output": {
                "schema_version": INTERPRETATION_SCHEMA_VERSION,
                "agent": "exact_board_interface_domain_agent",
                "stage": "verification.layer3.board_interface_discovery",
                "status": "blocked",
                "summary": "LLM selector evidence could not be deterministically validated",
                "wrapper_source_id": str(selection.get("wrapper_source_id") or ""),
                "wrapper_top_module": "",
                "compute_slot_abi": {},
                "timing_contract": {},
                "axi_interfaces": [],
                "blockers": selection_errors,
            },
        }

    source_reviews, source_review_coverage, source_review_errors = (
        run_progressive_board_source_review(
            run_stage_agent,
            out_dir,
            profile,
            selection,
            sample_context,
        )
    )
    if source_review_errors:
        return {
            "schema_version": "spatialaccagent.stage_worker_record.v0",
            "agent": "exact_board_interface_domain_agent",
            "stage": "verification.layer3.board_interface_discovery",
            "used_fallback": False,
            "error": "; ".join(source_review_errors),
            "selector_record_path": selector.get("result_path"),
            "output": {
                "schema_version": INTERPRETATION_SCHEMA_VERSION,
                "agent": "exact_board_interface_domain_agent",
                "stage": "verification.layer3.board_interface_discovery",
                "status": "blocked",
                "summary": "Progressive full-source review did not satisfy its fail-closed contract",
                "wrapper_source_id": str(selection.get("wrapper_source_id") or ""),
                "wrapper_top_module": "",
                "compute_slot_abi": {},
                "timing_contract": {},
                "axi_interfaces": [],
                "blockers": source_review_errors,
            },
        }

    source_manifest = llm_sample_source_manifest(sample_rows)
    relevant_source_ids = {
        str(value)
        for value in selection.get("relevant_sample_source_ids", [])
        if str(value)
    }
    compact_source_manifest = {
        "complete_source_ids": [
            str(row.get("source_id") or "") for row in source_manifest
        ],
        "complete_source_count": len(source_manifest),
        "complete_source_ids_sha256": canonical_sha256(
            sorted(str(row.get("source_id") or "") for row in source_manifest)
        ),
        "relevant_source_records": [
            row
            for row in source_manifest
            if str(row.get("source_id") or "") in relevant_source_ids
        ],
    }
    output_contract = board_interface_domain_output_contract()
    domain_inputs = {
        "vivado_facts": selected_fact_subgraph(
            facts, str(selection.get("selected_cell_id") or "")
        ),
        "selected_cell_pin_index": selected_cell_pin_index(
            facts, str(selection.get("selected_cell_id") or "")
        ),
        "target_board_profile": profile,
        "validated_llm_selection": selection,
        "sample_simulation_source_manifest": compact_source_manifest,
        "sample_source_semantic_reviews": source_reviews,
        "sample_source_review_coverage": source_review_coverage,
        "deterministic_output_contract": output_contract,
    }
    domain_rules = [
        "Use only object IDs, properties, connections, compile-order ownership, source hashes, and source context supplied in this request; never rely on module-name or signal-name keyword heuristics.",
        "Use selected_cell_pin_index as the authoritative compact index for required_ports, port_bindings, and AXI signal_fact_map. Copy each object_id, path, direction, and width_bits exactly; do not invent or omit physical pins.",
        "deterministic_output_contract is the exact machine-readable field and container contract consumed by the generic acceptance gate. Follow it literally while deriving all values and semantics from current evidence.",
        "sample_source_semantic_reviews are deterministic-coverage-checked LLM reviews of every byte of every selector-chosen hash-bound source. Use their exact findings as source evidence and cite only their source IDs; do not claim the source text was omitted.",
        "sample_simulation_source_manifest.complete_source_ids is the immutable complete closure used to construct replacement_boundary.retained_source_ids. relevant_source_records retain detailed provenance for every reviewed source.",
        "The LLM is the adaptive domain expert: select and explain the compute slot and semantic roles. Static framework code will only cross-check your claims against Vivado facts.",
        "Return status=blocked when evidence is genuinely ambiguous or incomplete. Never guess a cell, port role, timing value, source boundary, or generated internal implementation.",
        "Select exactly one Vivado cell object. required_ports and port_bindings must cover every physical pin owned by that cell, including full interface members, clocks, resets, calibration, control, and status. accelerator_port denotes the later generated boundary port and may preserve the exact physical boundary name; it does not claim generated RTL already exists.",
        "interface_classifications must cover every interface pin owned by the selected cell. Classify from Vivado VLNV/CONFIG.PROTOCOL properties and connectivity, not names.",
        "For each AXI semantic signal, provide signal_fact_map entries referring to the exact physical pin object ID; use an explicit constant/absent binding only when Vivado properties prove the sideband is disabled.",
        "Every clock/reset/calibration and memory timing claim must cite exact Vivado object/property or hash-bound sample-source evidence. Preserve exact frequencies, phases, reset polarities, calibration traffic gating, latency/backpressure behavior, and startup ordering.",
        "Inside compute_slot_abi return control_abi in exactly the deterministic_output_contract shape, including exact non-interface pin coverage, physical configuration-field projection, six canonical lifecycle roles, timing relations, and an ordered control_sequence list.",
        "An evidence-proved software, testbench, or scheduler sequence is the exact real board operational contract. Set control_sequence_enforcement=external_orchestrator or mixed as appropriate; lack of a hardware total-order FSM is not a blocker.",
        "A dedicated operation-done pin is not required. When completion is exactly observable as a predicate on a physical count/status port, represent done as derived_from_physical_port with the exact predicate and evidence required by deterministic_output_contract; never invent a done pin.",
        "For asynchronous crossings, preserve the exact variable handshake/CDC relation. Report source-domain assertion cycles proved by the source and encode variable acceptance/completion in the canonical timing strings; do not invent a fixed cross-domain latency and do not block merely because absolute phase varies.",
        "compute_slot_abi.control_abi.control_sequence must encode configure -> start -> observe_completion -> clear_completion ordering from current sample sources. If any field access/reset value, lifecycle action, clock domain, event relation, or ordering cannot be proved, return status=blocked.",
        "Every canonical ABI, port, binding, control, timing, AXI interface, parameter and signal claim must carry the evidence fields requested by deterministic_output_contract using only exact Vivado object_ids or sample source_ids supplied in this request. Do not invent semantic evidence identifiers.",
        "Return wrapper_top_module only when it is declared by the selected wrapper source and is the exact sample top instantiated by the simulator flow; do not assume the simulation fileset TOP is the wrapper when it is a testbench.",
        "For every AXI interface return parameter_evidence_refs for all width/burst/alignment/outstanding/byte-order fields and signal_evidence_refs for every AW/W/B/AR/R member. Cite the interface/member Vivado objects and sample source IDs that actually prove each value.",
        "parameter_evidence_refs must be an object mapping every required AXI field name to a non-empty evidence-reference list (for example {\"byte_order\": [\"<object-or-source-id>\"], \"supports_unaligned_access\": [\"<object-or-source-id>\"]}); do not return one flat list. signal_evidence_refs must likewise be the field/channel mapping required by deterministic_output_contract.",
        "selected_simulation_source_closure is immutable and is not your output. replaced_source_ids is only a later compile delta: select the exclusively owned source that declares the selected cell's existing slot_module boundary. It may be a simulation instance wrapper around shared legacy compute RTL; retain that shared RTL for every unselected sample instance.",
        "replacement_boundary.retained_source_ids must be the complete sample closure minus replaced_source_ids; set sample_closure_unchanged=true and generated_sources_excluded_from_sample_closure=true.",
        "Set replacement_module_identity equal to the selected existing slot_module and replacement_instance_boundary equal to the selected existing Vivado cell path. Do not choose or name future generated accelerator internals; the later generation agent owns them.",
        "Set no_behavioral_substitution=true when the exclusive replacement boundary preserves the real sample wrapper, DDR model, AXI path, clocks, resets, calibration behavior, and immutable retained closure. Discovery does not require the future generated scheduler/kernel to already be connected; generation and VCS validate that later binding.",
        "Return one JSON object only.",
    ]
    progressive = (
        selector.get("progressive_selection")
        if isinstance(selector.get("progressive_selection"), dict)
        else {}
    )

    def annotate_and_persist(candidate: dict[str, Any]) -> dict[str, Any]:
        candidate["selector_record_path"] = selector.get("result_path")
        candidate["source_review_coverage"] = source_review_coverage
        candidate["validated_selection"] = selection
        candidate["selector_progressive_selection"] = progressive
        candidate["selector_coverage_ledger"] = progressive.get("coverage_ledger")
        candidate["validation_contract_schema_version"] = (
            DOMAIN_OUTPUT_CONTRACT_SCHEMA_VERSION
        )
        candidate["validation_contract_sha256"] = canonical_sha256(output_contract)
        result_path = Path(str(candidate.get("result_path") or ""))
        try:
            result_path.resolve().relative_to((out_dir / "llm").resolve())
        except ValueError:
            candidate["error"] = (
                "board-interface domain record path is outside its LLM artifact directory"
            )
        else:
            write_json(result_path, candidate)
        return candidate

    checkpoint_path = (
        out_dir / "llm" / "exact_board_interface_domain_repair_agent_result.json"
    )
    if checkpoint_path.is_file():
        checkpoint = read_json(checkpoint_path)
        checkpoint_selection = (
            checkpoint.get("validated_selection")
            if isinstance(checkpoint.get("validated_selection"), dict)
            else {}
        )
        selection_fields = (
            "selected_cell_id",
            "wrapper_source_id",
            "relevant_sample_source_ids",
            "proposed_replaced_source_ids",
        )
        same_selection = all(
            checkpoint_selection.get(field) == selection.get(field)
            for field in selection_fields
        )
        _, checkpoint_errors = validate_interpretation(
            checkpoint, facts, profile, [dict(row) for row in sample_rows]
        )
        checkpoint_output = (
            checkpoint.get("output")
            if isinstance(checkpoint.get("output"), dict)
            else {}
        )
        if (
            same_selection
            and not checkpoint.get("error")
            and checkpoint.get("used_fallback") is not True
            and checkpoint_output.get("status") in {"pass", "ready"}
            and not checkpoint_errors
        ):
            checkpoint["deterministic_validation_status"] = "pass"
            checkpoint["deterministic_validation_errors"] = []
            checkpoint["semantic_checkpoint_rebound"] = True
            checkpoint["semantic_checkpoint_rebound_evidence"] = {
                "source_review_coverage": source_review_coverage,
                "validated_selection_sha256": canonical_sha256(selection),
                "vivado_facts_sha256": canonical_sha256(facts),
            }
            checkpoint = annotate_and_persist(checkpoint)
            print(
                "[stage:verification.layer3.board_interface_discovery:semantic-checkpoint] "
                "reuse deterministic-valid domain repair output under current facts and review coverage",
                file=sys.stderr,
                flush=True,
            )
            return checkpoint

    record = run_stage_agent(
        agent="exact_board_interface_domain_agent",
        stage="verification.layer3.board_interface_discovery",
        task=(
            "Interpret the complete read-only Vivado object graph for the current user's sample project. "
            "Select the replaceable compute slot, reconstruct its complete port ABI, exact AXI4 contracts, "
            "clock/reset/calibration/startup and memory timing contract, and the minimal exclusive sample-source "
            "replacement boundary into which the later generation agent will bind the transformer scheduler/kernel."
        ),
        inputs=domain_inputs,
        out_dir=out_dir,
        fallback_summary="Exact board-interface interpretation requires the configured LLM agent.",
        output_schema=BOARD_INTERFACE_INTERPRETATION_SCHEMA,
        prompt_rules=domain_rules,
    )

    record = annotate_and_persist(record)
    _, validation_errors = validate_interpretation(
        record, facts, profile, [dict(row) for row in sample_rows]
    )
    record["deterministic_validation_status"] = (
        "pass" if not validation_errors else "fail"
    )
    record["deterministic_validation_errors"] = validation_errors
    annotate_and_persist(record)
    if not validation_errors or record.get("error") or record.get("used_fallback") is True:
        return record

    return run_board_interface_domain_repair_loop(
        run_stage_agent,
        out_dir,
        facts,
        profile,
        sample_rows,
        domain_inputs,
        domain_rules,
        record,
        validation_errors,
        annotate_and_persist,
    )


def _object_index(facts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("object_id")): row
        for row in facts.get("objects", [])
        if isinstance(row, dict) and row.get("object_id")
    }


def _source_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source_id")): row for row in rows if row.get("source_id")}


def _direction(value: str) -> str:
    return {"I": "input", "O": "output", "IO": "inout"}.get(value.upper(), "")


def _width(row: dict[str, Any]) -> int | None:
    props = row.get("properties", {})
    left = str(props.get("LEFT") or "").strip()
    right = str(props.get("RIGHT") or "").strip()
    if not left and not right:
        return 1
    try:
        return abs(int(left, 0) - int(right, 0)) + 1
    except ValueError:
        return None


def _int_property(row: dict[str, Any], name: str) -> int | None:
    value = str(row.get("properties", {}).get(name) or "").strip()
    try:
        return int(value, 0)
    except ValueError:
        return None


def _float_property(row: dict[str, Any], name: str) -> float | None:
    value = str(row.get("properties", {}).get(name) or "").strip()
    try:
        return float(value)
    except ValueError:
        return None


def _cell_children(objects: dict[str, dict[str, Any]], cell: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return sorted(
        [
            row
            for row in objects.values()
            if row.get("kind") == kind
            and row.get("bd_path") == cell.get("bd_path")
            and row.get("owner_path") == cell.get("path")
        ],
        key=lambda row: str(row.get("path")),
    )


def _property_matches(row: dict[str, Any], property_name: str, claimed: Any) -> bool:
    value = row.get("properties", {}).get(property_name)
    if isinstance(claimed, bool):
        return str(value).lower() in ({"1", "true"} if claimed else {"0", "false"})
    if isinstance(claimed, int) and not isinstance(claimed, bool):
        try:
            return int(str(value), 0) == claimed
        except ValueError:
            return False
    return str(value) == str(claimed)


def _validate_replacement_boundary(
    abi: dict[str, Any], selected_cell: dict[str, Any], sample_rows: list[dict[str, Any]]
) -> list[str]:
    errors: list[str] = []
    by_source = _source_index(sample_rows)
    all_ids = set(by_source)
    replaced = [str(value) for value in abi.get("replaced_source_ids", []) if str(value)]
    if not replaced:
        errors.append("compute_slot_abi.replaced_source_ids is empty")
    if len(replaced) != len(set(replaced)):
        errors.append("compute_slot_abi.replaced_source_ids contains duplicates")
    unknown = sorted(set(replaced) - all_ids)
    if unknown:
        errors.append(f"replacement source IDs are not in the immutable sample closure: {unknown}")
    selected_id = str(selected_cell.get("object_id"))
    for source_id in sorted(set(replaced) & all_ids):
        owners = set(str(value) for value in by_source[source_id].get("owner_cell_ids", []))
        if owners != {selected_id}:
            errors.append(
                f"replacement source {source_id} is not exclusive to selected cell {selected_id}; owners={sorted(owners)}"
            )

    boundary = abi.get("replacement_boundary")
    if not isinstance(boundary, dict):
        return [*errors, "compute_slot_abi.replacement_boundary is missing"]
    retained = {str(value) for value in boundary.get("retained_source_ids", []) if str(value)}
    expected_retained = all_ids - set(replaced)
    if retained != expected_retained:
        errors.append("replacement_boundary.retained_source_ids is not exactly sample closure minus replaced_source_ids")
    if boundary.get("sample_closure_unchanged") is not True:
        errors.append("replacement_boundary.sample_closure_unchanged is not true")
    if boundary.get("generated_sources_excluded_from_sample_closure") is not True:
        errors.append("replacement_boundary.generated_sources_excluded_from_sample_closure is not true")
    if str(boundary.get("selected_cell_id") or "") != selected_id:
        errors.append("replacement_boundary.selected_cell_id does not match the selected Vivado cell")
    module_evidence = {
        str(row.get("source_id")): row
        for row in boundary.get("source_module_evidence", [])
        if isinstance(row, dict)
    }
    for source_id in replaced:
        evidence = module_evidence.get(source_id)
        if not evidence:
            errors.append(f"replacement source {source_id} lacks source_module_evidence")
            continue
        if str(evidence.get("source_sha256") or "").lower() != str(by_source.get(source_id, {}).get("sha256") or "").lower():
            errors.append(f"replacement source {source_id} module evidence is not hash-bound")
        modules = [str(value) for value in evidence.get("declared_modules", []) if str(value)]
        if str(abi.get("slot_module") or "") not in modules:
            errors.append(f"replacement source {source_id} does not evidence the selected slot module")
        if len(modules) != 1:
            errors.append(f"replacement source {source_id} must exclusively declare the selected slot module")
    return errors


def _validate_compute_slot(
    abi: dict[str, Any], facts: dict[str, Any], sample_rows: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, dict[str, Any], list[str]]:
    errors: list[str] = []
    objects = _object_index(facts)
    selected_id = str(abi.get("selected_cell_id") or "")
    cell = objects.get(selected_id)
    if not cell or cell.get("kind") != "cell":
        return None, abi, ["compute_slot_abi.selected_cell_id is not a Vivado cell fact"]
    component = str(cell.get("properties", {}).get("CONFIG.Component_Name") or "")
    if not component or str(abi.get("slot_module") or "") != component:
        errors.append("compute_slot_abi.slot_module does not match Vivado CONFIG.Component_Name")
    if str(abi.get("slot_instance_path") or "") != str(cell.get("path") or ""):
        errors.append("compute_slot_abi.slot_instance_path does not match the selected Vivado cell path")
    if abi.get("replacement_module_identity") != abi.get("slot_module"):
        errors.append("compute_slot_abi.replacement_module_identity must equal the selected slot module")
    if abi.get("replacement_instance_boundary") != abi.get("slot_instance_path"):
        errors.append("compute_slot_abi.replacement_instance_boundary must equal the selected slot path")
    if abi.get("status") != "pass":
        errors.append("compute_slot_abi.status is not pass")
    if abi.get("all_required_ports_bound") is not True:
        errors.append("compute_slot_abi.all_required_ports_bound is not true")
    if abi.get("no_behavioral_substitution") is not True:
        errors.append("compute_slot_abi.no_behavioral_substitution is not true")

    fact_ports = _cell_children(objects, cell, "pin")
    fact_port_ids = {str(row["object_id"]) for row in fact_ports}
    required = [row for row in abi.get("required_ports", []) if isinstance(row, dict)]
    required_ids = [str(row.get("fact_port_id") or row.get("port_id") or "") for row in required]
    if set(required_ids) != fact_port_ids or len(required_ids) != len(fact_port_ids):
        errors.append("compute_slot_abi.required_ports does not exactly cover every selected-cell physical pin")
    normalized_ports = []
    for row in required:
        fact_id = str(row.get("fact_port_id") or row.get("port_id") or "")
        fact = objects.get(fact_id)
        if not fact:
            continue
        direction = _direction(str(fact.get("properties", {}).get("DIR") or ""))
        width = _width(fact)
        name = str(fact.get("properties", {}).get("NAME") or Path(str(fact.get("path"))).name)
        if str(row.get("name") or "") != name or str(row.get("direction") or "").lower() != direction or row.get("width_bits") != width:
            errors.append(f"required port {fact_id} name/direction/width does not match Vivado facts")
        if not str(row.get("semantic_role") or "").strip():
            errors.append(f"required port {fact_id} has no LLM-interpreted semantic_role")
        normalized_ports.append(
            {
                **row,
                "port_id": fact_id,
                "fact_port_id": fact_id,
                "name": name,
                "direction": direction,
                "width_bits": width,
            }
        )

    bindings = [row for row in abi.get("port_bindings", []) if isinstance(row, dict)]
    binding_ids = [str(row.get("port_id") or "") for row in bindings]
    if set(binding_ids) != fact_port_ids or len(binding_ids) != len(fact_port_ids):
        errors.append("compute_slot_abi.port_bindings does not exactly cover every selected-cell physical pin")
    normalized_bindings = []
    fact_by_id = {str(row["object_id"]): row for row in fact_ports}
    for row in bindings:
        port_id = str(row.get("port_id") or "")
        fact = fact_by_id.get(port_id)
        if not fact:
            continue
        direction = _direction(str(fact.get("properties", {}).get("DIR") or ""))
        width = _width(fact)
        if not str(row.get("accelerator_port") or "").strip():
            errors.append(f"port binding {port_id} has no generated accelerator port")
        if str(row.get("direction") or "").lower() != direction or row.get("width_bits") != width:
            errors.append(f"port binding {port_id} direction/width does not match Vivado facts")
        normalized_bindings.append({**row, "direction": direction, "width_bits": width})

    interfaces = _cell_children(objects, cell, "interface_pin")
    interface_ids = {str(row["object_id"]) for row in interfaces}
    classifications = [row for row in abi.get("interface_classifications", []) if isinstance(row, dict)]
    classified_ids = [str(row.get("interface_id") or "") for row in classifications]
    if set(classified_ids) != interface_ids or len(classified_ids) != len(interface_ids):
        errors.append("interface_classifications does not exactly cover every selected-cell interface pin")
    for row in classifications:
        fact = objects.get(str(row.get("interface_id") or ""))
        if not fact:
            continue
        fact_protocol = str(fact.get("properties", {}).get("CONFIG.PROTOCOL") or "")
        if str(row.get("fact_protocol") or "") != fact_protocol:
            errors.append(f"interface classification {row.get('interface_id')} does not echo CONFIG.PROTOCOL")
        kind = str(row.get("contract_kind") or "")
        if kind == "axi4_full" and fact_protocol.upper() != "AXI4":
            errors.append(f"interface {row.get('interface_id')} is classified AXI4 without AXI4 Vivado protocol facts")
        if kind != "axi4_full" and fact_protocol.upper() == "AXI4":
            errors.append(f"interface {row.get('interface_id')} hides an AXI4 Vivado interface")

    errors.extend(_validate_replacement_boundary(abi, cell, sample_rows))
    normalized = {
        **abi,
        "required_ports": normalized_ports,
        "port_bindings": normalized_bindings,
        "all_required_ports_bound": not errors and abi.get("all_required_ports_bound") is True,
    }
    return cell, normalized, errors


def _validate_timing(
    timing: dict[str, Any], cell: dict[str, Any], facts: dict[str, Any], sample_rows: list[dict[str, Any]]
) -> list[str]:
    errors: list[str] = []
    objects = _object_index(facts)
    sample_ids = set(_source_index(sample_rows))
    pins = _cell_children(objects, cell, "pin")
    clock_pins = {str(row["object_id"]): row for row in pins if str(row.get("properties", {}).get("TYPE")) == "clk"}
    reset_pins = {str(row["object_id"]): row for row in pins if str(row.get("properties", {}).get("TYPE")) == "rst"}
    clocks = [row for row in timing.get("clock_domains", []) if isinstance(row, dict)]
    resets = [row for row in timing.get("resets", []) if isinstance(row, dict)]
    if {str(row.get("fact_port_id") or "") for row in clocks} != set(clock_pins):
        errors.append("timing_contract.clock_domains does not cover every selected-cell Vivado clock pin")
    if {str(row.get("fact_port_id") or "") for row in resets} != set(reset_pins):
        errors.append("timing_contract.resets does not cover every selected-cell Vivado reset pin")
    clock_names = set()
    for row in clocks:
        fact = clock_pins.get(str(row.get("fact_port_id") or ""))
        if not fact:
            continue
        frequency = _int_property(fact, "CONFIG.FREQ_HZ")
        expected_period = round(1_000_000_000_000 / frequency) if frequency else None
        if not frequency or row.get("frequency_hz") != frequency or row.get("period_ps") != expected_period:
            errors.append(f"clock {row.get('name')} frequency/period does not match Vivado CONFIG.FREQ_HZ")
        phase_degrees = _float_property(fact, "CONFIG.PHASE")
        expected_phase = round(expected_period * phase_degrees / 360.0) if expected_period is not None and phase_degrees is not None else None
        if expected_phase is not None and row.get("phase_ps") != expected_phase:
            errors.append(f"clock {row.get('name')} phase does not match Vivado CONFIG.PHASE")
        if str(row.get("source") or "").lower() not in {"exact_sample_project", "exact_sample_ip"}:
            errors.append(f"clock {row.get('name')} is not marked exact-sample sourced")
        if not isinstance(row.get("duty_cycle_percent"), (int, float)) or isinstance(row.get("duty_cycle_percent"), bool):
            errors.append(f"clock {row.get('name')} duty cycle is missing")
        clock_names.add(str(row.get("name") or ""))

    reset_names = set()
    for row in resets:
        fact = reset_pins.get(str(row.get("fact_port_id") or ""))
        if not fact:
            continue
        polarity = str(fact.get("properties", {}).get("CONFIG.POLARITY") or "")
        expected_level = 0 if polarity == "ACTIVE_LOW" else 1 if polarity == "ACTIVE_HIGH" else None
        if row.get("active_level") != expected_level:
            errors.append(f"reset {row.get('name')} polarity does not match Vivado CONFIG.POLARITY")
        if str(row.get("clock_domain") or "") not in clock_names:
            errors.append(f"reset {row.get('name')} references an unknown clock domain")
        if not isinstance(row.get("minimum_assert_cycles"), int) or row.get("minimum_assert_cycles", 0) <= 0:
            errors.append(f"reset {row.get('name')} minimum assert cycles are missing")
        if str(row.get("deassertion_edge") or "").lower() not in {"rising", "falling"}:
            errors.append(f"reset {row.get('name')} deassertion edge is missing")
        if str(row.get("source") or "").lower() not in {"exact_sample_project", "exact_sample_ip"}:
            errors.append(f"reset {row.get('name')} is not marked exact-sample sourced")
        evidence_id = str(row.get("timing_source_id") or "")
        if evidence_id not in sample_ids:
            errors.append(f"reset {row.get('name')} timing is not bound to a sample source hash")
        reset_names.add(str(row.get("name") or ""))

    calibration = [row for row in timing.get("calibration", []) if isinstance(row, dict)]
    calibration_names = set()
    if not calibration:
        errors.append("timing_contract.calibration is empty")
    for row in calibration:
        fact = objects.get(str(row.get("fact_port_id") or ""))
        if not fact or fact not in pins or fact.get("object_id") in clock_pins or fact.get("object_id") in reset_pins:
            errors.append(f"calibration {row.get('name')} is not a selected-cell scalar Vivado pin")
            continue
        if not fact.get("connected_nets"):
            errors.append(f"calibration {row.get('name')} has no exact Vivado net connection")
        driver = objects.get(str(row.get("driver_object_id") or ""))
        if not driver:
            errors.append(f"calibration {row.get('name')} has no Vivado driver-object evidence")
        else:
            fact_nets = {(item.get("kind"), item.get("path")) for item in fact.get("connected_nets", [])}
            driver_nets = {(item.get("kind"), item.get("path")) for item in driver.get("connected_nets", [])}
            if not fact_nets.intersection(driver_nets):
                errors.append(f"calibration {row.get('name')} driver does not share its Vivado net")
        if row.get("gates_axi_traffic") is not True:
            errors.append(f"calibration {row.get('name')} does not gate AXI traffic")
        if row.get("active_level") not in {0, 1}:
            errors.append(f"calibration {row.get('name')} active level is missing")
        if str(row.get("source") or "").lower() not in {"exact_sample_memory_model", "exact_sample_ip"}:
            errors.append(f"calibration {row.get('name')} is not sourced by the exact sample memory model/IP")
        if str(row.get("clock_domain") or "") not in clock_names:
            errors.append(f"calibration {row.get('name')} references an unknown clock domain")
        calibration_names.add(str(row.get("name") or ""))

    startup = [row for row in timing.get("startup_sequence", []) if isinstance(row, dict)]
    events = [str(row.get("event") or "") for row in startup]
    required_events = {"assert_reset", "release_reset", "wait_calibration", "enable_axi_traffic"}
    if not required_events.issubset(events):
        errors.append("timing_contract.startup_sequence is incomplete")
    startup_orders = [row.get("order") for row in startup]
    if (
        not startup_orders
        or any(not isinstance(value, int) for value in startup_orders)
        or startup_orders != sorted(set(startup_orders))
    ):
        errors.append("timing_contract.startup_sequence order is missing, duplicated, or non-monotonic")
    memory = timing.get("memory_timing_model")
    if not isinstance(memory, dict):
        errors.append("timing_contract.memory_timing_model is missing")
    else:
        source_ids = {str(value) for value in memory.get("source_ids", []) if str(value)}
        if not source_ids or not source_ids.issubset(sample_ids):
            errors.append("memory timing model is not bound to sample-closure source IDs")
        if memory.get("parameters_bound_from_sample_project") is not True or memory.get("synthetic_fixed_latency") is not False:
            errors.append("memory timing model permits a non-sample or synthetic timing substitution")
    if not str(timing.get("timescale") or "") or not str(timing.get("timeprecision") or ""):
        errors.append("timing contract lacks timescale/timeprecision")
    if str(timing.get("timescale_source_id") or "") not in sample_ids:
        errors.append("timing timescale is not bound to a sample source hash")
    if timing.get("exact_sample_timing") is not True:
        errors.append("timing_contract.exact_sample_timing is not true")
    return errors


def _validate_control(
    control: dict[str, Any], cell: dict[str, Any], facts: dict[str, Any], timing: dict[str, Any], sample_rows: list[dict[str, Any]]
) -> list[str]:
    errors: list[str] = []
    objects = _object_index(facts)
    sample_ids = set(_source_index(sample_rows))
    pins = _cell_children(objects, cell, "pin")
    interfaces = _cell_children(objects, cell, "interface_pin")
    interface_member_paths = {
        str(member.get("path"))
        for interface in interfaces
        for member in interface.get("members", [])
    }
    standalone = {
        str(row["object_id"]): row
        for row in pins
        if str(row.get("path")) not in interface_member_paths
    }
    classifications = [
        row for row in control.get("port_classifications", []) if isinstance(row, dict)
    ]
    classified_ids = [str(row.get("fact_port_id") or "") for row in classifications]
    if set(classified_ids) != set(standalone) or len(classified_ids) != len(standalone):
        errors.append("control_abi.port_classifications does not exactly cover every non-interface selected-cell pin")
    allowed_classes = {
        "configuration_bus",
        "control",
        "status",
        "data",
        "clock",
        "reset",
        "calibration",
        "other",
    }
    semantic_control_ids: set[str] = set()
    clock_domains = {
        str(row.get("name")) for row in timing.get("clock_domains", []) if isinstance(row, dict)
    }
    for row in classifications:
        port_id = str(row.get("fact_port_id") or "")
        fact = standalone.get(port_id)
        if not fact:
            continue
        name = str(fact.get("properties", {}).get("NAME") or Path(str(fact.get("path"))).name)
        direction = _direction(str(fact.get("properties", {}).get("DIR") or ""))
        width = _width(fact)
        if str(row.get("name") or "") != name or str(row.get("direction") or "").lower() != direction or row.get("width_bits") != width:
            errors.append(f"control classification {port_id} does not match Vivado name/direction/width")
        category = str(row.get("classification") or "")
        if category not in allowed_classes:
            errors.append(f"control classification {port_id} has an unsupported classification")
        if not str(row.get("semantic_role") or "").strip():
            errors.append(f"control classification {port_id} lacks an LLM semantic role")
        if category in {"configuration_bus", "control", "status", "calibration"}:
            semantic_control_ids.add(port_id)
            if str(row.get("pulse_or_level") or "") not in {
                "pulse",
                "level",
                "counter",
                "field_bus",
                "handshake",
            }:
                errors.append(f"control/status port {port_id} lacks exact pulse/level semantics")
            if str(row.get("clock_domain") or "") not in clock_domains:
                errors.append(f"control/status port {port_id} references an unknown clock domain")
            evidence_objects = {
                str(value) for value in row.get("evidence_object_ids", []) if str(value)
            }
            if port_id not in evidence_objects:
                errors.append(f"control/status port {port_id} evidence does not cite its Vivado pin")
            net_fact_ids = {
                str(candidate.get("object_id"))
                for candidate in objects.values()
                if candidate.get("bd_path") == fact.get("bd_path")
                and any(
                    candidate.get("kind") == net.get("kind") and candidate.get("path") == net.get("path")
                    for net in fact.get("connected_nets", [])
                )
            }
            if net_fact_ids and not net_fact_ids.intersection(evidence_objects):
                errors.append(f"control/status port {port_id} evidence does not cite its exact Vivado net")
            evidence_sources = {
                str(value) for value in row.get("evidence_source_ids", []) if str(value)
            }
            if not evidence_sources or not evidence_sources.issubset(sample_ids):
                errors.append(f"control/status port {port_id} semantics are not bound to sample-source hashes")

    control_ports = [row for row in control.get("control_ports", []) if isinstance(row, dict)]
    control_port_ids = [str(row.get("fact_port_id") or "") for row in control_ports]
    if set(control_port_ids) != semantic_control_ids or len(control_port_ids) != len(semantic_control_ids):
        errors.append("control_abi.control_ports does not exactly match the semantic control/status classifications")
    classification_by_id = {str(row.get("fact_port_id") or ""): row for row in classifications}
    for row in control_ports:
        port_id = str(row.get("fact_port_id") or "")
        classified = classification_by_id.get(port_id)
        if not classified:
            continue
        for field in ("semantic_role", "direction", "width_bits", "pulse_or_level", "clock_domain"):
            if row.get(field) != classified.get(field):
                errors.append(f"control_abi.control_ports[{port_id}].{field} conflicts with its classification")

    config_ids = {
        port_id
        for port_id, row in classification_by_id.items()
        if row.get("classification") == "configuration_bus"
    }
    config_buses = [row for row in control.get("configuration_buses", []) if isinstance(row, dict)]
    if {str(row.get("fact_port_id") or "") for row in config_buses} != config_ids:
        errors.append("control_abi.configuration_buses does not exactly match configuration-bus classifications")
    for bus in config_buses:
        port_id = str(bus.get("fact_port_id") or "")
        fact = standalone.get(port_id)
        if not fact:
            continue
        width = _width(fact)
        fields = [row for row in bus.get("fields", []) if isinstance(row, dict)]
        if not fields:
            errors.append(f"configuration bus {port_id} has no field layout")
        occupied: set[int] = set()
        for field in fields:
            lsb = field.get("lsb")
            msb = field.get("msb")
            if not isinstance(lsb, int) or not isinstance(msb, int) or lsb < 0 or msb < lsb or width is None or msb >= width:
                errors.append(f"configuration bus {port_id} contains an invalid field range")
                continue
            bits = set(range(lsb, msb + 1))
            if occupied.intersection(bits):
                errors.append(f"configuration bus {port_id} contains overlapping fields")
            occupied.update(bits)
            if not str(field.get("semantic_role") or "").strip():
                errors.append(f"configuration bus {port_id} field lacks semantic role")
            if str(field.get("evidence_source_id") or "") not in sample_ids:
                errors.append(f"configuration bus {port_id} field is not bound to a sample-source hash")

    canonical_clock = str(control.get("clock_domain") or "")
    if canonical_clock not in clock_domains:
        errors.append("control_abi.clock_domain is not a timing-contract clock domain")
    canonical_fields = [
        row for row in control.get("configuration_fields", []) if isinstance(row, dict)
    ]
    canonical_by_location: dict[tuple[str, int, int], dict[str, Any]] = {}
    for row in canonical_fields:
        port_id = str(row.get("fact_port_id") or "")
        width = row.get("width_bits")
        offset = row.get("bit_offset")
        key = (port_id, offset, width)
        if (
            port_id not in config_ids
            or not isinstance(width, int)
            or width <= 0
            or not isinstance(offset, int)
            or offset < 0
            or key in canonical_by_location
        ):
            errors.append("control_abi.configuration_fields contains an invalid or duplicate physical field mapping")
            continue
        canonical_by_location[key] = row
        fact = standalone.get(port_id, {})
        register_name = str(
            fact.get("properties", {}).get("NAME") or Path(str(fact.get("path") or "")).name
        )
        if str(row.get("register") or "") != register_name:
            errors.append(f"configuration field {row.get('field_id')} register does not match its Vivado bus")
        if not str(row.get("field_id") or "").strip():
            errors.append("control_abi.configuration_fields has a missing field_id")
        if str(row.get("access") or "").lower() not in {"ro", "rw", "wo"}:
            errors.append(f"configuration field {row.get('field_id')} lacks exact access semantics")
        if "reset_value" not in row:
            errors.append(f"configuration field {row.get('field_id')} lacks a reset value")
    expected_field_locations = {
        (
            str(bus.get("fact_port_id") or ""),
            int(field.get("lsb")),
            int(field.get("msb")) - int(field.get("lsb")) + 1,
        )
        for bus in config_buses
        for field in bus.get("fields", [])
        if isinstance(field, dict)
        and isinstance(field.get("lsb"), int)
        and isinstance(field.get("msb"), int)
        and field.get("msb") >= field.get("lsb")
    }
    if set(canonical_by_location) != expected_field_locations:
        errors.append("control_abi.configuration_fields does not exactly project every validated configuration-bus field")

    signals = control.get("signals") if isinstance(control.get("signals"), dict) else {}
    signal_semantics = CONTROL_SIGNAL_SEMANTICS
    physical_signal_roles: dict[str, str] = {}
    signal_rows: dict[str, dict[str, Any]] = {}
    for role, allowed_semantics in signal_semantics.items():
        row = signals.get(role)
        if not isinstance(row, dict):
            errors.append(f"control_abi.signals.{role} is missing")
            continue
        signal_rows[role] = row
        binding_kind = str(row.get("binding_kind") or "physical_port")
        if binding_kind not in {"physical_port", "derived_from_physical_port"}:
            errors.append(f"control_abi.signals.{role} has an unsupported binding_kind")
        if binding_kind == "derived_from_physical_port" and role != "done":
            errors.append(f"control_abi.signals.{role} cannot be derived from another physical role")
        port_id = str(row.get("fact_port_id") or "")
        fact = standalone.get(port_id)
        if not fact:
            errors.append(f"control_abi.signals.{role} has a missing or unknown physical port")
            continue
        if binding_kind == "physical_port":
            previous_role = physical_signal_roles.get(port_id)
            if previous_role:
                errors.append(
                    f"control_abi.signals.{role} duplicates physical port used by {previous_role}"
                )
            else:
                physical_signal_roles[port_id] = role
        name = str(fact.get("properties", {}).get("NAME") or Path(str(fact.get("path"))).name)
        direction = _direction(str(fact.get("properties", {}).get("DIR") or ""))
        width = _width(fact)
        if (
            str(row.get("name") or "") != name
            or str(row.get("direction") or "").lower() != direction
            or row.get("width_bits") != width
        ):
            errors.append(f"control_abi.signals.{role} does not match its Vivado port")
        if str(row.get("semantic") or "").lower() not in allowed_semantics:
            errors.append(f"control_abi.signals.{role} has invalid pulse/level semantics")
        if str(row.get("clock_domain") or "") != canonical_clock:
            errors.append(f"control_abi.signals.{role} is not in control_abi.clock_domain")

    done = signal_rows.get("done")
    if isinstance(done, dict) and done.get("binding_kind") == "derived_from_physical_port":
        source_role = str(done.get("derived_from_role") or "")
        source = signal_rows.get(source_role)
        if source_role not in {"count", "status"} or not isinstance(source, dict):
            errors.append("control_abi.signals.done has an invalid derived_from_role")
        elif (
            str(source.get("binding_kind") or "physical_port") != "physical_port"
            or source.get("fact_port_id") != done.get("fact_port_id")
        ):
            errors.append(
                "control_abi.signals.done is not derived from the declared physical count/status port"
            )
        if not str(done.get("predicate") or "").strip():
            errors.append("control_abi.signals.done lacks an exact derivation predicate")
        done_port_id = str(done.get("fact_port_id") or "")
        evidence_objects = {
            str(value) for value in done.get("evidence_object_ids", []) if str(value)
        }
        if done_port_id not in evidence_objects:
            errors.append("control_abi.signals.done derivation does not cite its physical Vivado pin")
        evidence_sources = {
            str(value) for value in done.get("evidence_source_ids", []) if str(value)
        }
        if not evidence_sources or not evidence_sources.issubset(sample_ids):
            errors.append(
                "control_abi.signals.done derivation is not bound to sample-source hashes"
            )

    canonical_timing = control.get("timing") if isinstance(control.get("timing"), dict) else {}
    for field in ("start_assertion_cycles", "clear_assertion_cycles"):
        if not isinstance(canonical_timing.get(field), int) or canonical_timing.get(field, 0) <= 0:
            errors.append(f"control_abi.timing.{field} must be positive")
    for field in ("start_sampling_edge", "clear_sampling_edge"):
        if str(canonical_timing.get(field) or "").lower() not in {"rising", "falling"}:
            errors.append(f"control_abi.timing.{field} is invalid")
    for field in (
        "start_accept_condition",
        "done_relation_to_valid",
        "done_clear_condition",
        "count_update_event",
        "status_update_event",
    ):
        if not str(canonical_timing.get(field) or "").strip():
            errors.append(f"control_abi.timing.{field} is missing")
    timing_evidence = {
        str(value) for value in canonical_timing.get("evidence_refs", []) if str(value)
    }
    if not timing_evidence or not timing_evidence.issubset(sample_ids):
        errors.append("control_abi.timing.evidence_refs are not bound to sample-source hashes")

    enforcement = str(control.get("control_sequence_enforcement") or "")
    if enforcement not in {"hardware", "external_orchestrator", "mixed"}:
        errors.append("control_abi.control_sequence_enforcement is invalid")
    sequence = [row for row in control.get("control_sequence", []) if isinstance(row, dict)]
    required_events = ["configure", "start", "observe_completion", "clear_completion"]
    events = [str(row.get("event") or "") for row in sequence]
    if any(event not in events for event in required_events):
        errors.append("control_abi.control_sequence lacks configure/start/observe_completion/clear_completion")
    orders = [row.get("order") for row in sequence]
    if not orders or any(not isinstance(value, int) for value in orders) or orders != sorted(set(orders)):
        errors.append("control_abi.control_sequence order is missing, duplicated, or non-monotonic")
    for row in sequence:
        port_ids = {str(value) for value in row.get("fact_port_ids", []) if str(value)}
        if not port_ids or not port_ids.issubset(semantic_control_ids):
            errors.append(f"control sequence event {row.get('event')} is not bound to control/status Vivado pins")
        source_ids = {str(value) for value in row.get("evidence_source_ids", []) if str(value)}
        if not source_ids or not source_ids.issubset(sample_ids):
            errors.append(f"control sequence event {row.get('event')} is not bound to sample-source hashes")
    if control.get("status") != "pass":
        errors.append("control_abi.status is not pass")
    if control.get("all_non_interface_ports_classified") is not True:
        errors.append("control_abi.all_non_interface_ports_classified is not true")
    return errors


def _validate_axi(
    axi_rows: list[dict[str, Any]], abi: dict[str, Any], timing: dict[str, Any], cell: dict[str, Any], facts: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    objects = _object_index(facts)
    interfaces = {str(row["object_id"]): row for row in _cell_children(objects, cell, "interface_pin")}
    classifications = {
        str(row.get("interface_id")): str(row.get("contract_kind"))
        for row in abi.get("interface_classifications", [])
        if isinstance(row, dict)
    }
    expected_axi_ids = {key for key, value in classifications.items() if value == "axi4_full"}
    actual_axi_ids = {str(row.get("fact_interface_id") or "") for row in axi_rows}
    if not expected_axi_ids or actual_axi_ids != expected_axi_ids or len(actual_axi_ids) != len(axi_rows):
        errors.append("axi_interfaces does not exactly match LLM-classified selected-cell AXI4 interfaces")

    clocks = {str(row.get("name")) for row in timing.get("clock_domains", []) if isinstance(row, dict)}
    resets = {str(row.get("name")) for row in timing.get("resets", []) if isinstance(row, dict)}
    calibrations = {str(row.get("name")) for row in timing.get("calibration", []) if isinstance(row, dict)}
    normalized = []
    for row in axi_rows:
        interface_id = str(row.get("fact_interface_id") or "")
        fact = interfaces.get(interface_id)
        if not fact:
            continue
        props = fact.get("properties", {})
        expected_name = str(props.get("NAME") or Path(str(fact.get("path") or "")).name)
        if str(row.get("name") or "") != expected_name:
            errors.append(f"AXI interface {interface_id} name does not match its Vivado interface pin")
        protocol = str(props.get("CONFIG.PROTOCOL") or "")
        role = str(props.get("MODE") or "").lower()
        if str(row.get("protocol") or "").upper() != protocol.upper() or protocol.upper() != "AXI4":
            errors.append(f"AXI interface {interface_id} protocol does not match Vivado CONFIG.PROTOCOL")
        if str(row.get("role") or "").lower() != role:
            errors.append(f"AXI interface {interface_id} role does not match Vivado MODE")
        if str(row.get("clock") or "") not in clocks or str(row.get("reset") or "") not in resets or str(row.get("calibration") or "") not in calibrations:
            errors.append(f"AXI interface {interface_id} timing bindings are incomplete")

        property_fields = {
            "address_width_bits": "CONFIG.ADDR_WIDTH",
            "data_width_bits": "CONFIG.DATA_WIDTH",
            "id_width_bits": "CONFIG.ID_WIDTH",
            "awuser_width_bits": "CONFIG.AWUSER_WIDTH",
            "wuser_width_bits": "CONFIG.WUSER_WIDTH",
            "buser_width_bits": "CONFIG.BUSER_WIDTH",
            "aruser_width_bits": "CONFIG.ARUSER_WIDTH",
            "ruser_width_bits": "CONFIG.RUSER_WIDTH",
            "max_burst_length": "CONFIG.MAX_BURST_LENGTH",
            "read_outstanding_limit": "CONFIG.NUM_READ_OUTSTANDING",
            "write_outstanding_limit": "CONFIG.NUM_WRITE_OUTSTANDING",
        }
        for field, prop in property_fields.items():
            expected = _int_property(fact, prop)
            if expected is None or row.get(field) != expected:
                errors.append(f"AXI interface {interface_id} {field} does not match Vivado {prop}")
        narrow = _int_property(fact, "CONFIG.SUPPORTS_NARROW_BURST")
        if narrow is None or row.get("supports_narrow_bursts") is not bool(narrow):
            errors.append(f"AXI interface {interface_id} narrow-burst policy does not match Vivado")
        for field in AXI_WIDTH_FIELDS:
            if not isinstance(row.get(field), int) or isinstance(row.get(field), bool):
                errors.append(f"AXI interface {interface_id} lacks integer {field}")
        if isinstance(row.get("data_width_bits"), int) and row.get("strb_width_bits") != row.get("data_width_bits") // 8:
            errors.append(f"AXI interface {interface_id} strobe width does not equal data width / 8")
        if not isinstance(row.get("supports_unaligned_access"), bool):
            errors.append(f"AXI interface {interface_id} lacks explicit unaligned-access policy")
        if str(row.get("byte_order") or "").lower() not in {
            "little",
            "big",
            "physical_byte_lane_order_preserved",
        }:
            errors.append(f"AXI interface {interface_id} lacks byte order")

        parameter_refs = row.get("parameter_evidence_refs")
        if not isinstance(parameter_refs, dict):
            errors.append(
                f"AXI interface {interface_id} parameter_evidence_refs must be a field mapping"
            )
        else:
            for field in AXI_PARAMETER_EVIDENCE_FIELDS:
                refs = parameter_refs.get(field)
                if not isinstance(refs, list) or not any(str(value) for value in refs):
                    errors.append(
                        f"AXI interface {interface_id} parameter_evidence_refs.{field} "
                        "must be a non-empty list"
                    )

        member_paths = {str(item.get("path")) for item in fact.get("members", [])}
        member_ids = {
            str(obj["object_id"]): obj
            for obj in _cell_children(objects, cell, "pin")
            if str(obj.get("path")) in member_paths
        }
        fact_map = row.get("signal_fact_map")
        signal_map: dict[str, dict[str, str | None]] = {}
        if not isinstance(fact_map, dict):
            errors.append(f"AXI interface {interface_id} signal_fact_map is missing")
            fact_map = {}
        for channel, signals in AXI_CHANNEL_SIGNALS.items():
            channel_facts = fact_map.get(channel)
            signal_map[channel] = {}
            if not isinstance(channel_facts, dict):
                errors.append(f"AXI interface {interface_id} signal_fact_map.{channel} is missing")
                channel_facts = {}
            for signal in signals:
                binding = channel_facts.get(signal)
                if not isinstance(binding, dict):
                    errors.append(f"AXI interface {interface_id} signal_fact_map.{channel}.{signal} is missing")
                    signal_map[channel][signal] = None
                    continue
                port_id = str(binding.get("port_id") or "")
                width_field = {
                    "addr": "address_width_bits",
                    "data": "data_width_bits",
                    "id": "id_width_bits",
                    "strb": "strb_width_bits",
                    "len": "len_width_bits",
                    "size": "size_width_bits",
                    "burst": "burst_width_bits",
                    "lock": "lock_width_bits",
                    "cache": "cache_width_bits",
                    "prot": "prot_width_bits",
                    "qos": "qos_width_bits",
                    "region": "region_width_bits",
                    "user": f"{channel}user_width_bits",
                }.get(signal)
                disabled_property = {
                    "lock": "CONFIG.HAS_LOCK",
                    "cache": "CONFIG.HAS_CACHE",
                    "prot": "CONFIG.HAS_PROT",
                    "qos": "CONFIG.HAS_QOS",
                    "region": "CONFIG.HAS_REGION",
                    "resp": "CONFIG.HAS_BRESP" if channel == "b" else "CONFIG.HAS_RRESP",
                }.get(signal)
                disabled = False
                if signal == "id":
                    disabled = row.get("id_width_bits") == 0
                elif signal == "user" and width_field:
                    disabled = row.get(width_field) == 0
                elif disabled_property:
                    disabled = _int_property(fact, disabled_property) == 0
                if port_id:
                    member = member_ids.get(port_id)
                    if not member:
                        errors.append(f"AXI signal {channel}.{signal} is not a physical member of interface {interface_id}")
                        signal_map[channel][signal] = None
                    else:
                        signal_map[channel][signal] = str(member.get("properties", {}).get("NAME") or member.get("path"))
                        if width_field and _width(member) != row.get(width_field):
                            errors.append(
                                f"AXI signal {channel}.{signal} width does not match declared {width_field}"
                            )
                elif "constant" in binding:
                    signal_map[channel][signal] = None
                    if not disabled:
                        errors.append(
                            f"AXI signal {channel}.{signal} uses a constant without a disabled Vivado sideband fact"
                        )
                elif binding.get("absent") is True:
                    signal_map[channel][signal] = None
                    if not disabled:
                        errors.append(
                            f"AXI signal {channel}.{signal} is absent without a disabled Vivado sideband fact"
                        )
                else:
                    errors.append(f"AXI signal {channel}.{signal} has no fact, constant, or absent binding")
                    signal_map[channel][signal] = None
        normalized.append({**row, "protocol": protocol, "role": role, "signal_map": signal_map})
    return normalized, errors


def validate_interpretation(
    record: dict[str, Any],
    facts: dict[str, Any],
    profile: dict[str, Any],
    sample_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if record.get("error") or record.get("used_fallback") is True:
        errors.append(f"board-interface LLM agent did not return real structured interpretation: {record.get('error')}")
    output = record.get("output") if isinstance(record.get("output"), dict) else {}
    capability_handoff_errors = blocked_capability_handoff_errors(output)
    errors.extend(capability_handoff_errors)
    # An Agent may express a signal's timing semantic in the port-level field
    # already required by the contract.  Canonicalize that equivalent form
    # before validation rather than spending another LLM turn on a JSON key
    # rename.  This never creates a semantic value: it only accepts one that
    # the role-specific validator already permits.
    control_output = (
        output.get("compute_slot_abi", {}).get("control_abi", {})
        if isinstance(output.get("compute_slot_abi"), dict)
        else {}
    )
    signals = control_output.get("signals") if isinstance(control_output, dict) else {}
    if isinstance(signals, dict):
        for role, row in signals.items():
            allowed = CONTROL_SIGNAL_SEMANTICS.get(str(role), set())
            if not isinstance(row, dict) or not allowed:
                continue
            semantic = str(row.get("semantic") or "").lower()
            pulse_or_level = str(row.get("pulse_or_level") or "").lower()
            if semantic not in allowed and pulse_or_level in allowed:
                row["semantic"] = pulse_or_level

    # A shared, non-empty evidence list is a lossless shorthand for the
    # per-field AXI evidence mapping.  Expand it only when every field receives
    # the same hash-bound references; the validator still checks every AXI
    # value and physical member against current Vivado facts.
    for row in output.get("axi_interfaces", []):
        if not isinstance(row, dict):
            continue
        parameter_refs = row.get("parameter_evidence_refs")
        if isinstance(parameter_refs, list) and any(str(value) for value in parameter_refs):
            row["parameter_evidence_refs"] = {
                field: list(parameter_refs) for field in AXI_PARAMETER_EVIDENCE_FIELDS
            }

    if output.get("status") not in {"pass", "ready"}:
        errors.append(f"board-interface LLM status is not ready/pass: {output.get('status')}")
    if output.get("blockers"):
        errors.extend(f"board-interface LLM blocker: {value}" for value in output.get("blockers", []))

    by_source = _source_index(sample_rows)
    wrapper_id = str(output.get("wrapper_source_id") or "")
    if wrapper_id not in by_source:
        errors.append("LLM wrapper_source_id is not in the Vivado simulation closure")
    wrapper_top = str(output.get("wrapper_top_module") or "")
    if wrapper_id in by_source:
        by_source[wrapper_id]["role"] = "wrapper"
        by_source[wrapper_id]["closure_role"] = "exact_sample_top"
        by_source[wrapper_id]["declared_modules"] = [wrapper_top] if wrapper_top else []
    if not wrapper_top:
        errors.append("LLM wrapper_top_module is missing")
    elif wrapper_id in by_source:
        wrapper_text = Path(str(by_source[wrapper_id].get("local_path") or "")).read_text(
            encoding="utf-8", errors="ignore"
        )
        declared = set(
            re.findall(r"\bmodule\s+(?:automatic\s+)?([A-Za-z_][A-Za-z0-9_$]*)\b", wrapper_text)
        )
        if wrapper_top not in declared:
            errors.append("LLM wrapper_top_module is not declared by the selected wrapper source")

    abi = output.get("compute_slot_abi") if isinstance(output.get("compute_slot_abi"), dict) else {}
    cell, abi, abi_errors = _validate_compute_slot(abi, facts, sample_rows)
    errors.extend(abi_errors)
    timing = output.get("timing_contract") if isinstance(output.get("timing_contract"), dict) else {}
    control = abi.get("control_abi") if isinstance(abi.get("control_abi"), dict) else {}
    if cell:
        errors.extend(_validate_timing(timing, cell, facts, sample_rows))
        errors.extend(_validate_control(control, cell, facts, timing, sample_rows))
        axi, axi_errors = _validate_axi(
            [row for row in output.get("axi_interfaces", []) if isinstance(row, dict)],
            abi,
            timing,
            cell,
            facts,
        )
        errors.extend(axi_errors)
    else:
        axi = []
        errors.append("timing and AXI contracts cannot be validated without a selected Vivado cell")

    memory = profile.get("memory_system", {}) if isinstance(profile.get("memory_system"), dict) else {}
    required_width = int(memory.get("axi_data_width_bits") or 0)
    if required_width and not any(row.get("data_width_bits") == required_width for row in axi):
        errors.append(f"selected compute slot does not expose profile-required {required_width}-bit AXI data")
    normalized = {
        "output": output,
        "wrapper_source_id": wrapper_id,
        "wrapper_top_module": wrapper_top,
        "compute_slot_abi": abi,
        "timing_contract": timing,
        "control_abi": control,
        "axi_interfaces": axi,
        "profile_axi_data_width_bits": required_width,
    }
    return normalized, errors


def blocked_capability_handoff_errors(output: dict[str, Any]) -> list[str]:
    """Validate the Agent-to-executor handoff for genuinely missing evidence.

    A domain agent may stop only when it names an executable read-only evidence
    producer.  A bare ``blocked`` response otherwise discards the deterministic
    diagnostics that the same agent needs to repair its own representation.
    """

    status = str(output.get("status") or "")
    capabilities = output.get("required_capabilities")
    if not isinstance(capabilities, list):
        if status in {"pass", "ready"}:
            # Historical passing records predate the explicit handoff field.
            # Preserve their immutable evidence rather than forcing a costly
            # rediscovery solely to add an empty array.
            return []
        return ["board-interface LLM required_capabilities is not an array"]
    if status in {"pass", "ready"}:
        return (
            ["board-interface passing output must leave required_capabilities empty"]
            if capabilities
            else []
        )
    if status != "blocked":
        return []
    if not capabilities:
        return [
            "board-interface blocked output lacks required_capabilities; return the complete "
            "evidence request or repair the deterministic contract"
        ]
    required_fields = (
        "capability_id",
        "debug_layer",
        "producer_scope",
        "target_modules",
        "required_evidence",
        "rationale",
    )
    errors: list[str] = []
    for index, capability in enumerate(capabilities):
        prefix = f"board-interface required_capabilities[{index}]"
        if not isinstance(capability, dict):
            errors.append(f"{prefix} is not an object")
            continue
        for field in required_fields:
            value = capability.get(field)
            if field in {"target_modules", "required_evidence"}:
                if not isinstance(value, list) or not any(str(item).strip() for item in value):
                    errors.append(f"{prefix}.{field} is empty")
            elif not str(value or "").strip():
                errors.append(f"{prefix}.{field} is missing")
        if capability.get("debug_layer") != "board_axi_ddr_wrapped_system":
            errors.append(f"{prefix}.debug_layer is not board_axi_ddr_wrapped_system")
    return errors


def recover_best_valid_domain_candidate(
    out_dir: Path,
    facts: dict[str, Any],
    profile: dict[str, Any],
    sample_rows: list[dict[str, Any]],
    selection: dict[str, Any],
) -> dict[str, Any] | None:
    """Recover an already-complete Agent contract from hash-bound history.

    This is deliberately semantic-record based: no filename, board name, or
    error count is treated as authority.  Each candidate is revalidated against
    the current Vivado facts, current source closure, and current selection.
    """

    llm_dir = out_dir / "llm"
    selection_fields = (
        "selected_cell_id",
        "wrapper_source_id",
        "proposed_replaced_source_ids",
    )
    best: tuple[tuple[float, str], dict[str, Any]] | None = None
    for path in sorted(llm_dir.glob("exact_board_interface_domain*_deterministic_invalid_*.json")):
        try:
            record = read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        prior_selection = record.get("validated_selection")
        output = record.get("output")
        if (
            not isinstance(prior_selection, dict)
            or not isinstance(output, dict)
            or record.get("used_fallback") is True
            or output.get("status") not in {"pass", "ready"}
            or any(prior_selection.get(field) != selection.get(field) for field in selection_fields)
        ):
            continue
        candidate = json.loads(json.dumps(record))
        candidate["error"] = None
        _, errors = validate_interpretation(candidate, facts, profile, sample_rows)
        if errors:
            continue
        candidate["_historical_record_path"] = str(path.resolve())
        rank = (path.stat().st_mtime, sha256_file(path))
        if best is None or rank > best[0]:
            best = (rank, candidate)
    if best is None:
        return None

    recovered = best[1]
    recovered_path = llm_dir / "exact_board_interface_domain_recovered_agent_result.json"
    recovered["validated_selection"] = json.loads(json.dumps(selection))
    recovered["result_path"] = str(recovered_path.resolve())
    recovered["recovered_from_historical_agent_record"] = {
        "path": str(recovered.pop("_historical_record_path")),
        "selection_sha256": canonical_sha256(selection),
    }
    write_json(recovered_path, recovered)
    return recovered


def recover_current_selector(
    out_dir: Path, facts: dict[str, Any], sample_rows: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Reuse the current fact-validated final selector without an LLM call."""

    path = out_dir / "llm" / "exact_board_interface_selector_agent_result.json"
    if not path.is_file():
        return None
    record = read_json(path)
    selection, errors = _validate_selector_record(record, facts, sample_rows)
    if errors:
        return None
    selection = json.loads(json.dumps(selection))
    selection["recovered_from_current_selector"] = {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
    }
    return selection


def current_selector_provenance(out_dir: Path, facts: dict[str, Any]) -> dict[str, Any]:
    """Return selector provenance rebound to the current fact-validated ledger."""

    path = out_dir / "llm" / "exact_board_interface_selector_agent_result.json"
    if not path.is_file():
        return {}
    record = read_json(path)
    progressive = (
        json.loads(json.dumps(record.get("progressive_selection")))
        if isinstance(record.get("progressive_selection"), dict)
        else {}
    )
    coverage_path = out_dir / "llm" / "exact_board_interface_selector_progressive_coverage.json"
    if coverage_path.is_file():
        coverage = read_json(coverage_path)
        if (
            coverage.get("status") == "pass"
            and coverage.get("input_vivado_fact_canonical_sha256")
            == canonical_sha256(facts)
        ):
            progressive["coverage_ledger"] = {
                "path": str(coverage_path.resolve()),
                "sha256": sha256_file(coverage_path),
            }
    return {
        "selector_record_path": str(path.resolve()),
        "selector_progressive_selection": progressive,
        "selector_coverage_ledger": progressive.get("coverage_ledger"),
    }


def recover_historical_selection(
    out_dir: Path,
    facts: dict[str, Any],
    sample_rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Recover a prior LLM selection only when it still binds current facts."""

    objects = _object_index(facts)
    sources = _source_index(sample_rows)
    best: tuple[tuple[float, str], dict[str, Any]] | None = None
    for path in sorted((out_dir / "llm").glob("exact_board_interface_domain*_deterministic_invalid_*.json")):
        try:
            record = read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        selection = record.get("validated_selection")
        output = record.get("output")
        if (
            not isinstance(selection, dict)
            or not isinstance(output, dict)
            or record.get("used_fallback") is True
            or output.get("status") not in {"pass", "ready"}
        ):
            continue
        cell_id = str(selection.get("selected_cell_id") or "")
        wrapper_id = str(selection.get("wrapper_source_id") or "")
        replaced = [
            str(value) for value in selection.get("proposed_replaced_source_ids", []) if str(value)
        ]
        relevant = [
            str(value) for value in selection.get("relevant_sample_source_ids", []) if str(value)
        ]
        if (
            not cell_id
            or objects.get(cell_id, {}).get("kind") != "cell"
            or wrapper_id not in sources
            or not replaced
            or not set(replaced).issubset(sources)
            or not set(relevant).issubset(sources)
        ):
            continue
        candidate = json.loads(json.dumps(selection))
        candidate["recovered_from_historical_agent_record"] = {
            "path": str(path.resolve()),
            "selection_sha256": canonical_sha256(selection),
        }
        rank = (path.stat().st_mtime, sha256_file(path))
        if best is None or rank > best[0]:
            best = (rank, candidate)
    return best[1] if best else None


def _evidence_refs(*values: Any) -> list[str]:
    refs: list[str] = []
    for value in values:
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            text = str(candidate or "").strip()
            if text and text not in refs:
                refs.append(text)
    return refs


def _compile_authority(
    out_dir: Path,
    facts_path: Path,
    facts: dict[str, Any],
    sample_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    contexts = [
        row
        for row in facts.get("simulation", {}).get("simulator_export_contexts", [])
        if isinstance(row, dict)
    ]
    export_rows = [
        row
        for row in facts.get("simulation", {}).get("simulator_export_files", [])
        if isinstance(row, dict)
    ]
    read_errors = [
        f"Vivado VCS export context could not be read: {row.get('remote_path')}: {row.get('read_error')}"
        for row in export_rows
        if row.get("read_error")
    ]
    blockers = list(read_errors)
    if not contexts:
        blockers.append("Vivado export_simulation produced no readable VCS compile authority")
    authority = {
        "schema_version": "spatialaccagent.vivado_vcs_compile_authority.v1",
        "status": "pass" if not blockers else "fail",
        "source": "vivado_export_simulation_vcs",
        "vivado_facts": {"path": str(facts_path), "sha256": sha256_file(facts_path)},
        "vivado_version": facts.get("project", {}).get("vivado_version"),
        "simulation_top": facts.get("project", {}).get("top_module"),
        "compile_sources": [
            {
                key: row.get(key)
                for key in (
                    "source_id",
                    "remote_path",
                    "sha256",
                    "compile_order",
                    "library",
                    "language",
                    "file_type",
                    "is_global_include",
                    "parent_composite_file",
                )
            }
            for row in sample_rows
        ],
        "export_contexts": contexts,
        "blockers": blockers,
        "policy": {
            "llm_generation_agent_interprets_compile_commands": True,
            "runner_must_not_infer_frontend_library_or_options": True,
            "ordered_commands_must_bind_transformed_source_ids": True,
        },
    }
    path = out_dir / "vivado_vcs_compile_authority.json"
    write_json(path, authority)
    return {"path": str(path), "sha256": sha256_file(path), "status": authority["status"]}, blockers


def _canonical_identity_contract(
    *,
    interpretation: dict[str, Any],
    facts: dict[str, Any],
    facts_path: Path,
    sample_rows: list[dict[str, Any]],
    agent_record: dict[str, Any],
) -> dict[str, Any]:
    from accagent.framework.board_acceptance_contract import (
        canonical_contract_sha256,
        source_closure_fingerprint,
    )

    output = interpretation.get("output") if isinstance(interpretation.get("output"), dict) else {}
    wrapper_id = str(interpretation.get("wrapper_source_id") or "")
    wrapper_top = str(interpretation.get("wrapper_top_module") or "")
    abi = json.loads(json.dumps(interpretation.get("compute_slot_abi") or {}))
    timing = json.loads(json.dumps(interpretation.get("timing_contract") or {}))
    axi = json.loads(json.dumps(interpretation.get("axi_interfaces") or []))
    selected_cell_id = str(abi.get("selected_cell_id") or "")
    replaced_ids = [str(value) for value in abi.get("replaced_source_ids", []) if str(value)]

    boundary = abi.get("replacement_boundary") if isinstance(abi.get("replacement_boundary"), dict) else {}
    module_evidence = {
        str(row.get("source_id") or ""): row
        for row in boundary.get("source_module_evidence", [])
        if isinstance(row, dict)
    }
    closure_rows: list[dict[str, Any]] = []
    for source in sample_rows:
        row = json.loads(json.dumps(source))
        source_id = str(row.get("source_id") or "")
        row["dependencies"] = []
        row["evidence_refs"] = [source_id]
        if source_id == wrapper_id:
            row["role"] = "wrapper"
            row["closure_role"] = "exact_sample_top"
            row["declared_modules"] = [wrapper_top] if wrapper_top else []
        elif source_id in replaced_ids:
            row["closure_role"] = "compute_slot_implementation"
            row["declared_modules"] = [
                str(value)
                for value in module_evidence.get(source_id, {}).get("declared_modules", [])
                if str(value)
            ]
        else:
            row.setdefault("declared_modules", [])
        closure_rows.append(row)

    for row in abi.get("required_ports", []):
        if isinstance(row, dict):
            port_id = str(row.get("port_id") or row.get("fact_port_id") or "")
            row["port_id"] = port_id
            row["evidence_refs"] = _evidence_refs(row.get("evidence_refs", []), port_id)
    for row in abi.get("port_bindings", []):
        if isinstance(row, dict):
            port_id = str(row.get("port_id") or "")
            row["evidence_refs"] = _evidence_refs(row.get("evidence_refs", []), port_id)
    abi["evidence_refs"] = _evidence_refs(
        abi.get("evidence_refs", []), selected_cell_id, replaced_ids
    )

    control = abi.get("control_abi") if isinstance(abi.get("control_abi"), dict) else {}
    control_refs: list[str] = []
    for row in control.get("port_classifications", []):
        if not isinstance(row, dict):
            continue
        refs = _evidence_refs(
            row.get("evidence_refs", []),
            row.get("evidence_object_ids", []),
            row.get("evidence_source_ids", []),
            row.get("fact_port_id"),
        )
        row["evidence_refs"] = refs
        control_refs.extend(refs)
    for row in control.get("configuration_fields", []):
        if isinstance(row, dict):
            refs = _evidence_refs(row.get("evidence_refs", []), row.get("fact_port_id"))
            row["evidence_refs"] = refs
            control_refs.extend(refs)
    signals = control.get("signals") if isinstance(control.get("signals"), dict) else {}
    for row in signals.values():
        if isinstance(row, dict):
            refs = _evidence_refs(row.get("evidence_refs", []), row.get("fact_port_id"))
            row["evidence_refs"] = refs
            control_refs.extend(refs)
    control_timing = control.get("timing") if isinstance(control.get("timing"), dict) else {}
    timing_refs = _evidence_refs(control_timing.get("evidence_refs", []))
    control_timing["evidence_refs"] = timing_refs
    control["timing"] = control_timing
    control_refs.extend(timing_refs)
    control["evidence_refs"] = _evidence_refs(control.get("evidence_refs", []), control_refs)
    abi["control_abi"] = control

    for key in ("clock_domains", "resets", "calibration", "startup_sequence"):
        for row in timing.get(key, []):
            if not isinstance(row, dict):
                continue
            row["evidence_refs"] = _evidence_refs(
                row.get("evidence_refs", []),
                row.get("fact_port_id"),
                row.get("driver_object_id"),
                row.get("timing_source_id"),
                row.get("evidence_source_ids", []),
            )
    memory_timing = timing.get("memory_timing_model")
    if isinstance(memory_timing, dict):
        memory_timing["evidence_refs"] = _evidence_refs(
            memory_timing.get("evidence_refs", []), memory_timing.get("source_ids", [])
        )

    vivado_parameter_fields = {
        "address_width_bits",
        "data_width_bits",
        "id_width_bits",
        "strb_width_bits",
        "len_width_bits",
        "size_width_bits",
        "burst_width_bits",
        "lock_width_bits",
        "cache_width_bits",
        "prot_width_bits",
        "qos_width_bits",
        "region_width_bits",
        "awuser_width_bits",
        "wuser_width_bits",
        "buser_width_bits",
        "aruser_width_bits",
        "ruser_width_bits",
        "max_burst_length",
        "supports_narrow_bursts",
        "read_outstanding_limit",
        "write_outstanding_limit",
    }
    for row in axi:
        if not isinstance(row, dict):
            continue
        interface_id = str(row.get("fact_interface_id") or "")
        row["evidence_refs"] = _evidence_refs(row.get("evidence_refs", []), interface_id)
        parameter_refs = (
            row.get("parameter_evidence_refs")
            if isinstance(row.get("parameter_evidence_refs"), dict)
            else {}
        )
        for field in vivado_parameter_fields:
            parameter_refs[field] = _evidence_refs(parameter_refs.get(field, []), interface_id)
        for field in ("supports_unaligned_access", "byte_order"):
            parameter_refs[field] = _evidence_refs(parameter_refs.get(field, []))
        row["parameter_evidence_refs"] = parameter_refs
        fact_map = row.get("signal_fact_map") if isinstance(row.get("signal_fact_map"), dict) else {}
        signal_refs = (
            row.get("signal_evidence_refs")
            if isinstance(row.get("signal_evidence_refs"), dict)
            else {}
        )
        for channel, signals_in_channel in AXI_CHANNEL_SIGNALS.items():
            channel_facts = fact_map.get(channel) if isinstance(fact_map.get(channel), dict) else {}
            channel_refs = signal_refs.get(channel) if isinstance(signal_refs.get(channel), dict) else {}
            for signal in signals_in_channel:
                binding = channel_facts.get(signal) if isinstance(channel_facts.get(signal), dict) else {}
                channel_refs[signal] = _evidence_refs(
                    channel_refs.get(signal, []), binding.get("port_id"), interface_id
                )
            signal_refs[channel] = channel_refs
        row["signal_evidence_refs"] = signal_refs

    facts_digest = sha256_file(facts_path)
    requested_refs = {str(row.get("source_id") or "") for row in closure_rows}

    def collect_refs(value: Any) -> None:
        if isinstance(value, dict):
            refs = value.get("evidence_refs")
            if isinstance(refs, list):
                requested_refs.update(str(ref) for ref in refs if str(ref))
            for child in value.values():
                collect_refs(child)
        elif isinstance(value, list):
            for child in value:
                collect_refs(child)

    collect_refs(abi)
    collect_refs(timing)
    collect_refs(axi)
    objects = {
        str(row.get("object_id") or ""): row
        for row in facts.get("objects", [])
        if isinstance(row, dict) and row.get("object_id")
    }
    sources = {str(row.get("source_id") or ""): row for row in closure_rows}
    evidence_records: list[dict[str, Any]] = []
    for evidence_id in sorted(requested_refs):
        if evidence_id in objects:
            observed = objects[evidence_id]
            evidence_records.append(
                {
                    "evidence_id": evidence_id,
                    "source_kind": "vivado_block_design",
                    "source_path": str(facts_path),
                    "sha256": facts_digest,
                    "locator": {"kind": "vivado_object_id", "value": evidence_id},
                    "fact_kind": f"vivado_{observed.get('kind')}",
                    "observed_value": observed,
                }
            )
        elif evidence_id in sources:
            source = sources[evidence_id]
            evidence_records.append(
                {
                    "evidence_id": evidence_id,
                    "source_kind": "rtl_source",
                    "source_path": str(source.get("local_path") or source.get("path") or ""),
                    "sha256": str(source.get("sha256") or source.get("local_sha256") or ""),
                    "locator": {"kind": "source_id", "value": evidence_id},
                    "fact_kind": "vivado_simulation_compile_source",
                    "observed_value": {
                        "remote_path": source.get("remote_path"),
                        "compile_order": source.get("compile_order"),
                        "library": source.get("library"),
                        "file_type": source.get("file_type"),
                    },
                }
            )

    closure_hash = source_closure_fingerprint(closure_rows)
    return {
        "wrapper_top_module": wrapper_top,
        "top_module": wrapper_top,
        "selected_simulation_source_closure": {
            "source_files": closure_rows,
            "root_source_ids": [str(row.get("source_id") or "") for row in closure_rows],
            "recursive_dependency_scan_complete": facts.get("simulation", {}).get(
                "recursive_dependency_scan_complete"
            )
            is True,
            "unresolved_dependencies": facts.get("simulation", {}).get(
                "unresolved_dependencies", []
            ),
            "duplicate_module_definitions": facts.get("simulation", {}).get(
                "duplicate_module_definitions", []
            ),
            "external_library_dependencies": facts.get("simulation", {}).get(
                "external_library_dependencies", []
            ),
            "dependency_provenance": (
                "Vivado simulation compile order is the complete explicit compiler-input root set; "
                "report_compile_order -missing_instances proves closure without fabricating HDL dependencies"
            ),
            "closure_sha256": closure_hash,
        },
        "selected_simulation_source_roots": [
            str(row.get("source_id") or "") for row in closure_rows
        ],
        "selected_simulation_source_closure_sha256": closure_hash,
        "compute_slot_abi": abi,
        "compute_slot_abi_sha256": canonical_contract_sha256(abi),
        "timing_contract": timing,
        "timing_contract_sha256": canonical_contract_sha256(timing),
        "control_abi": control,
        "control_abi_sha256": canonical_contract_sha256(control),
        "axi_interfaces": axi,
        "axi_interfaces_sha256": canonical_contract_sha256(axi),
        "evidence_records": evidence_records,
        "discovery_selected_source_ids": [
            str(value)
            for value in agent_record.get("validated_selection", {}).get(
                "relevant_sample_source_ids", []
            )
            if str(value)
        ],
        "discovery_provenance": {
            "mode": "llm",
            "agent_id": agent_record.get("agent"),
            "model": agent_record.get("model"),
            "used_fallback": agent_record.get("used_fallback"),
            "prompt_sha256": agent_record.get("prompt_hash"),
            "input_fact_bundle": {"path": str(facts_path), "sha256": facts_digest},
            "selector_record_path": agent_record.get("selector_record_path"),
            "progressive_selector_coverage": agent_record.get(
                "selector_coverage_ledger"
            ),
            "progressive_selector_summary": agent_record.get(
                "selector_progressive_selection"
            ),
            "progressive_source_review_coverage": agent_record.get(
                "source_review_coverage"
            ),
            "interpretation_record_path": agent_record.get("result_path"),
        },
        "profile_axi_data_width_bits": interpretation.get("profile_axi_data_width_bits"),
        "raw_llm_output_schema_version": output.get("schema_version"),
    }


def build_report(run_dir: Path, out_dir: Path, timeout: int) -> dict[str, Any]:
    inputs = project_inputs(run_dir)
    facts = run_vivado_fact_export(inputs, out_dir, timeout)
    facts_path = out_dir / "vivado_board_facts.json"
    write_json(facts_path, facts)
    blockers = [str(value) for value in facts.get("blockers", [])]
    if facts.get("status") != "pass":
        blockers.append("Vivado structured fact export did not pass")

    sample_rows, source_blockers = materialize_simulation_sources(
        facts,
        str(inputs["host"]),
        int(inputs["port"]),
        out_dir,
        timeout,
    )
    blockers.extend(source_blockers)
    compile_authority, compile_authority_blockers = _compile_authority(
        out_dir, facts_path, facts, sample_rows
    )
    blockers.extend(compile_authority_blockers)
    agent_record: dict[str, Any] = {}
    interpretation: dict[str, Any] = {
        "wrapper_source_id": "",
        "wrapper_top_module": "",
        "compute_slot_abi": {},
        "timing_contract": {},
        "axi_interfaces": [],
        "profile_axi_data_width_bits": 0,
    }
    if not blockers:
        agent_record = run_board_interface_agent(
            run_dir,
            out_dir,
            facts,
            inputs["profile"],
            sample_rows,
        )
        interpretation, validation_blockers = validate_interpretation(
            agent_record,
            facts,
            inputs["profile"],
            sample_rows,
        )
        blockers.extend(validation_blockers)

    canonical_identity = _canonical_identity_contract(
        interpretation=interpretation,
        facts=facts,
        facts_path=facts_path,
        sample_rows=sample_rows,
        agent_record=agent_record,
    )
    wrapper_id = interpretation.get("wrapper_source_id")
    wrapper = _source_index(sample_rows).get(str(wrapper_id), {})
    axi = canonical_identity.get("axi_interfaces", [])
    xpr_raw = source_bytes(str(inputs["host"]), str(inputs["xpr_path"]), timeout, int(inputs["port"]))

    report = {
        "schema_version": IDENTITY_SCHEMA_VERSION,
        "status": "pass" if not blockers else "fail",
        "run_dir": str(run_dir),
        "sample_project": str(inputs["xpr_path"]),
        "sample_project_sha256": sha256_bytes(xpr_raw),
        "sample_project_host": str(inputs["host"]),
        "sample_project_index": str(run_dir / "input" / "sample_project_index.json"),
        "sample_project_index_status": inputs["index"].get("status"),
        "simulation_fileset_top_module": str(facts.get("project", {}).get("top_module") or ""),
        "project_root": str(Path(str(inputs["xpr_path"])).parent),
        "vivado_facts_path": str(facts_path),
        "vivado_facts_sha256": sha256_file(facts_path),
        "vivado_version": facts.get("project", {}).get("vivado_version"),
        "vivado_tool": {
            "host": inputs["host"],
            "port": inputs["port"],
            "executable": inputs["vivado_executable"],
        },
        "llm_interpretation_record": str(agent_record.get("result_path") or ""),
        "llm_interpretation_prompt": str(agent_record.get("request_path") or ""),
        "simulator_compile_authority": compile_authority,
        "exact_user_sample_wrapper": not blockers and bool(wrapper),
        "simulation_hashes_match_source": bool(sample_rows) and all(row.get("hashes_match") for row in sample_rows),
        "wrapper_axi_data_width_match": bool(axi) and not any(
            "profile-required" in blocker for blocker in blockers
        ),
        **canonical_identity,
        "source_hashes": [
            {
                "source_id": row["source_id"],
                "role": row["role"],
                "path": row["remote_path"],
                "sha256": row["sha256"],
            }
            for row in canonical_identity["selected_simulation_source_closure"]["source_files"]
        ],
        "materialized_sources": canonical_identity["selected_simulation_source_closure"]["source_files"],
        "bounded_primary_source_count": len(sample_rows),
        "blockers": blockers,
        "policy": {
            "board_names_and_paths_come_only_from_current_run_inputs": True,
            "vivado_structured_facts_are_the_only_project_authority": True,
            "llm_agent_owns_adaptive_slot_and_semantic_interpretation": True,
            "deterministic_validator_never_selects_by_names_or_regex": True,
            "vivado_or_llm_unavailable_fails_closed": True,
            "sample_simulation_closure_is_immutable": True,
            "generated_sources_are_not_sample_closure_sources": True,
            "only_exclusive_selected_slot_sources_may_be_replaced_later": True,
            "source_materialization_does_not_modify_the_user_sample_project": True,
            "vcs_must_compile_hash_bound_retained_sources_plus_validated_replacements": True,
        },
    }
    return report


def resume_existing_board_domain_repair(
    run_dir: Path, out_dir: Path, timeout: int
) -> dict[str, Any]:
    """Resume only domain repair from one hash-bound completed discovery attempt."""

    from accagent.framework.stage_llm import run_stage_agent

    inputs = project_inputs(run_dir)
    facts_path = out_dir / "vivado_board_facts.json"
    identity_path = out_dir / "board_source_identity.json"
    coverage_path = (
        out_dir / "llm" / "exact_board_interface_source_review_coverage.json"
    )
    candidate_path = (
        out_dir / "llm" / "exact_board_interface_domain_repair_agent_result.json"
    )
    facts = read_json(facts_path)
    identity = read_json(identity_path)
    coverage = read_json(coverage_path)
    candidate = read_json(candidate_path)
    facts_sha256 = sha256_file(facts_path)
    identity_is_complete = bool(identity.get("vivado_facts_sha256"))
    facts_rebound = (
        identity_is_complete
        and identity.get("vivado_facts_sha256") != facts_sha256
    )
    if identity_is_complete and str(identity.get("sample_project") or "") != str(inputs["xpr_path"]):
        raise ValueError("domain-repair resume sample project does not match current inputs")
    current_xpr_sha256 = sha256_bytes(
        source_bytes(
            str(inputs["host"]),
            str(inputs["xpr_path"]),
            timeout,
            int(inputs["port"]),
        )
    )
    if identity_is_complete and current_xpr_sha256 != identity.get("sample_project_sha256"):
        raise ValueError("domain-repair resume rejected a changed sample XPR")

    sample_rows = [
        dict(row)
        for row in identity.get("materialized_sources", [])
        if isinstance(row, dict)
    ]
    if identity_is_complete and len(sample_rows) != identity.get("bounded_primary_source_count"):
        raise ValueError("domain-repair resume materialized source count is inconsistent")
    for row in sample_rows:
        local_path = Path(str(row.get("local_path") or ""))
        if (
            not local_path.is_file()
            or sha256_file(local_path) != str(row.get("sha256") or "")
            or row.get("hashes_match") is not True
        ):
            raise ValueError(
                f"domain-repair resume rejected changed source {row.get('source_id')}"
            )
    source_recovery: dict[str, Any] | None = None
    if not sample_rows:
        sample_rows, source_blockers = recover_staged_simulation_sources(facts, out_dir)
        if source_blockers:
            raise ValueError("; ".join(source_blockers))
        source_recovery = {
            "mode": "staged_hash_bound_recovery",
            "vivado_facts_sha256": facts_sha256,
            "source_count": len(sample_rows),
        }

    if coverage.get("status") != "pass":
        raise ValueError("domain-repair resume source-review coverage is not pass")
    records = [
        row for row in coverage.get("records", []) if isinstance(row, dict)
    ]
    if len(records) != coverage.get("chunk_count"):
        raise ValueError("domain-repair resume source-review record count is inconsistent")
    llm_dir = (out_dir / "llm").resolve()
    source_reviews: list[dict[str, Any]] = []
    for row in records:
        record_path = Path(str(row.get("path") or ""))
        try:
            record_path.resolve(strict=True).relative_to(llm_dir)
        except (FileNotFoundError, ValueError) as exc:
            raise ValueError(
                f"domain-repair resume source-review record is missing/outside LLM directory: {exc}"
            ) from exc
        if sha256_file(record_path) != row.get("sha256"):
            raise ValueError("domain-repair resume source-review record hash changed")
        record = read_json(record_path)
        output = record.get("output") if isinstance(record.get("output"), dict) else {}
        if (
            record.get("error")
            or record.get("used_fallback") is True
            or output.get("status") not in {"pass", "ready"}
        ):
            raise ValueError("domain-repair resume source-review record is not a real pass")
        source_reviews.append(output)

    covered_sources = {
        str(value) for value in coverage.get("source_ids", []) if str(value)
    }
    candidate_selection = (
        candidate.get("validated_selection")
        if isinstance(candidate.get("validated_selection"), dict)
        else {}
    )
    selection_candidates = [
        candidate_selection,
        recover_current_selector(out_dir, facts, sample_rows) or {},
        recover_historical_selection(out_dir, facts, sample_rows) or {},
    ]
    selection = next(
        (
            row
            for row in selection_candidates
            if {
                str(value)
                for value in row.get("relevant_sample_source_ids", [])
                if str(value)
            }
            == covered_sources
            and covered_sources
        ),
        {},
    )
    if not selection:
        raise ValueError(
            "domain-repair resume has no current-fact selector compatible with source-review coverage"
        )
    selected_sources = covered_sources
    recovered_candidate = recover_best_valid_domain_candidate(
        out_dir,
        facts,
        inputs["profile"],
        sample_rows,
        selection,
    )
    if recovered_candidate is not None:
        candidate = recovered_candidate
        candidate.update(current_selector_provenance(out_dir, facts))
        candidate["source_review_coverage"] = {
            "path": str(coverage_path.resolve()),
            "sha256": sha256_file(coverage_path),
        }
    source_manifest = llm_sample_source_manifest(sample_rows)
    compact_source_manifest = {
        "complete_source_ids": [
            str(row.get("source_id") or "") for row in source_manifest
        ],
        "complete_source_count": len(source_manifest),
        "complete_source_ids_sha256": canonical_sha256(
            sorted(str(row.get("source_id") or "") for row in source_manifest)
        ),
        "relevant_source_records": [
            row
            for row in source_manifest
            if str(row.get("source_id") or "") in selected_sources
        ],
    }
    output_contract = board_interface_domain_output_contract()
    domain_inputs = {
        "vivado_facts": selected_fact_subgraph(
            facts, str(selection.get("selected_cell_id") or "")
        ),
        "target_board_profile": inputs["profile"],
        "validated_llm_selection": selection,
        "sample_simulation_source_manifest": compact_source_manifest,
        "sample_source_semantic_reviews": source_reviews,
        "sample_source_review_coverage": coverage,
        "deterministic_output_contract": output_contract,
        "resume_evidence": {
            "facts_path": str(facts_path.resolve()),
            "facts_sha256": sha256_file(facts_path),
            "historical_identity_facts_sha256": (
                identity.get("vivado_facts_sha256") if facts_rebound else None
            ),
            "facts_rebound": facts_rebound,
            "coverage_path": str(coverage_path.resolve()),
            "coverage_sha256": sha256_file(coverage_path),
            "candidate_path": str(candidate_path.resolve()),
            "candidate_sha256": sha256_file(candidate_path),
        },
    }
    provenance_fields = {
        key: candidate.get(key)
        for key in (
            "selector_record_path",
            "source_review_coverage",
            "validated_selection",
            "selector_progressive_selection",
            "selector_coverage_ledger",
        )
    }
    if recovered_candidate is not None:
        provenance_fields["recovered_from_historical_agent_record"] = (
            recovered_candidate.get("recovered_from_historical_agent_record")
        )
    if selection.get("recovered_from_historical_agent_record"):
        provenance_fields["recovered_selection"] = selection.get(
            "recovered_from_historical_agent_record"
        )
    if selection.get("recovered_from_current_selector"):
        provenance_fields["recovered_selection"] = selection.get(
            "recovered_from_current_selector"
        )
    if source_recovery is not None:
        provenance_fields["staged_source_recovery"] = source_recovery

    def annotate_and_persist(record: dict[str, Any]) -> dict[str, Any]:
        record.update(provenance_fields)
        record["validation_contract_schema_version"] = (
            DOMAIN_OUTPUT_CONTRACT_SCHEMA_VERSION
        )
        record["validation_contract_sha256"] = canonical_sha256(output_contract)
        result_path = Path(str(record.get("result_path") or ""))
        try:
            result_path.resolve().relative_to(llm_dir)
        except ValueError:
            record["error"] = (
                "board-interface domain record path is outside its LLM artifact directory"
            )
        else:
            write_json(result_path, record)
        return record

    candidate["error"] = None
    candidate["used_fallback"] = False
    _, candidate_errors = validate_interpretation(
        candidate, facts, inputs["profile"], [dict(row) for row in sample_rows]
    )
    repaired = run_board_interface_domain_repair_loop(
        run_stage_agent,
        out_dir,
        facts,
        inputs["profile"],
        sample_rows,
        domain_inputs,
        board_interface_domain_prompt_rules(),
        candidate,
        candidate_errors,
        annotate_and_persist,
        starting_attempt=int(candidate.get("deterministic_repair_attempt") or 0),
    )
    interpretation, blockers = validate_interpretation(
        repaired, facts, inputs["profile"], [dict(row) for row in sample_rows]
    )
    if blockers:
        report = {
            **identity,
            "status": "fail",
            "llm_interpretation_record": str(repaired.get("result_path") or ""),
            "llm_interpretation_prompt": str(repaired.get("request_path") or ""),
            "blockers": blockers,
        }
        write_json(identity_path, report)
        return report

    canonical_identity = _canonical_identity_contract(
        interpretation=interpretation,
        facts=facts,
        facts_path=facts_path,
        sample_rows=sample_rows,
        agent_record=repaired,
    )
    wrapper = _source_index(sample_rows).get(
        str(interpretation.get("wrapper_source_id") or ""), {}
    )
    axi = canonical_identity.get("axi_interfaces", [])
    report = {
        **identity,
        "status": "pass",
        "sample_project": str(inputs["xpr_path"]),
        "sample_project_sha256": current_xpr_sha256,
        "vivado_facts_path": str(facts_path),
        "vivado_facts_sha256": facts_sha256,
        "blockers": [],
        "llm_interpretation_record": str(repaired.get("result_path") or ""),
        "llm_interpretation_prompt": str(repaired.get("request_path") or ""),
        # A resumed identity must rebind the current Vivado-exported VCS
        # authority.  Historical recovery records may predate this reference;
        # only the current pass artifact and its current hash are accepted.
        "simulator_compile_authority": (
            {
                "path": str((out_dir / "vivado_vcs_compile_authority.json").resolve()),
                "sha256": sha256_file(out_dir / "vivado_vcs_compile_authority.json"),
            }
            if (
                (out_dir / "vivado_vcs_compile_authority.json").is_file()
                and read_json(out_dir / "vivado_vcs_compile_authority.json").get("status") == "pass"
                and read_json(out_dir / "vivado_vcs_compile_authority.json").get("source")
                == "vivado_export_simulation_vcs"
            )
            else {}
        ),
        "exact_user_sample_wrapper": bool(wrapper),
        "simulation_hashes_match_source": bool(sample_rows)
        and all(row.get("hashes_match") for row in sample_rows),
        "wrapper_axi_data_width_match": bool(axi),
        **canonical_identity,
        "source_hashes": [
            {
                "source_id": row["source_id"],
                "role": row["role"],
                "path": row["remote_path"],
                "sha256": row["sha256"],
            }
            for row in canonical_identity["selected_simulation_source_closure"][
                "source_files"
            ]
        ],
        "materialized_sources": canonical_identity[
            "selected_simulation_source_closure"
        ]["source_files"],
        "bounded_primary_source_count": len(sample_rows),
    }
    report.pop("identity_contract_validation", None)
    return write_validated_identity(identity_path, report)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--checkpoint-selector-maps-only",
        action="store_true",
        help="Validate current map records and persist their stable semantic checkpoint without rerunning Vivado or an LLM",
    )
    parser.add_argument(
        "--remote-timeout-sec",
        type=int,
        default=0,
        help="Outer transport/tool timeout; 0 disables it during development",
    )
    return parser.parse_args(argv)


def write_validated_identity(out: Path, report: dict[str, Any]) -> dict[str, Any]:
    """Persist discovery output and fail closed against the shared exact identity gate."""

    write_json(out, report)
    if report.get("status") != "pass":
        return report
    from accagent.framework.board_acceptance_contract import validate_exact_board_identity

    validation = validate_exact_board_identity(out)
    report["identity_contract_validation"] = validation
    if validation.get("status") != "pass":
        report["status"] = "fail"
        report["exact_user_sample_wrapper"] = False
        report["blockers"] = [
            *[str(value) for value in report.get("blockers", [])],
            *[
                f"exact identity contract: {value}"
                for value in validation.get("blockers", [])
                if str(value)
            ],
        ]
    write_json(out, report)
    return report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir.resolve()
    out_dir = run_dir / "verification" / "board_interface"
    out = (args.out or out_dir / "board_source_identity.json").resolve()
    if args.checkpoint_selector_maps_only:
        try:
            result = materialize_existing_selector_map_checkpoint(run_dir, out_dir)
        except Exception as exc:
            print(f"selector map checkpoint bootstrap failed: {exc}", file=sys.stderr)
            return 1
        print(result["checkpoint"]["path"])
        return 0
    try:
        report = build_report(run_dir, out_dir, args.remote_timeout_sec)
    except Exception as exc:
        report = {
            "schema_version": IDENTITY_SCHEMA_VERSION,
            "status": "fail",
            "run_dir": str(run_dir),
            "blockers": [str(exc)],
            "policy": {
                "vivado_or_llm_unavailable_fails_closed": True,
                "no_regex_or_filename_guess_fallback": True,
            },
        }
    report = write_validated_identity(out, report)
    print(out)
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
