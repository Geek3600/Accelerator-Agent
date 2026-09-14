from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.verification import sample_project_board_interface_discovery as discovery
from scripts.verification import sample_project_board_interface_impl as impl
from accagent.framework.board_acceptance_contract import validate_exact_board_identity
from tests.test_board_acceptance_contract import _case as exact_contract_case


def encoded(value: object) -> str:
    return str(value).encode("utf-8").hex()


def record(tag: str, *values: object) -> str:
    return "\t".join([tag, *(encoded(value) for value in values)])


class VivadoFactParsingTests(unittest.TestCase):
    def test_nested_vivado_relation_sets_have_stable_order(self) -> None:
        bd = "/projects/sample/design.bd"
        missing = "\n".join(
            [
                "Missing instances:",
                "Index  Instance Path  File Path  Line",
                "-----  -------------  ---------  ----",
                "< empty >",
            ]
        )
        rows = [
            record("META", "schema", "spatialaccagent.vivado_fact_stream.v1"),
            record("META", "project_open_status", "pass"),
            record("META", "simulation_fileset_status", "pass"),
            record("META", "compile_order_status", "pass"),
            record("META", "compile_report_status", "pass"),
            record("META", "missing_instance_report_status", "pass"),
            record("META", "simulator_export_status", "pass"),
            record("META", "fact_export_status", "pass"),
            record("META", "top_module", "top"),
            record("SOURCE", 0, "/projects/sample/top.sv"),
            record("SOURCE_PROPERTY", 0, "USED_IN", "simulation"),
            record("MISSING_REPORT", missing),
            record("BD", bd, "design", "pass", 0, ""),
            record("OBJECT", bd, "cell", "/slot", ""),
            record("OBJECT", bd, "net", "/net_b", ""),
            record("OBJECT", bd, "net", "/net_a", ""),
            record("NETREF", bd, "cell", "/slot", "net", "/net_b"),
            record("NETREF", bd, "cell", "/slot", "net", "/net_a"),
            record("MEMBER", bd, "cell", "/slot", "pin", "/slot/z"),
            record("MEMBER", bd, "cell", "/slot", "pin", "/slot/a"),
        ]
        facts = impl.parse_vivado_fact_stream(("\n".join(rows) + "\n").encode())
        cell = next(row for row in facts["objects"] if row["kind"] == "cell")
        self.assertEqual(
            cell["connected_nets"],
            [{"kind": "net", "path": "/net_a"}, {"kind": "net", "path": "/net_b"}],
        )
        self.assertEqual(
            cell["members"],
            [{"kind": "pin", "path": "/slot/a"}, {"kind": "pin", "path": "/slot/z"}],
        )

    def test_structured_stream_builds_source_ownership_and_empty_unresolved_list(self) -> None:
        xpr = "/projects/sample/project.xpr"
        wrapper = "/projects/sample/generated/wrapper.sv"
        slot = "/projects/sample/generated/slot.sv"
        bd = "/projects/sample/design.bd"
        cell = "/slot_0"
        missing = "\n".join(
            [
                "Missing instances for 'simulation' with fileset 'sim_1':",
                "Index  Instance Path  File Path  Line",
                "-----  -------------  ---------  ----",
                "< empty >",
            ]
        )
        rows = [
            record("META", "schema", "spatialaccagent.vivado_fact_stream.v1"),
            record("META", "vivado_version", "2021.1"),
            record("META", "project_path", xpr),
            record("META", "project_open_status", "pass"),
            record("META", "simulation_fileset_status", "pass"),
            record("META", "simulation_fileset", "sim_1"),
            record("META", "top_module", "sample_wrapper"),
            record("META", "compile_order_status", "pass"),
            record("META", "compile_report_status", "pass"),
            record("META", "missing_instance_report_status", "pass"),
            record("META", "simulator_export_status", "pass"),
            record("META", "fact_export_status", "pass"),
            record("SOURCE", 0, slot),
            record("SOURCE_PROPERTY", 0, "LIBRARY", "slot_lib"),
            record("SOURCE_PROPERTY", 0, "FILE_TYPE", "SystemVerilog"),
            record("SOURCE_PROPERTY", 0, "FILESET_NAME", "sources_1"),
            record("SOURCE_PROPERTY", 0, "USED_IN", "simulation synthesis"),
            record("SOURCE_PROPERTY", 0, "PARENT_COMPOSITE_FILE", "/projects/sample/slot.xci"),
            record("SOURCE", 1, wrapper),
            record("SOURCE_PROPERTY", 1, "LIBRARY", "xil_defaultlib"),
            record("SOURCE_PROPERTY", 1, "FILE_TYPE", "SystemVerilog"),
            record("SOURCE_PROPERTY", 1, "FILESET_NAME", "sources_1"),
            record("SOURCE_PROPERTY", 1, "USED_IN", "simulation"),
            record("COMPILE_REPORT", "compile order report"),
            record("MISSING_REPORT", missing),
            record("BD", bd, "design", "pass", 0, ""),
            record("OBJECT", bd, "cell", cell, ""),
            record("PROPERTY", bd, "cell", cell, "CONFIG.Component_Name", "sample_slot"),
            record("CELL_SOURCE", bd, cell, "sample_slot", slot),
        ]
        facts = impl.parse_vivado_fact_stream(("\n".join(rows) + "\n").encode("utf-8"))

        self.assertEqual(facts["status"], "pass")
        self.assertEqual(facts["simulation"]["unresolved_dependencies"], [])
        cell_fact = next(row for row in facts["objects"] if row["kind"] == "cell")
        slot_fact = next(row for row in facts["simulation"]["source_files"] if row["remote_path"] == slot)
        self.assertEqual(slot_fact["owner_cell_ids"], [cell_fact["object_id"]])
        self.assertEqual(cell_fact["simulation_source_ids"], [slot_fact["source_id"]])

    def test_unrecognized_missing_instance_report_fails_closed(self) -> None:
        rows = [
            record("META", "schema", "spatialaccagent.vivado_fact_stream.v1"),
            record("META", "project_open_status", "pass"),
            record("META", "simulation_fileset_status", "pass"),
            record("META", "compile_order_status", "pass"),
            record("META", "compile_report_status", "pass"),
            record("META", "missing_instance_report_status", "pass"),
            record("META", "simulator_export_status", "pass"),
            record("META", "fact_export_status", "pass"),
            record("META", "top_module", "top"),
            record("SOURCE", 0, "/tmp/top.sv"),
            record("SOURCE_PROPERTY", 0, "USED_IN", "simulation"),
            record("MISSING_REPORT", "opaque output"),
            record("BD", "/tmp/design.bd", "design", "pass", 0, ""),
            record("OBJECT", "/tmp/design.bd", "cell", "/slot", ""),
        ]
        facts = impl.parse_vivado_fact_stream(("\n".join(rows) + "\n").encode("utf-8"))
        self.assertEqual(facts["status"], "fail")
        self.assertTrue(any("format was not recognized" in value for value in facts["blockers"]))


class CurrentRunAuthorityTests(unittest.TestCase):
    def write_json(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_xpr_comes_from_index_and_tool_endpoint_comes_from_tool_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            xpr = "/remote/current/sample.xpr"
            self.write_json(
                run_dir / "input" / "target_board_profile.json",
                {"shell": {"vivado_project_path": xpr}},
            )
            self.write_json(
                run_dir / "input" / "sample_project_index.json",
                {
                    "policy": {"timeout_sec": 60},
                    "samples": [
                        {
                            "status": "ok",
                            "source_path": xpr,
                            "host": "eda-user@tool-host",
                            "port": 2202,
                        }
                    ],
                },
            )
            self.write_json(
                run_dir / "input" / "tool_profile.json",
                {
                    "tools": [
                        {
                            "name": "vivado",
                            "role": "synthesis_implementation_bitstream_generation",
                            "host": "eda-user@tool-host",
                            "port": 2202,
                            "executable": "/tools/current/bin/vivado",
                        }
                    ]
                },
            )
            inputs = impl.project_inputs(run_dir)
            self.assertEqual(inputs["xpr_path"], xpr)
            self.assertEqual(inputs["host"], "eda-user@tool-host")
            self.assertEqual(inputs["port"], 2202)
            self.assertEqual(inputs["vivado_executable"], "/tools/current/bin/vivado")

    def test_default_tool_timeout_is_unbounded(self) -> None:
        self.assertEqual(impl.parse_args(["--run-dir", "."]).remote_timeout_sec, 0)
        self.assertEqual(discovery.parse_args(["--run-dir", "."]).remote_timeout_sec, 0)
        self.assertIsNone(impl.command_timeout(0))


class ReplacementBoundaryTests(unittest.TestCase):
    def boundary(self, cell_id: str, rows: list[dict[str, object]]) -> dict[str, object]:
        replaced = str(rows[0]["source_id"])
        return {
            "slot_module": "selected_slot",
            "replaced_source_ids": [replaced],
            "replacement_boundary": {
                "selected_cell_id": cell_id,
                "retained_source_ids": [str(row["source_id"]) for row in rows[1:]],
                "sample_closure_unchanged": True,
                "generated_sources_excluded_from_sample_closure": True,
                "source_module_evidence": [
                    {
                        "source_id": replaced,
                        "source_sha256": rows[0]["sha256"],
                        "declared_modules": ["selected_slot"],
                    }
                ],
            },
        }

    def test_exclusive_slot_source_is_a_valid_replacement_boundary(self) -> None:
        cell = {"object_id": "cell:selected"}
        rows = [
            {"source_id": "source:slot", "sha256": "1" * 64, "owner_cell_ids": ["cell:selected"]},
            {"source_id": "source:wrapper", "sha256": "2" * 64, "owner_cell_ids": []},
        ]
        self.assertEqual(impl._validate_replacement_boundary(self.boundary("cell:selected", rows), cell, rows), [])

    def test_shared_source_cannot_be_replaced(self) -> None:
        cell = {"object_id": "cell:selected"}
        rows = [
            {
                "source_id": "source:shared",
                "sha256": "1" * 64,
                "owner_cell_ids": ["cell:selected", "cell:other"],
            },
            {"source_id": "source:wrapper", "sha256": "2" * 64, "owner_cell_ids": []},
        ]
        errors = impl._validate_replacement_boundary(self.boundary("cell:selected", rows), cell, rows)
        self.assertTrue(any("not exclusive" in value for value in errors))


class ControlAbiTests(unittest.TestCase):
    def facts(self) -> tuple[dict[str, object], dict[str, object]]:
        bd = "/sample/design.bd"
        cell = {
            "object_id": "cell:selected",
            "kind": "cell",
            "bd_path": bd,
            "path": "/slot",
            "owner_path": "",
            "properties": {},
        }
        ports = {
            "start": ("request", "I", 1),
            "clear": ("clear_request", "I", 1),
            "valid": ("result_valid", "O", 1),
            "done": ("result_done", "O", 1),
            "count": ("result_count", "O", 32),
            "status": ("result_status", "O", 4),
        }
        objects = [cell]
        for role, (name, direction, width) in ports.items():
            net_path = f"/{role}_net"
            objects.extend(
                [
                    {
                        "object_id": f"pin:{role}",
                        "kind": "pin",
                        "bd_path": bd,
                        "path": f"/slot/{name}",
                        "owner_path": "/slot",
                        "properties": {
                            "NAME": name,
                            "DIR": direction,
                            "LEFT": str(width - 1) if width > 1 else "",
                            "RIGHT": "0" if width > 1 else "",
                            "TYPE": "undef",
                        },
                        "connected_nets": [{"kind": "net", "path": net_path}],
                    },
                    {
                        "object_id": f"net:{role}",
                        "kind": "net",
                        "bd_path": bd,
                        "path": net_path,
                        "owner_path": "",
                        "properties": {},
                        "connected_nets": [],
                    },
                ]
            )
        return {"objects": objects}, cell

    def control(self, source_id: str) -> dict[str, object]:
        specs = {
            "start": ("request", "input", 1, "control", "pulse"),
            "clear": ("clear_request", "input", 1, "control", "pulse"),
            "valid": ("result_valid", "output", 1, "status", "level"),
            "done": ("result_done", "output", 1, "status", "level"),
            "count": ("result_count", "output", 32, "status", "counter"),
            "status": ("result_status", "output", 4, "status", "level"),
        }
        classifications = [
            {
                "fact_port_id": f"pin:{role}",
                "name": name,
                "direction": direction,
                "width_bits": width,
                "classification": category,
                "semantic_role": role,
                "pulse_or_level": pulse_or_level,
                "clock_domain": "compute_clock",
                "evidence_object_ids": [f"pin:{role}", f"net:{role}"],
                "evidence_source_ids": [source_id],
            }
            for role, (name, direction, width, category, pulse_or_level) in specs.items()
        ]
        return {
            "status": "pass",
            "all_non_interface_ports_classified": True,
            "clock_domain": "compute_clock",
            "port_classifications": classifications,
            "control_ports": [
                {
                    key: classification[key]
                    for key in ("fact_port_id", "semantic_role", "direction", "width_bits", "pulse_or_level", "clock_domain")
                }
                for classification in classifications
            ],
            "configuration_buses": [],
            "configuration_fields": [],
            "signals": {
                role: {
                    "binding_kind": "physical_port",
                    "fact_port_id": f"pin:{role}",
                    "name": name,
                    "direction": direction,
                    "width_bits": width,
                    "semantic": (
                        "status" if role == "status" else pulse_or_level
                    ),
                    "clock_domain": "compute_clock",
                }
                for role, (name, direction, width, _, pulse_or_level) in specs.items()
            },
            "timing": {
                "start_assertion_cycles": 1,
                "clear_assertion_cycles": 1,
                "start_sampling_edge": "rising",
                "clear_sampling_edge": "rising",
                "start_accept_condition": "idle",
                "done_relation_to_valid": "after_final_valid",
                "done_clear_condition": "clear_sampled",
                "count_update_event": "accepted_output",
                "status_update_event": "state_transition",
                "evidence_refs": [source_id],
            },
            "control_sequence": [
                {
                    "event": event,
                    "order": order,
                    "fact_port_ids": [f"pin:{role}" for role in specs],
                    "evidence_source_ids": [source_id],
                }
                for order, event in enumerate(
                    ["configure", "start", "observe_completion", "clear_completion"], start=1
                )
            ],
            "control_sequence_enforcement": "hardware",
        }

    def test_control_semantics_require_vivado_net_and_sample_source_evidence(self) -> None:
        facts, cell = self.facts()
        source_id = "source:control"
        timing = {"clock_domains": [{"name": "compute_clock"}]}
        rows = [{"source_id": source_id}]
        self.assertEqual(impl._validate_control(self.control(source_id), cell, facts, timing, rows), [])

        broken = self.control(source_id)
        broken["port_classifications"][0]["evidence_object_ids"] = ["pin:start"]
        errors = impl._validate_control(broken, cell, facts, timing, rows)
        self.assertTrue(any("exact Vivado net" in value for value in errors))

    def test_derived_done_and_external_orchestrator_preserve_exact_control(self) -> None:
        facts, cell = self.facts()
        facts["objects"] = [
            row
            for row in facts["objects"]
            if row.get("object_id") not in {"pin:done", "net:done"}
        ]
        source_id = "source:control"
        timing = {"clock_domains": [{"name": "compute_clock"}]}
        rows = [{"source_id": source_id}]
        control = self.control(source_id)
        control["port_classifications"] = [
            row
            for row in control["port_classifications"]
            if row.get("fact_port_id") != "pin:done"
        ]
        control["control_ports"] = [
            row
            for row in control["control_ports"]
            if row.get("fact_port_id") != "pin:done"
        ]
        for step in control["control_sequence"]:
            step["fact_port_ids"] = [
                port_id
                for port_id in step["fact_port_ids"]
                if port_id != "pin:done"
            ]
        status = control["signals"]["status"]
        control["signals"]["done"] = {
            **status,
            "binding_kind": "derived_from_physical_port",
            "semantic": "counter_nonzero",
            "derived_from_role": "status",
            "predicate": "value != 0",
            "evidence_object_ids": ["pin:status", "net:status"],
            "evidence_source_ids": [source_id],
        }
        control["control_sequence_enforcement"] = "external_orchestrator"
        self.assertEqual(
            impl._validate_control(control, cell, facts, timing, rows), []
        )

        duplicated = json.loads(json.dumps(control))
        duplicated["signals"]["start"] = {
            **duplicated["signals"]["clear"],
            "binding_kind": "physical_port",
            "semantic": "pulse",
        }
        errors = impl._validate_control(duplicated, cell, facts, timing, rows)
        self.assertTrue(any("duplicates physical port" in value for value in errors))

        unknown_enforcement = json.loads(json.dumps(control))
        unknown_enforcement["control_sequence_enforcement"] = "assumed"
        errors = impl._validate_control(
            unknown_enforcement, cell, facts, timing, rows
        )
        self.assertTrue(any("control_sequence_enforcement" in value for value in errors))


class DomainRepairFlowTests(unittest.TestCase):
    def test_domain_validated_selection_is_a_final_selector_checkpoint(self) -> None:
        selection = {
            "schema_version": "spatialaccagent.board_interface_selection.v1",
            "status": "pass",
            "selected_cell_id": "cell:selected",
            "wrapper_source_id": "source:wrapper",
            "relevant_sample_source_ids": ["source:wrapper"],
            "proposed_replaced_source_ids": ["source:slot"],
            "blockers": [],
        }
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "board_interface"
            checkpoint_path = (
                out_dir
                / "llm"
                / "exact_board_interface_domain_repair_agent_result.json"
            )
            checkpoint_path.parent.mkdir(parents=True)
            checkpoint = {
                "used_fallback": False,
                "error": None,
                "prompt_hash": "domain-prompt",
                "validated_selection": selection,
                "output": {"status": "pass"},
            }
            checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
            with (
                mock.patch.object(
                    impl, "validate_interpretation", return_value=({}, [])
                ),
                mock.patch.object(
                    impl, "_validate_selector_record", return_value=(selection, [])
                ),
                mock.patch.object(
                    impl, "_validate_progressive_final_selection", return_value=[]
                ),
            ):
                record = impl._reuse_domain_validated_selector_checkpoint(
                    out_dir, {}, {}, [], [], None
                )

            self.assertIsNotNone(record)
            self.assertTrue(record["semantic_checkpoint_reuse"])
            self.assertEqual(record["output"], selection)
            self.assertEqual(record["used_fallback"], False)

    def test_current_facts_can_rebind_a_deterministic_valid_domain_checkpoint(self) -> None:
        selection = {
            "selected_cell_id": "cell:selected",
            "wrapper_source_id": "source:wrapper",
            "relevant_sample_source_ids": ["source:wrapper"],
            "proposed_replaced_source_ids": ["source:wrapper"],
        }
        coverage = {
            "status": "pass",
            "source_ids": ["source:wrapper"],
            "chunk_count": 1,
            "records": [],
        }

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out_dir = root / "verification" / "board_interface"
            checkpoint_path = (
                out_dir
                / "llm"
                / "exact_board_interface_domain_repair_agent_result.json"
            )
            checkpoint_path.parent.mkdir(parents=True)
            checkpoint = {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": "exact_board_interface_domain_repair_agent",
                "stage": "verification.layer3.board_interface_discovery.repair",
                "result_path": str(checkpoint_path),
                "prompt_hash": "checkpoint-prompt",
                "used_fallback": False,
                "error": None,
                "validated_selection": selection,
                "output": {
                    "schema_version": impl.INTERPRETATION_SCHEMA_VERSION,
                    "status": "pass",
                },
            }
            checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
            selector = {
                "result_path": str(out_dir / "llm" / "selector.json"),
                "progressive_selection": {"coverage_ledger": {"status": "pass"}},
            }

            with (
                mock.patch.object(
                    impl, "run_progressive_board_selector", return_value=selector
                ),
                mock.patch.object(
                    impl, "_validate_selector_record", return_value=(selection, [])
                ),
                mock.patch.object(impl, "_full_context", return_value=([], [])),
                mock.patch.object(
                    impl,
                    "run_progressive_board_source_review",
                    return_value=([], coverage, []),
                ),
                mock.patch.object(impl, "llm_sample_source_manifest", return_value=[]),
                mock.patch.object(impl, "selected_fact_subgraph", return_value={}),
                mock.patch.object(
                    impl, "validate_interpretation", return_value=({}, [])
                ),
                mock.patch(
                    "accagent.framework.stage_llm.run_stage_agent",
                    side_effect=AssertionError("domain LLM must not rerun"),
                ),
            ):
                result = impl.run_board_interface_agent(root, out_dir, {}, {}, [])

            self.assertTrue(result["semantic_checkpoint_rebound"])
            self.assertEqual(result["source_review_coverage"], coverage)
            self.assertEqual(result["validated_selection"], selection)
            self.assertEqual(result["deterministic_validation_status"], "pass")

    def test_deterministic_errors_are_repaired_with_the_explicit_contract(self) -> None:
        calls: list[dict[str, object]] = []
        selection = {
            "selected_cell_id": "cell:selected",
            "wrapper_source_id": "source:wrapper",
            "relevant_sample_source_ids": [],
            "proposed_replaced_source_ids": [],
        }

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out_dir = root / "verification" / "board_interface"

            def runner(**kwargs: object) -> dict[str, object]:
                calls.append(kwargs)
                agent = str(kwargs["agent"])
                output = {
                    "schema_version": impl.INTERPRETATION_SCHEMA_VERSION,
                    "agent": agent,
                    "stage": str(kwargs["stage"]),
                    "status": "blocked" if len(calls) == 1 else "pass",
                    "summary": "candidate",
                    "wrapper_source_id": "source:wrapper",
                    "wrapper_top_module": "wrapper",
                    "compute_slot_abi": {},
                    "timing_contract": {},
                    "axi_interfaces": [],
                    "blockers": [],
                }
                return {
                    "schema_version": "spatialaccagent.stage_worker_record.v0",
                    "agent": agent,
                    "stage": str(kwargs["stage"]),
                    "prompt_hash": f"prompt-{len(calls)}",
                    "result_path": str(out_dir / "llm" / f"{agent}_result.json"),
                    "used_fallback": False,
                    "error": None,
                    "output": output,
                }

            selector = {
                "result_path": str(out_dir / "llm" / "selector.json"),
                "progressive_selection": {"coverage_ledger": {"status": "pass"}},
            }
            patches = [
                mock.patch.object(
                    impl, "run_progressive_board_selector", return_value=selector
                ),
                mock.patch.object(
                    impl, "_validate_selector_record", return_value=(selection, [])
                ),
                mock.patch.object(impl, "_full_context", return_value=([], [])),
                mock.patch.object(
                    impl,
                    "run_progressive_board_source_review",
                    return_value=([], {"status": "pass"}, []),
                ),
                mock.patch.object(impl, "llm_sample_source_manifest", return_value=[]),
                mock.patch.object(impl, "selected_fact_subgraph", return_value={}),
                mock.patch.object(
                    impl,
                    "validate_interpretation",
                    side_effect=[
                        ({}, ["required_ports shape mismatch"]),
                        ({}, ["AXI clock must reference a timing-domain name"]),
                        ({}, []),
                    ],
                ),
                mock.patch(
                    "accagent.framework.stage_llm.run_stage_agent", side_effect=runner
                ),
            ]
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
                result = impl.run_board_interface_agent(
                    root, out_dir, {}, {}, []
                )

            self.assertEqual(len(calls), 3)
            contract = calls[0]["inputs"]["deterministic_output_contract"]
            self.assertIn(
                "fact_port_id",
                contract["compute_slot_abi"]["required_ports"]["item_required_fields"],
            )
            self.assertEqual(
                contract["timing_contract"]["calibration"]["container"],
                "nonempty list",
            )
            self.assertEqual(
                contract["timing_contract"]["clock_domains"]["value_rules"]["source"]["allowed_values"],
                ["exact_sample_project", "exact_sample_ip"],
            )
            self.assertIn(
                "round(1000000000000 / frequency_hz)",
                contract["timing_contract"]["clock_domains"]["value_rules"]["period_ps"],
            )
            self.assertEqual(
                contract["timing_contract"]["calibration"]["value_rules"]["source"]["allowed_values"],
                ["exact_sample_memory_model", "exact_sample_ip"],
            )
            self.assertIn(
                "evidence_refs",
                contract["control_abi"]["timing_required_fields"],
            )
            self.assertIn(
                "name",
                contract["axi_interfaces"]["item_required_fields"],
            )
            self.assertIn(
                "derived_done", contract["control_abi"]["signals"]
            )
            self.assertIn(
                "fact_interface_id",
                contract["axi_interfaces"]["item_required_fields"],
            )
            self.assertIn("signal_fact_map", contract["axi_interfaces"])
            self.assertEqual(
                calls[1]["agent"], "exact_board_interface_domain_repair_agent"
            )
            self.assertEqual(
                calls[1]["inputs"]["deterministic_validation_errors"],
                ["required_ports shape mismatch"],
            )
            self.assertEqual(
                calls[2]["inputs"]["deterministic_validation_errors"],
                ["AXI clock must reference a timing-domain name"],
            )
            self.assertEqual(result["deterministic_repair_attempt"], 2)
            self.assertEqual(
                result["deterministic_validation_status"], "pass"
            )


class ProgressiveSelectorTests(unittest.TestCase):
    def fixture(self) -> tuple[dict[str, object], list[dict[str, object]]]:
        bd = "/sample/design.bd"
        objects = [
            {
                "object_id": "cell:one",
                "kind": "cell",
                "bd_path": bd,
                "path": "/arbitrary_a",
                "owner_path": "",
                "properties": {"CONFIG.Component_Name": "opaque_a"},
                "connected_nets": [],
                "members": [],
                "simulation_source_ids": ["source:one"],
            },
            {
                "object_id": "pin:one",
                "kind": "pin",
                "bd_path": bd,
                "path": "/arbitrary_a/member",
                "owner_path": "/arbitrary_a",
                "properties": {"INTF": "TRUE", "NAME": "member"},
                "connected_nets": [{"kind": "net", "path": "/n"}],
                "members": [],
                "simulation_source_ids": [],
            },
            {
                "object_id": "cell:two",
                "kind": "cell",
                "bd_path": bd,
                "path": "/qwen_cnn_core_named_but_not_special",
                "owner_path": "",
                "properties": {"CONFIG.Component_Name": "opt_named_but_not_special"},
                "connected_nets": [],
                "members": [],
                "simulation_source_ids": ["source:two"],
            },
            {
                "object_id": "port:top",
                "kind": "port",
                "bd_path": bd,
                "path": "/external",
                "owner_path": "",
                "properties": {"NAME": "external"},
                "connected_nets": [{"kind": "net", "path": "/n"}],
                "members": [],
                "simulation_source_ids": [],
            },
            {
                "object_id": "net:n",
                "kind": "net",
                "bd_path": bd,
                "path": "/n",
                "owner_path": "",
                "properties": {"NAME": "n"},
                "connected_nets": [],
                "members": [],
                "simulation_source_ids": [],
            },
        ]
        facts = {
            "schema_version": impl.FACT_SCHEMA_VERSION,
            "status": "pass",
            "project": {"top_module": "sample_top"},
            "simulation": {
                "source_files": [],
                "fileset_properties": {},
                "unresolved_dependencies": [],
                "recursive_dependency_scan_complete": True,
                "external_library_dependencies": [],
                "simulator_export_contexts": [
                    {
                        "remote_path": "/tmp/spatialaccagent_board_old/vcs_export/vcs/sample.sh",
                        "sha256": "e" * 64,
                        "text": (
                            "# Generated by Vivado on Mon Jan 01 00:00:00 UTC 2024\n"
                            "vlogan_opts='-full64 +define+KEEP_ME'\n"
                            "include_path='/real/project/include'\n"
                        ),
                    }
                ],
            },
            "block_designs": [{"remote_path": bd, "status": "pass"}],
            "objects": objects,
            "blockers": [],
        }
        rows = [
            {
                "source_id": source_id,
                "role": "simulation_source",
                "remote_path": f"/sample/{index}.sv",
                "sha256": str(index) * 64,
                "size_bytes": 64,
                "compile_order": index,
                "library": "work",
                "language": "SystemVerilog",
                "file_type": "SystemVerilog",
                "file_set": "sim_1",
                "used_in": ["simulation"],
                "parent_composite_file": "",
                "owner_cell_ids": [f"cell:{'one' if index == 1 else 'two'}"],
            }
            for index, source_id in enumerate(("source:one", "source:two"), start=1)
        ]
        return facts, rows

    def map_output(
        self, coverage: dict[str, list[str]], *, summary_padding: int = 0
    ) -> dict[str, object]:
        return {
            "schema_version": impl.SELECTION_MAP_SCHEMA_VERSION,
            "agent": "map",
            "stage": "verification.layer3.board_interface_selection.map",
            "status": "pass",
            "summary": "reviewed" + ("x" * summary_padding),
            "reviewed_object_ids": list(coverage["object_ids"]),
            "reviewed_source_ids": list(coverage["source_ids"]),
            "candidate_cells": [],
            "candidate_wrapper_sources": [],
            "candidate_relevant_sources": [],
            "candidate_replacement_sources": [],
            "findings": [],
            "blockers": [],
        }

    def test_evidence_partition_covers_every_fact_and_source_once_without_name_filtering(self) -> None:
        facts, rows = self.fixture()
        _, units = impl.selection_evidence_units(facts, rows)
        coverage = impl._coverage_from_units(units)
        object_occurrences = [
            value for unit in units for value in unit.get("object_ids", [])
        ]
        source_occurrences = [
            value for unit in units for value in unit.get("source_ids", [])
        ]
        self.assertEqual(set(coverage["object_ids"]), {row["object_id"] for row in facts["objects"]})
        self.assertEqual(set(coverage["source_ids"]), {row["source_id"] for row in rows})
        self.assertEqual(len(object_occurrences), len(set(object_occurrences)))
        self.assertEqual(len(source_occurrences), len(set(source_occurrences)))
        serialized = json.dumps(units)
        self.assertIn("qwen_cnn_core_named_but_not_special", serialized)
        self.assertIn("opt_named_but_not_special", serialized)

    def test_map_gate_rejects_failed_missing_and_duplicate_coverage(self) -> None:
        facts, rows = self.fixture()
        _, units = impl.selection_evidence_units(facts, rows)
        coverage = impl._coverage_from_units(units)
        known_objects = set(coverage["object_ids"])
        known_sources = set(coverage["source_ids"])
        known_cells = {"cell:one", "cell:two"}

        valid = {"used_fallback": False, "error": None, "output": self.map_output(coverage)}
        self.assertEqual(
            impl._validate_selection_map_record(
                valid, coverage, known_cells, known_objects, known_sources
            )[1],
            [],
        )

        duplicate = json.loads(json.dumps(valid))
        duplicate["output"]["reviewed_object_ids"].append(coverage["object_ids"][0])
        self.assertTrue(
            any(
                "exactly its assigned" in error
                for error in impl._validate_selection_map_record(
                    duplicate, coverage, known_cells, known_objects, known_sources
                )[1]
            )
        )
        missing = json.loads(json.dumps(valid))
        missing["output"]["reviewed_source_ids"] = []
        self.assertTrue(
            impl._validate_selection_map_record(
                missing, coverage, known_cells, known_objects, known_sources
            )[1]
        )
        failed = json.loads(json.dumps(valid))
        failed["error"] = "context_length_exceeded"
        self.assertTrue(
            impl._validate_selection_map_record(
                failed, coverage, known_cells, known_objects, known_sources
            )[1]
        )

    def test_framework_binds_map_coverage_without_llm_id_echo(self) -> None:
        facts, rows = self.fixture()
        _, units = impl.selection_evidence_units(facts, rows)
        coverage = impl._coverage_from_units(units)
        record = {
            "used_fallback": False,
            "error": None,
            "output": {
                **self.map_output(coverage),
                "reviewed_object_ids": [],
                "reviewed_source_ids": [],
            },
        }

        bound = impl._bind_framework_map_coverage(record, coverage)
        self.assertEqual(
            bound["output"]["reviewed_object_ids"], coverage["object_ids"]
        )
        self.assertEqual(
            bound["output"]["reviewed_source_ids"], coverage["source_ids"]
        )
        self.assertEqual(
            impl._validate_selection_map_record(
                bound,
                coverage,
                {"cell:one", "cell:two"},
                set(coverage["object_ids"]),
                set(coverage["source_ids"]),
            )[1],
            [],
        )

    def test_progressive_selector_final_prompt_uses_reviews_not_raw_projection(self) -> None:
        facts, rows = self.fixture()
        calls: list[dict[str, object]] = []
        map_attempts: dict[str, int] = {}
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "board_interface"

            def runner(**kwargs: object) -> dict[str, object]:
                calls.append(kwargs)
                agent = str(kwargs["agent"])
                inputs = kwargs["inputs"]
                if "_map_" in agent:
                    map_attempts[agent] = map_attempts.get(agent, 0) + 1
                    coverage = inputs["chunk"]["assigned_coverage"]
                    output = self.map_output(coverage, summary_padding=1200)
                    if "cell:one" in coverage["object_ids"]:
                        output["candidate_cells"] = [
                            {
                                "cell_id": "cell:one",
                                "evidence_object_ids": ["cell:one"],
                                "evidence_source_ids": [],
                                "rationale": "structural candidate",
                            }
                        ]
                    if "source:one" in coverage["source_ids"]:
                        source = {
                            "source_id": "source:one",
                            "evidence_object_ids": [],
                            "evidence_source_ids": ["source:one"],
                            "rationale": "exclusive implementation evidence",
                        }
                        output["candidate_relevant_sources"] = [source]
                        output["candidate_replacement_sources"] = [source]
                    if "source:two" in coverage["source_ids"]:
                        source = {
                            "source_id": "source:two",
                            "evidence_object_ids": [],
                            "evidence_source_ids": ["source:two"],
                            "rationale": "wrapper evidence",
                        }
                        output["candidate_wrapper_sources"] = [source]
                        output["candidate_relevant_sources"] = [source]
                    if agent.endswith("_000_agent") and map_attempts[agent] == 1:
                        foreign_source = next(
                            source_id
                            for source_id in ("source:one", "source:two")
                            if source_id not in coverage["source_ids"]
                        )
                        output["candidate_relevant_sources"].append(
                            {
                                "source_id": foreign_source,
                                "evidence_object_ids": [],
                                "evidence_source_ids": [foreign_source],
                                "rationale": "invalid cross-chunk nomination",
                            }
                        )
                elif "_reduce_" in agent:
                    children = inputs["semantic_map_or_reduce_outputs"]
                    output = {
                        "schema_version": impl.SELECTION_REDUCE_SCHEMA_VERSION,
                        "agent": agent,
                        "stage": "verification.layer3.board_interface_selection.reduce",
                        "status": "pass",
                        "summary": "merged semantic evidence",
                        "candidate_cells": [
                            row
                            for child in children
                            for row in child["candidate_cells"]
                        ],
                        "candidate_wrapper_sources": [
                            row
                            for child in children
                            for row in child["candidate_wrapper_sources"]
                        ],
                        "candidate_relevant_sources": [
                            row
                            for child in children
                            for row in child["candidate_relevant_sources"]
                        ],
                        "candidate_replacement_sources": [
                            row
                            for child in children
                            for row in child["candidate_replacement_sources"]
                        ],
                        "findings": [
                            row for child in children for row in child["findings"]
                        ],
                        "blockers": [],
                    }
                else:
                    output = {
                        "schema_version": "spatialaccagent.board_interface_selection.v1",
                        "agent": agent,
                        "stage": "verification.layer3.board_interface_selection",
                        "status": "pass",
                        "summary": "selected from progressive evidence",
                        "selected_cell_id": "cell:one",
                        "wrapper_source_id": "source:two",
                        "relevant_sample_source_ids": ["source:one", "source:two"],
                        "proposed_replaced_source_ids": ["source:one"],
                        "blockers": [],
                    }
                result = {
                    "schema_version": "spatialaccagent.stage_worker_record.v0",
                    "agent": agent,
                    "used_fallback": False,
                    "error": None,
                    "result_path": str(out_dir / "llm" / f"{agent}_result.json"),
                    "output": output,
                }
                if "_map_" in agent:
                    from accagent.framework import stage_llm
                    from accagent.framework.llm_io import build_prompt

                    prompt_inputs, _, _ = (
                        stage_llm.build_stage_agent_prompt_inputs(inputs)
                    )
                    prompt = build_prompt(
                        agent=agent,
                        task=kwargs["task"],
                        inputs=prompt_inputs,
                        output_schema=kwargs["output_schema"],
                        rules=kwargs["prompt_rules"],
                    )
                    prompt_path = out_dir / "llm" / f"{agent}_prompt.md"
                    prompt_path.parent.mkdir(parents=True, exist_ok=True)
                    prompt_path.write_text(prompt, encoding="utf-8")
                    contract = impl._selector_map_llm_contract()
                    result.update(
                        {
                            "stage": kwargs["stage"],
                            "model": contract["model"],
                            "reasoning_effort": contract["reasoning_effort"],
                            "mode": contract["mode"],
                            "stream": contract["stream"],
                            "transport": contract["transport"],
                            "prompt_protocol": contract["prompt_protocol"],
                            "prompt_hash": stage_llm.prompt_hash(prompt),
                            "request_path": str(prompt_path),
                        }
                    )
                impl.write_json(Path(result["result_path"]), result)
                return result

            _, units = impl.selection_evidence_units(facts, rows)
            largest_unit = max(impl._compact_size(unit) for unit in units)
            record = impl.run_progressive_board_selector(
                runner,
                out_dir,
                facts,
                {"board": "current-user-sample"},
                rows,
                map_budget_bytes=largest_unit + 256,
                reduce_budget_bytes=3500,
            )
            self.assertEqual(record["output"]["status"], "pass")
            self.assertGreater(record["progressive_selection"]["map_chunk_count"], 1)
            self.assertGreater(record["progressive_selection"]["reduction_record_count"], 0)
            repair_calls = [
                call
                for call in calls
                if "deterministic_validation_errors" in call["inputs"]
            ]
            self.assertEqual(len(repair_calls), 1)
            self.assertTrue(
                any(
                    "out-of-chunk source evidence" in error
                    for error in repair_calls[0]["inputs"][
                        "deterministic_validation_errors"
                    ]
                )
            )
            self.assertIn("candidate_output", repair_calls[0]["inputs"])
            reduce_calls = [
                call for call in calls if "_reduce_" in str(call["agent"])
            ]
            self.assertTrue(reduce_calls)
            for call in reduce_calls:
                reduce_text = json.dumps(call["inputs"])
                self.assertNotIn("reviewed_object_ids", reduce_text)
                self.assertNotIn("reviewed_source_ids", reduce_text)
                self.assertNotIn("assigned_coverage", reduce_text)
            final_inputs = calls[-1]["inputs"]
            self.assertEqual(
                set(final_inputs),
                {
                    "global_vivado_context",
                    "target_board_profile",
                    "progressive_evidence_reviews",
                    "complete_coverage",
                },
            )
            final_text = json.dumps(final_inputs)
            self.assertNotIn("evidence_units", final_text)
            self.assertNotIn("source_files", final_text)
            self.assertNotIn("reviewed_object_ids", final_text)
            self.assertNotIn("reviewed_source_ids", final_text)
            self.assertTrue(final_inputs["complete_coverage"]["all_fact_and_source_units_reviewed"])
            ledger_ref = record["progressive_selection"]["coverage_ledger"]
            ledger_path = Path(ledger_ref["path"])
            self.assertTrue(ledger_path.is_file())
            self.assertEqual(impl.sha256_file(ledger_path), ledger_ref["sha256"])
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            checkpoint_ref = record["progressive_selection"][
                "map_semantic_checkpoint"
            ]
            self.assertEqual(ledger["map_semantic_checkpoint"], checkpoint_ref)
            map_workers = [
                row for row in ledger["worker_records"] if row["phase"] == "map"
            ]
            self.assertEqual(len(map_workers), record["progressive_selection"]["map_chunk_count"])
            for index, worker in enumerate(map_workers):
                self.assertEqual(worker["chunk_index"], index)
                self.assertRegex(worker["semantic_fingerprint"], r"^[0-9a-f]{64}$")
                self.assertEqual(
                    worker["reuse_authority"]["checkpoint_semantic_fingerprint"],
                    worker["semantic_fingerprint"],
                )
            persisted = json.loads(Path(record["result_path"]).read_text(encoding="utf-8"))
            self.assertEqual(persisted["progressive_selection"]["coverage_ledger"], ledger_ref)

            approval = {
                "artifact": {"path": "/approval.json", "sha256": "a" * 64},
                "decision": {
                    "schema_version": "spatialaccagent.board_selection_human_approval.v0",
                    "status": "approved",
                    "action_id": "repair.board_target_selection_with_bounded_approval",
                    "decision": "agent_select_exactly_one_of_approved_candidates",
                    "approved_candidate_cell_ids": ["cell:one"],
                    "approval_text": "Either current candidate is acceptable.",
                },
            }
            calls.clear()
            approved_record = impl.run_progressive_board_selector(
                runner,
                out_dir,
                facts,
                {"board": "current-user-sample"},
                rows,
                human_approval=approval,
                map_budget_bytes=largest_unit + 256,
                reduce_budget_bytes=3500,
            )
            self.assertEqual(approved_record["output"]["status"], "pass")
            self.assertFalse(any("_map_" in str(call["agent"]) for call in calls))
            self.assertEqual(
                calls[-1]["inputs"]["human_board_selection_approval"], approval
            )

            fresh_export_facts = json.loads(json.dumps(facts))
            fresh_export_facts["simulation"]["simulator_export_contexts"] = [
                {
                    "remote_path": "/tmp/spatialaccagent_board_fresh/vcs_export/vcs/sample.sh",
                    "sha256": "f" * 64,
                    "text": (
                        "# Generated by Vivado on Tue Feb 02 02:02:02 UTC 2027\n"
                        "vlogan_opts='-full64 +define+KEEP_ME'\n"
                        "include_path='/real/project/include'\n"
                    ),
                }
            ]
            calls.clear()
            reused_record = impl.run_progressive_board_selector(
                runner,
                out_dir,
                fresh_export_facts,
                {"board": "current-user-sample"},
                rows,
                map_budget_bytes=largest_unit + 256,
                reduce_budget_bytes=3500,
            )
            self.assertEqual(reused_record["output"]["status"], "pass")
            self.assertFalse(any("_map_" in str(call["agent"]) for call in calls))

            structural_change = json.loads(json.dumps(fresh_export_facts))
            structural_change["objects"][0]["properties"]["CONFIG.NEW_SEMANTIC"] = "1"
            calls.clear()
            changed_record = impl.run_progressive_board_selector(
                runner,
                out_dir,
                structural_change,
                {"board": "current-user-sample"},
                rows,
                map_budget_bytes=largest_unit + 256,
                reduce_budget_bytes=3500,
            )
            self.assertEqual(changed_record["output"]["status"], "pass")
            self.assertEqual(
                sum("_map_" in str(call["agent"]) for call in calls),
                1,
            )

            compile_option_change = json.loads(json.dumps(structural_change))
            compile_option_change["simulation"]["simulator_export_contexts"][0][
                "text"
            ] = compile_option_change["simulation"]["simulator_export_contexts"][0][
                "text"
            ].replace("+define+KEEP_ME", "+define+CHANGED_SEMANTICS")
            calls.clear()
            changed_options_record = impl.run_progressive_board_selector(
                runner,
                out_dir,
                compile_option_change,
                {"board": "current-user-sample"},
                rows,
                map_budget_bytes=largest_unit + 256,
                reduce_budget_bytes=3500,
            )
            self.assertEqual(changed_options_record["output"]["status"], "pass")
            self.assertEqual(
                sum("_map_" in str(call["agent"]) for call in calls),
                changed_options_record["progressive_selection"]["map_chunk_count"],
            )


class DomainSourceReviewTests(unittest.TestCase):
    def test_oversized_source_is_losslessly_segmented(self) -> None:
        text = "".join(f"assign signal_{index} = value_{index};\n" for index in range(500))
        context = {
            "source_id": "source:large",
            "sha256": impl.sha256_bytes(text.encode("utf-8")),
            "text_sha256": impl.sha256_bytes(text.encode("utf-8")),
            "text_encoding": "utf-8",
            "text": text,
            "truncated": False,
        }
        segments = impl._source_review_segments([context], 2048)
        self.assertGreater(len(segments), 1)
        self.assertEqual("".join(row["text"] for row in segments), text)
        self.assertEqual(segments[0]["start_byte"], 0)
        self.assertEqual(segments[-1]["end_byte"], len(text.encode("utf-8")))
        for previous, current in zip(segments, segments[1:]):
            self.assertEqual(previous["end_byte"], current["start_byte"])
            self.assertEqual(previous["end_char"], current["start_char"])
        for row in segments:
            self.assertEqual(
                row["segment_text_sha256"],
                impl.sha256_bytes(row["text"].encode(row["text_encoding"])),
            )

    def test_full_source_chunks_are_hash_and_coverage_bound(self) -> None:
        contexts = [
            {
                "source_id": f"source:{index}",
                "sha256": str(index + 1) * 64,
                "path": f"/source/{index}.v",
                "remote_path": f"/remote/{index}.v",
                "text": "module source_%d;\n%s\nendmodule\n" % (index, "x" * 900),
                "text_encoding": "utf-8",
                "truncated": False,
            }
            for index in range(3)
        ]
        calls: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "board_interface"

            def runner(**kwargs: object) -> dict[str, object]:
                calls.append(kwargs)
                chunk = kwargs["inputs"]["chunk"]
                rows = chunk["source_contexts"]
                output = {
                    "schema_version": impl.DOMAIN_SOURCE_REVIEW_SCHEMA_VERSION,
                    "agent": kwargs["agent"],
                    "stage": kwargs["stage"],
                    "status": "pass",
                    "summary": "reviewed complete source chunk",
                    "reviewed_source_ids": chunk["assigned_source_ids"],
                    "reviewed_segment_ids": chunk["assigned_segment_ids"],
                    "source_summaries": [
                        {
                            "source_id": row["source_id"],
                            "segment_id": row["segment_id"],
                            "sha256": row["sha256"],
                            "segment_text_sha256": row["segment_text_sha256"],
                            "text_encoding": row["text_encoding"],
                            "start_line": row["start_line"],
                            "end_line": row["end_line"],
                            "start_byte": row["start_byte"],
                            "end_byte": row["end_byte"],
                            "declared_modules": [],
                            "semantic_roles": [],
                            "summary": "fully reviewed",
                            "findings": [],
                        }
                        for row in rows
                    ],
                    "cross_source_findings": [],
                    "blockers": [],
                }
                path = out_dir / "llm" / f"{kwargs['agent']}_result.json"
                record = {
                    "schema_version": "spatialaccagent.stage_worker_record.v0",
                    "agent": kwargs["agent"],
                    "used_fallback": False,
                    "error": None,
                    "result_path": str(path),
                    "output": output,
                }
                impl.write_json(path, record)
                return record

            whole_segments = impl._source_review_segments(contexts, 1_000_000)
            self.assertEqual(len(whole_segments), len(contexts))
            segment_sizes = [impl._compact_size(row) for row in whole_segments]
            budget = max(segment_sizes) + 4
            outputs, coverage, errors = impl.run_progressive_board_source_review(
                runner,
                out_dir,
                {"board": "current-user-sample"},
                {"selected_cell_id": "cell:selected"},
                contexts,
                map_budget_bytes=budget,
            )
            self.assertEqual(errors, [])
            self.assertGreaterEqual(len(outputs), 1)
            self.assertEqual(len(calls), len(outputs))
            self.assertTrue(Path(coverage["path"]).is_file())
            self.assertEqual(impl.sha256_file(Path(coverage["path"])), coverage["sha256"])
            reviewed = {
                source_id
                for output in outputs
                for source_id in output["reviewed_source_ids"]
            }
            self.assertEqual(reviewed, {row["source_id"] for row in contexts})

            def unexpected_runner(**kwargs: object) -> dict[str, object]:
                raise AssertionError(f"source-review LLM reran: {kwargs['agent']}")

            reused_outputs, reused_coverage, reused_errors = (
                impl.run_progressive_board_source_review(
                    unexpected_runner,
                    out_dir,
                    {"board": "current-user-sample"},
                    {"selected_cell_id": "cell:selected"},
                    contexts,
                    map_budget_bytes=segment_sizes[0] + segment_sizes[1] + 5,
                )
            )
            self.assertEqual(reused_errors, [])
            self.assertEqual(reused_outputs, outputs)
            self.assertEqual(reused_coverage, coverage)


class PolicyTests(unittest.TestCase):
    def test_fact_exporter_has_no_case_specific_compute_slot_or_host(self) -> None:
        text = impl.VIVADO_FACT_EXPORT_TCL.lower()
        for forbidden in ("cnn_core", "qwen", "opt_", "10.12.133.23", "/home/eda/"):
            self.assertNotIn(forbidden, text)

    def test_discovery_schema_stops_at_existing_slot_replacement_boundary(self) -> None:
        abi = impl.BOARD_INTERFACE_INTERPRETATION_SCHEMA["properties"]["compute_slot_abi"]
        required = set(abi["required"])
        self.assertIn("replacement_module_identity", required)
        self.assertIn("replacement_instance_boundary", required)
        self.assertNotIn("generated_accelerator_module", required)
        self.assertNotIn("generated_accelerator_instance_path", required)
        self.assertNotIn("generated_accelerator_source_id", required)
        selector_required = set(impl.BOARD_INTERFACE_SELECTION_SCHEMA["required"])
        self.assertNotIn("relevant_generated_source_ids", selector_required)

    def test_canonical_discovery_assembler_passes_shared_identity_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ideal_path, _, _, _ = exact_contract_case(root / "ideal")
            ideal = json.loads(ideal_path.read_text(encoding="utf-8"))
            closure = ideal["selected_simulation_source_closure"]["source_files"]
            sample_rows = []
            for row in closure:
                sample_rows.append(
                    {
                        **row,
                        "local_path": row["path"],
                        "remote_path": row["path"],
                        "hashes_match": True,
                        "compile_order": len(sample_rows),
                        "library": "work",
                        "file_type": "SystemVerilog",
                    }
                )
            abi = ideal["compute_slot_abi"]
            abi["selected_cell_id"] = "sample_project_facts"
            abi["replacement_boundary"] = {
                "source_module_evidence": [
                    {
                        "source_id": "sample_slot",
                        "declared_modules": [abi["slot_module"]],
                    }
                ]
            }
            facts = {
                "simulation": {
                    "source_files": sample_rows,
                    "recursive_dependency_scan_complete": True,
                    "unresolved_dependencies": [],
                    "duplicate_module_definitions": [],
                    "external_library_dependencies": [],
                },
                "objects": [
                    {
                        "object_id": "sample_project_facts",
                        "kind": "cell",
                        "path": abi["slot_instance_path"],
                        "properties": {},
                    },
                    *[
                        {
                            "object_id": row["port_id"],
                            "kind": "pin",
                            "path": row["name"],
                            "properties": {},
                        }
                        for row in abi["required_ports"]
                    ],
                ],
            }
            facts_path = root / "vivado_board_facts.json"
            impl.write_json(facts_path, facts)
            interpretation = {
                "output": {"schema_version": impl.INTERPRETATION_SCHEMA_VERSION},
                "wrapper_source_id": "wrapper",
                "wrapper_top_module": ideal["top_module"],
                "compute_slot_abi": abi,
                "timing_contract": ideal["timing_contract"],
                "axi_interfaces": ideal["axi_interfaces"],
                "profile_axi_data_width_bits": 512,
            }
            coverage_path = root / "exact_board_interface_selector_progressive_coverage.json"
            object_ids = [str(row["object_id"]) for row in facts["objects"]]
            source_ids = [str(row["source_id"]) for row in sample_rows]
            worker_path = root / "selector_map_000.json"
            impl.write_json(
                worker_path,
                {
                    "schema_version": "spatialaccagent.stage_worker_record.v0",
                    "agent": "exact_board_interface_selector_map_000_agent",
                    "output": {
                        "reviewed_object_ids": object_ids,
                        "reviewed_source_ids": source_ids,
                    },
                },
            )
            semantic_fingerprint = "b" * 64
            checkpoint_path = root / "selector_map_checkpoint.json"
            impl.write_json(
                checkpoint_path,
                {
                    "schema_version": impl.SELECTOR_MAP_CHECKPOINT_SCHEMA_VERSION,
                    "status": "pass",
                    "chunk_count": 1,
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "chunk_count": 1,
                            "agent": "exact_board_interface_selector_map_000_agent",
                            "semantic_fingerprint": semantic_fingerprint,
                            "record_file": worker_path.name,
                            "record_sha256": impl.sha256_file(worker_path),
                            "last_materialization_source": "exact_prompt",
                            "origin_exact_prompt_validated": True,
                        }
                    ],
                },
            )
            checkpoint_ref = {
                "path": str(checkpoint_path),
                "sha256": impl.sha256_file(checkpoint_path),
            }
            impl.write_json(
                coverage_path,
                {
                    "schema_version": "spatialaccagent.board_interface_selection_coverage.v1",
                    "status": "pass",
                    "input_vivado_fact_canonical_sha256": impl.canonical_sha256(facts),
                    "map_semantic_checkpoint": checkpoint_ref,
                    "complete_coverage": {
                        "reviewed_object_ids": object_ids,
                        "reviewed_source_ids": source_ids,
                        "reviewed_object_count": len(object_ids),
                        "reviewed_source_count": len(source_ids),
                        "reviewed_object_ids_sha256": impl.canonical_sha256(
                            sorted(object_ids)
                        ),
                        "reviewed_source_ids_sha256": impl.canonical_sha256(
                            sorted(source_ids)
                        ),
                        "all_fact_and_source_units_reviewed": True,
                    },
                    "worker_records": [
                        {
                            "phase": "map",
                            "agent": "exact_board_interface_selector_map_000_agent",
                            "chunk_index": 0,
                            "semantic_fingerprint": semantic_fingerprint,
                            "reuse_authority": {
                                "checkpoint_chunk_index": 0,
                                "checkpoint_semantic_fingerprint": semantic_fingerprint,
                                "materialization_source": "exact_prompt",
                            },
                            "path": str(worker_path),
                            "sha256": impl.sha256_file(worker_path),
                            "reviewed_object_count": len(object_ids),
                            "reviewed_source_count": len(source_ids),
                            "reviewed_object_ids_sha256": impl.canonical_sha256(
                                sorted(object_ids)
                            ),
                            "reviewed_source_ids_sha256": impl.canonical_sha256(
                                sorted(source_ids)
                            ),
                        }
                    ],
                },
            )
            coverage_ref = {
                "path": str(coverage_path),
                "sha256": impl.sha256_file(coverage_path),
            }
            canonical = impl._canonical_identity_contract(
                interpretation=interpretation,
                facts=facts,
                facts_path=facts_path,
                sample_rows=sample_rows,
                agent_record={
                    "agent": "exact_board_interface_domain_agent",
                    "model": "configured-model",
                    "used_fallback": False,
                    "prompt_hash": "a" * 64,
                    "selector_coverage_ledger": coverage_ref,
                    "selector_progressive_selection": {
                        "status": "pass",
                        "coverage_ledger": coverage_ref,
                    },
                },
            )
            self.assertEqual(
                canonical["discovery_provenance"]["progressive_selector_coverage"],
                coverage_ref,
            )
            identity_path = root / "board_source_identity.json"
            impl.write_json(
                identity_path,
                {
                    "schema_version": impl.IDENTITY_SCHEMA_VERSION,
                    "status": "pass",
                    "exact_user_sample_wrapper": True,
                    "vivado_facts_path": str(facts_path),
                    "vivado_facts_sha256": impl.sha256_file(facts_path),
                    **canonical,
                },
            )
            result = validate_exact_board_identity(identity_path)
            self.assertEqual(result["status"], "pass", result["blockers"])


if __name__ == "__main__":
    unittest.main()
