import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.board_acceptance_contract import (
    FROZEN_COMPUTE_SLOT_IDENTITY_ATTESTATION_SCHEMA_VERSION,
    FROZEN_COMPUTE_SLOT_IDENTITY_REQUIRED_CHECKS,
    REQUIRED_PROTOCOL_MONITOR_CHECKS,
    _authority_contains_token,
    _is_simulator_compile_input,
    _normalized_authority_shell_tokens,
    canonical_contract_sha256,
    compile_source_set_fingerprint,
    compute_slot_port_map_fingerprint,
    sha256_file,
    source_closure_fingerprint,
    validate_exact_board_acceptance,
    validate_exact_board_identity,
    validate_exact_board_preflight,
)
from accagent.framework.board_progress import (
    BOARD_DEBUG_OBSERVABILITY_SCHEMA_VERSION,
    BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
    REQUIRED_DEBUG_EVENT_KINDS,
    REQUIRED_DEBUG_SEMANTIC_ROLES,
    REQUIRED_PROGRESS_EVENT_FIELDS,
)
from accagent.framework.case_adapter import (
    EXACT_BOARD_ACCEPTANCE_CAPABILITIES,
    EXACT_BOARD_DISCOVERY_CAPABILITIES,
    normalize_user_adapter,
    qwen2_hf_case_adapter,
)
from accagent.framework.stage_repair_execute import (
    _materialize_external_fixture_preflight_selection,
    materialize_exact_board_preflight_manifest,
)
from scripts.verification.qwen_hierarchical_check import check_axi_ddr_interface


def _write(path: Path, text: str) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"path": str(path), "sha256": sha256_file(path)}


class ExactBoardSourceClassificationTest(TestCase):
    def test_headers_are_not_independent_simulator_source_tokens(self) -> None:
        self.assertTrue(
            _is_simulator_compile_input(
                {"path": "/sample/design.sv", "file_type": "SystemVerilog"}
            )
        )
        self.assertFalse(
            _is_simulator_compile_input(
                {"path": "/sample/defs.svh", "file_type": "SystemVerilog Header"}
            )
        )
        self.assertFalse(
            _is_simulator_compile_input(
                {"path": "/sample/controller.elf", "file_type": "ELF"}
            )
        )

    def test_hash_bound_quoted_include_is_authorized_after_shell_normalization(self) -> None:
        digest = "a" * 64
        context = (
            "vlogan -work xil_defaultlib \\\n"
            '  +incdir+"/sample/ip/include" source.sv\n'
        )
        normalized = {digest: _normalized_authority_shell_tokens(context)}

        self.assertTrue(
            _authority_contains_token(
                {digest: context},
                {digest},
                "+incdir+/sample/ip/include",
                normalized,
            )
        )
        self.assertFalse(
            _authority_contains_token(
                {digest: context},
                {digest},
                "+incdir+/unrelated/include",
                normalized,
            )
        )

    def test_fixture_materializer_adds_framework_required_global_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            fixture_dir = run_dir / "verification" / "board_interface"
            component = _write(fixture_dir / "component.sv", "module MemoryModel; endmodule\n")
            global_source = _write(fixture_dir / "glbl.v", "module glbl; endmodule\n")
            component_id = "fixture:component"
            global_id = "fixture:global"
            context = "vlogan component.sv glbl.v\n"
            context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
            source_rows = [
                {
                    "source_id": component_id,
                    **component,
                    "dependencies": [],
                    "declared_modules": ["MemoryModel"],
                },
                {
                    "source_id": global_id,
                    **global_source,
                    "dependencies": [],
                    "declared_modules": ["glbl"],
                    "invoked_by_compile": True,
                },
            ]
            compile_authority = {
                "status": "pass",
                "compile_sources": source_rows,
                "hdl_export_artifacts": [source_rows[1]],
                "export_contexts": [
                    {"text": context, "sha256": context_hash}
                ],
            }
            fixture = {
                "status": "pass",
                "blockers": [],
                "compile_authority": compile_authority,
            }
            fixture["contract_sha256"] = hashlib.sha256(
                json.dumps(
                    fixture,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("utf-8")
            ).hexdigest()
            fixture_path = fixture_dir / "external_simulation_fixture.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            blockers: list[str] = []

            reference, sources, _ = _materialize_external_fixture_preflight_selection(
                {
                    "external_simulation_fixture": {
                        "selected_source_ids": [component_id],
                        "model_instance": {
                            "source_id": component_id,
                            "module": "MemoryModel",
                        },
                    }
                },
                run_dir,
                blockers,
            )

            self.assertEqual(blockers, [])
            self.assertEqual(
                reference["selected_source_ids"], [component_id, global_id]
            )
            self.assertEqual(
                [row["source_id"] for row in sources], [component_id, global_id]
            )

    def test_compute_slot_axi_fixture_selection_is_not_required(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            blockers: list[str] = []
            plan = {
                "validation_mode": "compute_slot_axi",
                "external_simulation_fixture": {
                    "selected_source_ids": ["obsolete:fixture"]
                },
            }

            reference, sources, contexts = (
                _materialize_external_fixture_preflight_selection(
                    plan,
                    run_dir,
                    blockers,
                )
            )

            self.assertEqual(blockers, [])
            self.assertEqual(reference, {})
            self.assertEqual(sources, [])
            self.assertEqual(contexts, {})
            self.assertNotIn("external_simulation_fixture", plan)


def _axi_signal_map(prefix: str) -> dict:
    return {
        "aw": {
            "id": f"{prefix}_awid",
            "addr": f"{prefix}_awaddr",
            "len": f"{prefix}_awlen",
            "size": f"{prefix}_awsize",
            "burst": f"{prefix}_awburst",
            "lock": f"{prefix}_awlock",
            "cache": f"{prefix}_awcache",
            "prot": f"{prefix}_awprot",
            "qos": f"{prefix}_awqos",
            "region": f"{prefix}_awregion",
            "user": None,
            "valid": f"{prefix}_awvalid",
            "ready": f"{prefix}_awready",
        },
        "w": {
            "data": f"{prefix}_wdata",
            "strb": f"{prefix}_wstrb",
            "last": f"{prefix}_wlast",
            "user": None,
            "valid": f"{prefix}_wvalid",
            "ready": f"{prefix}_wready",
        },
        "b": {
            "id": f"{prefix}_bid",
            "resp": f"{prefix}_bresp",
            "user": None,
            "valid": f"{prefix}_bvalid",
            "ready": f"{prefix}_bready",
        },
        "ar": {
            "id": f"{prefix}_arid",
            "addr": f"{prefix}_araddr",
            "len": f"{prefix}_arlen",
            "size": f"{prefix}_arsize",
            "burst": f"{prefix}_arburst",
            "lock": f"{prefix}_arlock",
            "cache": f"{prefix}_arcache",
            "prot": f"{prefix}_arprot",
            "qos": f"{prefix}_arqos",
            "region": f"{prefix}_arregion",
            "user": None,
            "valid": f"{prefix}_arvalid",
            "ready": f"{prefix}_arready",
        },
        "r": {
            "id": f"{prefix}_rid",
            "data": f"{prefix}_rdata",
            "resp": f"{prefix}_rresp",
            "last": f"{prefix}_rlast",
            "user": None,
            "valid": f"{prefix}_rvalid",
            "ready": f"{prefix}_rready",
        },
    }


def _case(root: Path) -> tuple[Path, Path, dict, dict]:
    sources_dir = root / "sources"
    fact_bundle = _write(
        root / "sample_project_fact_bundle.json",
        json.dumps({"source": "user sample project", "facts": ["source closure", "slot ABI", "timing", "AXI"]}),
    )
    evidence_ref = ["sample_project_facts"]
    generated_evidence_ref = ["generated_control_facts"]
    source_specs = [
        ("wrapper", "wrapper", "module BoardTop; endmodule\n", ["bd"], ["BoardTop"]),
        ("bd", "bd_sim", "module BoardDesign; endmodule\n", ["memory_model", "sample_slot"], ["BoardDesign"]),
        ("memory_model", "ip_sim", "module ExactMemoryModel; endmodule\n", [], ["ExactMemoryModel"]),
        ("sample_slot", "sample_compute_slot", "module SlotShell; endmodule\n", [], ["SlotShell"]),
    ]
    closure = []
    for source_id, role, text, dependencies, modules in source_specs:
        artifact = _write(sources_dir / f"{source_id}.sv", text)
        closure.append(
            {
                "source_id": source_id,
                "role": role,
                **artifact,
                "dependencies": dependencies,
                "declared_modules": modules,
                "evidence_refs": evidence_ref,
            }
        )
    closure[-1]["closure_role"] = "compute_slot_implementation"

    debug_literals = sorted(
        {
            BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
            "evidence/progress_events.jsonl",
            *REQUIRED_DEBUG_EVENT_KINDS,
            *REQUIRED_PROGRESS_EVENT_FIELDS,
        }
    )
    debug_testbench_text = (
        "module BoardTestbench;\n"
        f'  string debug_abi = "{" ".join(debug_literals)}";\n'
        '  initial begin $display("progress %s", debug_abi); $fflush(1); end\n'
        "endmodule\n"
    )
    generated_specs = [
        ("slot_adapter", "compute_slot_adapter", "module SlotShell; endmodule\n", ["generated_harness"], ["SlotShell"]),
        ("generated_harness", "generated_accelerator", "module MultiHarness; endmodule\n", ["generated_kernel"], ["MultiHarness"]),
        ("generated_kernel", "generated_kernel", "module SingleKernel; endmodule\n", [], ["SingleKernel"]),
        ("board_testbench", "testbench", debug_testbench_text, ["wrapper"], ["BoardTestbench"]),
        ("axi_monitor", "protocol_monitor", "module AxiMonitor; endmodule\n", [], ["AxiMonitor"]),
    ]
    generated = []
    for source_id, role, text, dependencies, modules in generated_specs:
        artifact = _write(sources_dir / f"{source_id}.sv", text)
        generated.append(
            {
                "source_id": source_id,
                "role": role,
                **artifact,
                "dependencies": dependencies,
                "declared_modules": modules,
            }
        )

    fixture_source = {
        "source_id": "external-fixture-source",
        "role": "external_fixture_compile_source",
        **_write(
            sources_dir / "external_fixture_source.sv",
            "module OpaqueExternalComponent; endmodule\n",
        ),
        "dependencies": [],
        "declared_modules": ["OpaqueExternalComponent"],
        "provider_configuration_sha256": "4" * 64,
    }
    physical_bindings = [
        {
            "object_id": "physical:member0",
            "path": "/provider/physical/member0",
            "width_bits": 8,
            "direction": "inout",
            "sample_top_port": "sample_member0",
            "binding_role": "external_memory_component",
            "target_port": "fixture_member0",
        },
        {
            "object_id": "physical:member1",
            "path": "/provider/physical/member1",
            "width_bits": 1,
            "direction": "input",
            "sample_top_port": "sample_member1",
            "binding_role": "exact_timing_clock_driver",
            "timing_clock_name": "memory_ui_clock",
        },
    ]
    provider_groups = [
        {
            "configuration_sha256": "4" * 64,
            "representative": {
                "external_interfaces": [
                    {
                        "provider_member_pins": [
                            {
                                "object_id": "physical:member0",
                                "path": "/provider/physical/member0",
                                "properties": {"DIR": "IO", "LEFT": "7", "RIGHT": "0"},
                            },
                            {
                                "object_id": "physical:member1",
                                "path": "/provider/physical/member1",
                                "properties": {"DIR": "I"},
                            },
                        ]
                    }
                ]
            },
        }
    ]
    fixture_authority = {
        "schema_version": "test.external_fixture_authority.v1",
        "provider_groups": provider_groups,
    }
    fixture_authority["authority_sha256"] = canonical_contract_sha256(fixture_authority)
    fixture_export_text = "/tools/vlogan -work fixture_lib external_fixture_source.sv\n"
    fixture_export_artifact = _write(root / "external_fixture_export.sh", fixture_export_text)
    fixture_compile_authority = {
        "schema_version": "test.external_fixture_compile_authority.v1",
        "status": "pass",
        "compile_sources": [copy.deepcopy(fixture_source)],
        "export_contexts": [
            {
                **fixture_export_artifact,
                "remote_path": "/provider/export/compile.sh",
                "text": fixture_export_text,
            }
        ],
        "provider_groups_sha256": canonical_contract_sha256(provider_groups),
    }
    fixture_compile_authority["compile_authority_sha256"] = canonical_contract_sha256(
        fixture_compile_authority
    )
    fixture = {
        "schema_version": "test.external_simulation_fixture.v1",
        "status": "pass",
        "authority": fixture_authority,
        "authority_sha256": fixture_authority["authority_sha256"],
        "compile_authority": fixture_compile_authority,
        "blockers": [],
    }
    fixture["contract_sha256"] = canonical_contract_sha256(fixture)
    fixture_artifact = _write(
        root / "external_simulation_fixture.json", json.dumps(fixture)
    )
    model_instance = {
        "module": "OpaqueExternalComponent",
        "source_id": fixture_source["source_id"],
        "physical_port_bindings": copy.deepcopy(physical_bindings),
    }

    abi = {
        "status": "pass",
        "slot_module": "SlotShell",
        "slot_instance_path": "u_slot",
        "replacement_module_identity": "SlotShell",
        "replacement_instance_boundary": "u_slot",
        "replaced_source_ids": ["sample_slot"],
        "all_required_ports_bound": True,
        "no_behavioral_substitution": True,
        "evidence_refs": evidence_ref,
        "required_ports": [
            {"port_id": "clock", "name": "clock", "direction": "input", "width_bits": 1, "semantic_role": "clock", "evidence_refs": evidence_ref},
            {"port_id": "reset", "name": "reset_n", "direction": "input", "width_bits": 1, "semantic_role": "reset", "evidence_refs": evidence_ref},
        ],
        "port_bindings": [
            {"port_id": "clock", "accelerator_port": "clock", "direction": "input", "width_bits": 1, "evidence_refs": evidence_ref},
            {"port_id": "reset", "accelerator_port": "reset_n", "direction": "input", "width_bits": 1, "evidence_refs": evidence_ref},
        ],
        "control_abi": {
            "clock_domain": "memory_ui_clock",
            "evidence_refs": evidence_ref,
            "configuration_fields": [
                {
                    "field_id": "sequence_length",
                    "register": "configuration_0",
                    "width_bits": 16,
                    "bit_offset": 0,
                    "access": "rw",
                    "reset_value": 0,
                    "evidence_refs": evidence_ref,
                },
                {
                    "field_id": "layer_count",
                    "register": "configuration_0",
                    "width_bits": 8,
                    "bit_offset": 16,
                    "access": "rw",
                    "reset_value": 0,
                    "evidence_refs": evidence_ref,
                },
            ],
            "signals": {
                "start": {"name": "start", "direction": "input", "width_bits": 1, "semantic": "pulse", "clock_domain": "memory_ui_clock", "evidence_refs": evidence_ref},
                "clear": {"name": "clear", "direction": "input", "width_bits": 1, "semantic": "pulse", "clock_domain": "memory_ui_clock", "evidence_refs": evidence_ref},
                "valid": {"name": "valid", "direction": "output", "width_bits": 1, "semantic": "level", "clock_domain": "memory_ui_clock", "evidence_refs": evidence_ref},
                "done": {"name": "done", "direction": "output", "width_bits": 1, "semantic": "level", "clock_domain": "memory_ui_clock", "evidence_refs": evidence_ref},
                "count": {"name": "count", "direction": "output", "width_bits": 32, "semantic": "counter", "clock_domain": "memory_ui_clock", "evidence_refs": evidence_ref},
                "status": {"name": "status", "direction": "output", "width_bits": 4, "semantic": "status", "clock_domain": "memory_ui_clock", "evidence_refs": evidence_ref},
            },
            "timing": {
                "start_assertion_cycles": 1,
                "clear_assertion_cycles": 1,
                "start_sampling_edge": "rising",
                "clear_sampling_edge": "rising",
                "start_accept_condition": "idle_and_calibrated",
                "done_relation_to_valid": "done_after_final_valid_transfer",
                "done_clear_condition": "clear_sampled",
                "count_update_event": "accepted_output_transfer",
                "status_update_event": "state_transition",
                "evidence_refs": evidence_ref,
            },
        },
    }
    for name, direction, width, semantic in (
        ("start", "input", 1, "control_start"),
        ("clear", "input", 1, "control_clear"),
        ("valid", "output", 1, "control_valid"),
        ("done", "output", 1, "control_done"),
        ("count", "output", 32, "control_count"),
        ("status", "output", 4, "control_status"),
    ):
        abi["required_ports"].append(
            {
                "port_id": name,
                "name": name,
                "direction": direction,
                "width_bits": width,
                "semantic_role": semantic,
                "evidence_refs": evidence_ref,
            }
        )
        abi["port_bindings"].append(
            {
                "port_id": name,
                "accelerator_port": name,
                "direction": direction,
                "width_bits": width,
                "evidence_refs": evidence_ref,
            }
        )
    timing = {
        "exact_sample_timing": True,
        "timescale": "1ns",
        "timeprecision": "1ps",
        "clock_domains": [
            {
                "name": "memory_ui_clock",
                "period_ps": 4000,
                "phase_ps": 0,
                "duty_cycle_percent": 50,
                "source": "exact_sample_ip",
                "evidence_refs": evidence_ref,
            }
        ],
        "resets": [
            {
                "name": "memory_ui_reset_n",
                "active_level": 0,
                "clock_domain": "memory_ui_clock",
                "minimum_assert_cycles": 16,
                "deassertion_edge": "rising",
                "source": "exact_sample_ip",
                "evidence_refs": evidence_ref,
            }
        ],
        "calibration": [
            {
                "name": "memory_calibrated",
                "active_level": 1,
                "clock_domain": "memory_ui_clock",
                "gates_axi_traffic": True,
                "source": "exact_sample_memory_model",
                "evidence_refs": evidence_ref,
            }
        ],
        "startup_sequence": [
            {"order": 0, "event": "assert_reset", "evidence_refs": evidence_ref},
            {"order": 1, "event": "release_reset", "evidence_refs": evidence_ref},
            {"order": 2, "event": "wait_calibration", "evidence_refs": evidence_ref},
            {"order": 3, "event": "enable_axi_traffic", "evidence_refs": evidence_ref},
        ],
        "memory_timing_model": {
            "source_ids": ["memory_model"],
            "parameters_bound_from_sample_project": True,
            "synthetic_fixed_latency": False,
            "evidence_refs": evidence_ref,
        },
    }
    axi = {
        "name": "memory_port",
        "protocol": "AXI4",
        "role": "master",
        "clock": "memory_ui_clock",
        "reset": "memory_ui_reset_n",
        "calibration": "memory_calibrated",
        "address_width_bits": 48,
        "data_width_bits": 64,
        "id_width_bits": 4,
        "strb_width_bits": 8,
        "len_width_bits": 8,
        "size_width_bits": 3,
        "burst_width_bits": 2,
        "lock_width_bits": 1,
        "cache_width_bits": 4,
        "prot_width_bits": 3,
        "qos_width_bits": 4,
        "region_width_bits": 4,
        "awuser_width_bits": 0,
        "wuser_width_bits": 0,
        "buser_width_bits": 0,
        "aruser_width_bits": 0,
        "ruser_width_bits": 0,
        "max_burst_length": 256,
        "supports_narrow_bursts": True,
        "supports_unaligned_access": False,
        "read_outstanding_limit": 8,
        "write_outstanding_limit": 8,
        "byte_order": "little",
        "signal_map": _axi_signal_map("mem"),
    }
    axi["evidence_refs"] = evidence_ref
    axi["parameter_evidence_refs"] = {
        field: evidence_ref
        for field in {
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
            "supports_unaligned_access",
            "read_outstanding_limit",
            "write_outstanding_limit",
            "byte_order",
        }
    }
    axi["signal_evidence_refs"] = {
        channel: {signal: evidence_ref for signal in signals}
        for channel, signals in _axi_signal_map("mem").items()
    }
    identity = {
        "schema_version": "test.exact_board_identity.v1",
        "status": "pass",
        "exact_user_sample_wrapper": True,
        "top_module": "BoardTop",
        "discovery_provenance": {
            "mode": "llm",
            "agent_id": "board_discovery_agent",
            "model": "test-llm",
            "used_fallback": False,
            "input_fact_bundle": fact_bundle,
        },
        "evidence_records": [
            {
                "evidence_id": "sample_project_facts",
                "source_kind": "vivado_block_design",
                "source_path": fact_bundle["path"],
                "sha256": fact_bundle["sha256"],
                "locator": {"kind": "structured_fact_bundle", "value": "facts"},
                "fact_kind": "sample_project_interface_and_timing",
                "observed_value": "structured",
            }
        ],
        "selected_simulation_source_closure": {
            "source_files": closure,
            "root_source_ids": ["wrapper"],
            "recursive_dependency_scan_complete": True,
            "unresolved_dependencies": [],
            "duplicate_module_definitions": [],
            "external_library_dependencies": [],
        },
        "compute_slot_abi": abi,
        "timing_contract": timing,
        "axi_interfaces": [axi],
    }
    identity["selected_simulation_source_closure_sha256"] = source_closure_fingerprint(closure)
    identity["compute_slot_abi_sha256"] = canonical_contract_sha256(abi)
    identity["timing_contract_sha256"] = canonical_contract_sha256(timing)
    identity["axi_interfaces_sha256"] = canonical_contract_sha256([axi])
    identity_path = root / "identity.json"
    identity_path.write_text(json.dumps(identity), encoding="utf-8")

    log = _write(root / "elaboration.log", "real elaboration completed\n")
    certificate = _write(
        root / "single_layer_promotion_certificate.json",
        json.dumps({"schema_version": "test.single_layer_certificate.v1", "status": "pass"}),
    )
    compile_hash = compile_source_set_fingerprint(closure)
    slot_adapter_source = next(row for row in generated if row["source_id"] == "slot_adapter")
    harness_source = next(row for row in generated if row["source_id"] == "generated_harness")
    kernel_source = next(row for row in generated if row["source_id"] == "generated_kernel")
    testbench_source = next(row for row in generated if row["source_id"] == "board_testbench")
    monitor_source = next(row for row in generated if row["source_id"] == "axi_monitor")
    harness_sources = [slot_adapter_source, harness_source, kernel_source]
    preserved_sources = [row for row in closure if row["source_id"] != "sample_slot"]
    compile_sources = [*preserved_sources, fixture_source, *generated]
    compile_hash = compile_source_set_fingerprint(compile_sources)
    simulation = {
        "schema_version": "test.board_simulation.v1",
        "status": "pass",
        "exact_sample_wrapper_unmodified": True,
        "source_identity_sha256": sha256_file(identity_path),
        "source_files": copy.deepcopy(compile_sources),
        "compile_source_ids": [row["source_id"] for row in compile_sources],
        "compiled_sample_source_ids": [row["source_id"] for row in preserved_sources],
        "replaced_sample_source_ids": ["sample_slot"],
        "generated_source_ids": [row["source_id"] for row in generated],
        "external_simulation_fixture": {
            **fixture_artifact,
            "contract_sha256": fixture["contract_sha256"],
            "selected_source_ids": [fixture_source["source_id"]],
            "model_instance": copy.deepcopy(model_instance),
        },
        "source_replacements": [
            {
                "replaced_source_id": "sample_slot",
                "generated_source_id": "slot_adapter",
                "replaced_module": "SlotShell",
                "generated_module": "SlotShell",
                "compute_slot_abi_sha256": identity["compute_slot_abi_sha256"],
            }
        ],
        "synthesis_sources_excluded": True,
        "source_closure_sha256": identity["selected_simulation_source_closure_sha256"],
        "compile_source_set_sha256": compile_hash,
        "compute_slot_abi_sha256": identity["compute_slot_abi_sha256"],
        "timing_contract_sha256": identity["timing_contract_sha256"],
        "axi_interfaces_sha256": identity["axi_interfaces_sha256"],
        "multilayer_harness": {
            "source_files": copy.deepcopy(harness_sources),
            "source_set_sha256": compile_source_set_fingerprint(harness_sources),
            "top_module": "MultiHarness",
            "instance_path": "u_slot.u_accel",
            "verified_single_layer_top_module": "SingleKernel",
            "certified_kernel_source_ids": ["generated_kernel"],
            "instantiated_kernel_count": 1,
            "target_layer_count": 7,
            "single_layer_promotion_certificate": certificate,
        },
        "all_target_layers": True,
        "target_layer_count": 7,
        "bound_layer_count": 7,
        "board_consumed_tensor_hashes": ["1" * 64, "2" * 64],
        "board_integration_contract": {
            "status": "pass",
            "source_closure_sha256": identity["selected_simulation_source_closure_sha256"],
            "compute_slot_abi_sha256": identity["compute_slot_abi_sha256"],
            "timing_contract_sha256": identity["timing_contract_sha256"],
            "scheduler": {"enabled": True, "all_target_layers": True, "layer_count": 7, "evidence_refs": generated_evidence_ref},
            "double_weight_buffer": {"enabled": True, "bank_count": 2, "atomic_layer_switch": True, "evidence_refs": generated_evidence_ref},
            "activation_ping_pong": {"enabled": True, "bank_count": 2, "inter_layer_chaining": True, "evidence_refs": generated_evidence_ref},
            "background_prefetch": {
                "enabled": True,
                "overlaps_current_layer_compute": True,
                "prefetch_scope": "next_layer_weights",
                "evidence_refs": generated_evidence_ref,
            },
            "final_writeback": {"enabled": True, "only_after_last_layer": True, "axi_interface": "memory_port", "evidence_refs": generated_evidence_ref},
            "intra_layer_spatial_pipeline": {
                "preserved": True,
                "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
                "different_tokens_overlap_across_required_dataflow": True,
                "heterogeneous_stage_latency_supported": True,
                "stage_turnover_gaps_are_diagnostic": True,
                "all_stages_same_cycle_concurrency_required": False,
                "serial_leaf_execution": False,
                "evidence_refs": generated_evidence_ref,
            },
        },
        "elaborated_hierarchy": {
            "schema_version": "test.elaborated_hierarchy.v1",
            "evidence_refs": ["elaboration_evidence"],
            "status": "pass",
            "elaboration_tool": "real_simulator",
            "elaboration_exit_code": 0,
            "source_closure_sha256": identity["selected_simulation_source_closure_sha256"],
            "compile_source_set_sha256": compile_hash,
            "compute_slot_abi_sha256": identity["compute_slot_abi_sha256"],
            "elaboration_log": log,
            "instances": [
                {
                    "instance_path": "board_tb.u_board",
                    "module": "BoardTop",
                    "source_sha256": closure[0]["sha256"],
                    "binding_role": "exact_sample_top",
                },
                {
                    "instance_path": "board_tb.u_board.u_slot",
                    "module": "SlotShell",
                    "source_sha256": slot_adapter_source["sha256"],
                    "binding_role": "compute_slot",
                },
                {
                    "instance_path": "board_tb.u_board.u_slot.u_accel",
                    "module": "MultiHarness",
                    "source_sha256": harness_source["sha256"],
                    "binding_roles": ["generated_accelerator", "multilayer_harness"],
                },
                {
                    "instance_path": "board_tb.u_board.u_slot.u_accel.u_kernel",
                    "module": "SingleKernel",
                    "source_sha256": kernel_source["sha256"],
                    "binding_role": "verified_single_layer_kernel",
                },
                {
                    "instance_path": "board_tb.u_external_fixture",
                    "module": model_instance["module"],
                    "source_id": model_instance["source_id"],
                    "source_sha256": fixture_source["sha256"],
                    "physical_port_bindings": copy.deepcopy(physical_bindings),
                    "calibration_forced": False,
                    "binding_role": "external_memory_component",
                },
            ],
            "compute_slot_binding": {
                "exact_sample_top_instance_path": "board_tb.u_board",
                "compute_slot_instance_path": "board_tb.u_board.u_slot",
                "generated_accelerator_instance_path": "board_tb.u_board.u_slot.u_accel",
                "all_required_ports_bound": True,
                "no_stub_or_behavioral_substitution": True,
                "port_map_sha256": compute_slot_port_map_fingerprint(abi),
            },
            "unresolved_modules": [],
            "blackboxes": [],
        },
        "protocol_monitor_contract": {
            "status": "ready",
            "axi_interfaces_sha256": identity["axi_interfaces_sha256"],
            "all_axi_interfaces_covered": True,
            "monitors": [
                {
                    "monitor_id": "memory_port_monitor",
                    "interface": "memory_port",
                    "bound_instance_path": "board_tb.u_board.u_slot.u_accel",
                    "channels": ["AW", "W", "B", "AR", "R"],
                    "fatal_on_violation": True,
                    "source_files": [copy.deepcopy(monitor_source)],
                    "checks": [
                        {"kind": kind, "enabled": True, "severity": "fatal"}
                        for kind in sorted(REQUIRED_PROTOCOL_MONITOR_CHECKS)
                    ],
                    "structured_report": {
                        "path": "evidence/memory_port_protocol.json",
                        "schema_version": "test.protocol.v1",
                        "required_fields": ["status", "violations", "transaction_counts"],
                    },
                }
            ],
        },
        "testbench": {
            **copy.deepcopy(testbench_source),
            "top_module": "BoardTestbench",
            "exact_sample_top_module": "BoardTop",
            "uses_memory_model_source_ids": ["memory_model"],
            "timing_contract_sha256": identity["timing_contract_sha256"],
            "compute_slot_abi_sha256": identity["compute_slot_abi_sha256"],
            "control_abi_sha256": canonical_contract_sha256(abi["control_abi"]),
            "force_calibration": False,
            "synthetic_memory_latency": False,
            "behavioral_ddr_substitute": False,
            "external_simulation_fixture_contract_sha256": fixture["contract_sha256"],
            "external_memory_component": copy.deepcopy(model_instance),
            "evidence_refs": ["generated_testbench_facts"],
            "debug_observability_contract": {
                "schema_version": BOARD_DEBUG_OBSERVABILITY_SCHEMA_VERSION,
                "status": "ready",
                "format": "jsonl",
                "implementation": "testbench_only",
                "synthesis_impact": "none",
                "observational_only": True,
                "drives_dut_signals": False,
                "new_synthesizable_ports_or_state": False,
                "flush_after_each_event": True,
                "heartbeat_is_semantic_progress": False,
                "fixed_wall_clock_timeout": False,
                "fixed_cycle_timeout": False,
                "bounded_deep_trace": True,
                "required_event_kinds": sorted(REQUIRED_DEBUG_EVENT_KINDS),
                "required_event_fields": sorted(REQUIRED_PROGRESS_EVENT_FIELDS),
                "progress_event_log": {
                    "path": "evidence/progress_events.jsonl",
                    "schema_version": BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
                },
                "probes": [
                    {
                        "probe_id": f"probe.{role}",
                        "semantic_role": role,
                        "source_id": "board_testbench",
                        "source_sha256": testbench_source["sha256"],
                        "instance_path": "board_tb.u_board.u_slot.u_accel",
                        "observed_fields": ["valid", "ready", "state"],
                        "read_only": True,
                    }
                    for role in sorted(REQUIRED_DEBUG_SEMANTIC_ROLES)
                ],
            },
            "forbidden_construct_scan": {
                "status": "planned",
                "required": False,
                "producer": "existing_simulator_compile",
                "method": "simulator_elaboration",
                "source_sha256": testbench_source["sha256"],
            },
        },
        "top_module": "BoardTestbench",
        "generated_evidence_records": [
            {
                "evidence_id": "generated_control_facts",
                "source_id": "generated_harness",
                "source_sha256": harness_source["sha256"],
                "locator": {"kind": "rtl_hierarchy", "value": "MultiHarness"},
                "fact_kind": "scheduler_buffers_prefetch_writeback_and_spatial_pipeline",
                "observed_value": "present",
            },
            {
                "evidence_id": "generated_testbench_facts",
                "source_id": "board_testbench",
                "source_sha256": testbench_source["sha256"],
                "locator": {"kind": "hdl_ast", "value": "BoardTestbench"},
                "fact_kind": "exact_sample_top_memory_timing_and_control_binding",
                "observed_value": "present_without_behavioral_memory_substitute",
            },
        ],
    }
    simulation["protocol_monitor_contract_sha256"] = canonical_contract_sha256(
        simulation["protocol_monitor_contract"]
    )
    simulation["board_integration_contract_sha256"] = canonical_contract_sha256(
        simulation["board_integration_contract"]
    )
    simulation["execution_outputs"] = {
        "compile_log": {"path": "logs/compile.log"},
        "simulation_log": {"path": "logs/simulation.log"},
        "progress_event_log": {
            "path": "evidence/progress_events.jsonl",
            "schema_version": BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
        },
        "elaborated_hierarchy_report": {
            "path": "evidence/elaborated_hierarchy.json",
            "schema_version": "test.elaborated_hierarchy.v1",
        },
        "pipeline_overlap_report": {
            "path": "evidence/pipeline_overlap.json",
            "schema_version": "test.pipeline_overlap.v1",
        },
        "protocol_monitor_reports": [
            {
                "interface": "memory_port",
                "path": "evidence/memory_port_protocol.json",
                "schema_version": "test.protocol.v1",
            }
        ],
    }
    hierarchy_report = _write(
        root / "executed" / "elaborated_hierarchy.json",
        json.dumps(simulation["elaborated_hierarchy"]),
    )
    compile_log = _write(root / "executed" / "compile.log", "compile exit 0\n")
    simulation_log = _write(root / "executed" / "simulation.log", "PASS\n")
    counts = {"aw": 4, "w": 8, "b": 4, "ar": 8, "r": 16}
    protocol_report = _write(
        root / "executed" / "memory_port_protocol.json",
        json.dumps(
            {
                "schema_version": "test.protocol.v1",
                "status": "pass",
                "violations": [],
                "transaction_counts": counts,
            }
        ),
    )
    overlap_report = _write(
        root / "executed" / "pipeline_overlap.json",
        json.dumps(
            {
                "schema_version": "test.pipeline_overlap.v1",
                "status": "pass",
                "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
                "required_dependency_overlap_complete": True,
                "all_planned_stages_participate_in_required_overlap": True,
                "token_order_preserved": True,
                "serial_leaf_execution_observed": False,
                "observed_different_token_overlap_count": 6,
                "stage_turnover_gaps_are_diagnostic": True,
                "all_stages_same_cycle_concurrency_required": False,
                "diagnostic_maximum_concurrent_stage_count": 3,
                "all_spatial_stages_concurrent_observed": False,
                "whole_sequence_barrier_observed": False,
                "expected_stage_count": 4,
                "observed_stage_count": 4,
            }
        ),
    )
    simulation["execution_evidence"] = {
        "status": "pass",
        "tool": "real_simulator",
        "tool_version": "test-version",
        "job_id": "job-1",
        "command_sha256": "3" * 64,
        "source_identity_sha256": sha256_file(identity_path),
        "source_closure_sha256": identity["selected_simulation_source_closure_sha256"],
        "compile_source_set_sha256": compile_hash,
        "compute_slot_abi_sha256": identity["compute_slot_abi_sha256"],
        "timing_contract_sha256": identity["timing_contract_sha256"],
        "axi_interfaces_sha256": identity["axi_interfaces_sha256"],
        "compile": {
            "exit_code": 0,
            "log": {
                **compile_log,
                "relative_path": "logs/compile.log",
                "evidence_refs": ["compile_log_evidence"],
            },
        },
        "simulation": {
            "exit_code": 0,
            "completed": True,
            "pass_marker_seen": True,
            "log": {
                **simulation_log,
                "relative_path": "logs/simulation.log",
                "evidence_refs": ["simulation_log_evidence"],
            },
        },
        "elaborated_hierarchy_report": {
            **hierarchy_report,
            "relative_path": "evidence/elaborated_hierarchy.json",
            "schema_version": "test.elaborated_hierarchy.v1",
            "evidence_refs": ["elaboration_evidence"],
        },
    }
    simulation["protocol_monitor_results"] = {
        "status": "pass",
        "all_axi_interfaces_covered": True,
        "protocol_monitor_contract_sha256": simulation["protocol_monitor_contract_sha256"],
        "interfaces": [
            {
                "interface": "memory_port",
                "status": "pass",
                "violations": [],
                "transaction_counts": counts,
                "evidence_refs": ["protocol_evidence"],
                "structured_report": {
                    **protocol_report,
                    "relative_path": "evidence/memory_port_protocol.json",
                },
            }
        ],
    }
    simulation["pipeline_overlap_results"] = {
        "status": "pass",
        "board_integration_contract_sha256": simulation["board_integration_contract_sha256"],
        "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
        "required_dependency_overlap_complete": True,
        "all_planned_stages_participate_in_required_overlap": True,
        "token_order_preserved": True,
        "serial_leaf_execution_observed": False,
        "observed_different_token_overlap_count": 6,
        "stage_turnover_gaps_are_diagnostic": True,
        "all_stages_same_cycle_concurrency_required": False,
        "diagnostic_maximum_concurrent_stage_count": 3,
        "all_spatial_stages_concurrent_observed": False,
        "whole_sequence_barrier_observed": False,
        "expected_stage_count": 4,
        "observed_stage_count": 4,
        "evidence_refs": ["pipeline_overlap_evidence"],
        "structured_trace_report": {
            **overlap_report,
            "relative_path": "evidence/pipeline_overlap.json",
        },
    }
    simulation["dynamic_evidence_records"] = [
        {
            "evidence_id": "compile_log_evidence",
            "evidence_kind": "compile_log",
            "schema_version": "test.compile_log.v1",
            **compile_log,
        },
        {
            "evidence_id": "simulation_log_evidence",
            "evidence_kind": "simulation_log",
            "schema_version": "test.simulation_log.v1",
            **simulation_log,
        },
        {
            "evidence_id": "elaboration_evidence",
            "evidence_kind": "elaborated_hierarchy",
            "schema_version": "test.elaborated_hierarchy.v1",
            **hierarchy_report,
        },
        {
            "evidence_id": "protocol_evidence",
            "evidence_kind": "protocol_monitor_report",
            "schema_version": "test.protocol.v1",
            **protocol_report,
        },
        {
            "evidence_id": "pipeline_overlap_evidence",
            "evidence_kind": "pipeline_overlap_report",
            "schema_version": "test.pipeline_overlap.v1",
            **overlap_report,
        },
    ]

    export_text = (
        "/tools/vlogan -work xil_defaultlib source.sv\n"
        "/tools/vcs -top BoardTestbench -o simv\n"
    )
    export_artifact = _write(root / "vivado_export_commands.sh", export_text)
    export_context_sha256 = export_artifact["sha256"]
    facts = {
        "schema_version": "test.vivado_facts.v1",
        "status": "pass",
        "simulation": {
            "simulator_export_contexts": [
                {
                    "remote_path": "/sample/export/compile.sh",
                    "sha256": export_context_sha256,
                    "text": export_text,
                }
            ]
        },
    }
    facts_path = root / "vivado_structured_facts.json"
    facts_path.write_text(json.dumps(facts), encoding="utf-8")
    identity["vivado_facts_path"] = str(facts_path)
    identity["vivado_facts_sha256"] = sha256_file(facts_path)
    identity_path.write_text(json.dumps(identity), encoding="utf-8")

    tool_profile = {
        "schema_version": "test.tool_profile.v1",
        "tools": [
            {
                "role": "functional_verification",
                "name": "vcs",
                "host": "vcs.test",
                "port": 22,
                "executable": "/tools/vcs",
            }
        ],
    }
    tool_profile_path = root / "input" / "tool_profile.json"
    tool_profile_path.parent.mkdir(parents=True, exist_ok=True)
    tool_profile_path.write_text(json.dumps(tool_profile), encoding="utf-8")
    commands = [
        {
            "order": index,
            "phase": "compile",
            "tool_role": "functional_verification",
            "executable": "/tools/vlogan",
            "argv": ["-work", "xil_defaultlib", {"source_id": source_id}],
            "source_ids": [source_id],
            "cwd": "stage",
            "env": {},
            "shell": False,
            "authority_refs": (
                [fixture_export_artifact["sha256"]]
                if source_id == fixture_source["source_id"]
                else [export_context_sha256]
            ),
        }
        for index, source_id in enumerate(simulation["compile_source_ids"])
    ]
    commands.append(
        {
            "order": len(commands),
            "phase": "elaborate",
            "tool_role": "functional_verification",
            "executable": "/tools/vcs",
            "argv": ["-top", "BoardTestbench", "-o", "simv"],
            "source_ids": [],
            "cwd": "stage",
            "env": {},
            "shell": False,
            "authority_refs": [export_context_sha256],
        }
    )
    compile_plan = {
        "schema_version": "spatialaccagent.vcs_compile_plan.v1",
        "status": "ready",
        "compile_authority": {
            "vivado_facts_path": str(facts_path),
            "vivado_facts_sha256": identity["vivado_facts_sha256"],
            "simulator_export_context_sha256s": [export_context_sha256],
            "external_fixture_contract_sha256": fixture["contract_sha256"],
            "external_fixture_export_context_sha256s": [
                fixture_export_artifact["sha256"]
            ],
        },
        "tool_binding": tool_profile["tools"][0],
        "tool_profile_sha256": sha256_file(tool_profile_path),
        "top_module": "BoardTestbench",
        "output": "simv",
        "ordered_commands": commands,
    }
    simulation["vcs_compile_plan"] = compile_plan
    simulation["vcs_compile_plan_sha256"] = canonical_contract_sha256(compile_plan)
    current_identity_sha256 = sha256_file(identity_path)
    simulation["source_identity_sha256"] = current_identity_sha256
    simulation["execution_evidence"]["source_identity_sha256"] = current_identity_sha256
    simulation_path = root / "simulation.json"
    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
    return identity_path, simulation_path, identity, simulation


def _convert_case_to_compute_slot_axi(
    identity_path: Path,
    simulation_path: Path,
    identity: dict,
    simulation: dict,
    *,
    keep_optional_fixture_reference: bool = False,
) -> dict:
    simulation["validation_mode"] = "compute_slot_axi"
    generated_ids = list(simulation["generated_source_ids"])
    source_by_id = {
        row["source_id"]: copy.deepcopy(row) for row in simulation["source_files"]
    }
    source_by_id["board_testbench"]["dependencies"] = ["slot_adapter"]
    simulation["source_files"] = [source_by_id[source_id] for source_id in generated_ids]
    simulation["compile_source_ids"] = generated_ids
    simulation["compiled_sample_source_ids"] = []
    simulation["testbench"]["dependencies"] = ["slot_adapter"]
    simulation["testbench"].pop("exact_sample_top_module", None)
    simulation["testbench"]["uses_memory_model_source_ids"] = []
    simulation["testbench"].pop("external_simulation_fixture_contract_sha256", None)
    simulation["testbench"].pop("external_memory_component", None)
    simulation["testbench"]["axi_transaction_memory_model"] = {
        "status": "pass",
        "contract_driven": True,
        "boundary": "compute_slot_axi",
        "axi_interfaces_sha256": identity["axi_interfaces_sha256"],
        "timing_contract_sha256": identity["timing_contract_sha256"],
        "replaces_compute_slot_rtl": False,
    }
    if not keep_optional_fixture_reference:
        simulation.pop("external_simulation_fixture", None)

    hierarchy = simulation["elaborated_hierarchy"]
    hierarchy["instances"] = [
        row
        for row in hierarchy["instances"]
        if row.get("binding_role")
        not in {"exact_sample_top", "external_memory_component"}
    ]
    for row in hierarchy["instances"]:
        row["instance_path"] = row["instance_path"].replace(
            "board_tb.u_board.u_slot", "board_tb.u_slot"
        )
    binding = hierarchy["compute_slot_binding"]
    binding.pop("exact_sample_top_instance_path", None)
    binding["testbench_instance_path"] = "board_tb"
    binding["compute_slot_instance_path"] = "board_tb.u_slot"
    binding["generated_accelerator_instance_path"] = "board_tb.u_slot.u_accel"
    simulation["protocol_monitor_contract"]["monitors"][0][
        "bound_instance_path"
    ] = "board_tb.u_slot.u_accel"
    simulation["protocol_monitor_contract_sha256"] = canonical_contract_sha256(
        simulation["protocol_monitor_contract"]
    )
    simulation["protocol_monitor_results"][
        "protocol_monitor_contract_sha256"
    ] = simulation["protocol_monitor_contract_sha256"]

    compile_hash = compile_source_set_fingerprint(simulation["source_files"])
    simulation["compile_source_set_sha256"] = compile_hash
    hierarchy["compile_source_set_sha256"] = compile_hash
    simulation["execution_evidence"]["compile_source_set_sha256"] = compile_hash

    plan = simulation["vcs_compile_plan"]
    authority = plan["compile_authority"]
    authority.pop("external_fixture_contract_sha256", None)
    authority.pop("external_fixture_export_context_sha256s", None)
    authority_ref = authority["simulator_export_context_sha256s"][0]
    commands = []
    for source_id in generated_ids:
        commands.append(
            {
                "order": len(commands),
                "phase": "compile",
                "tool_role": "functional_verification",
                "executable": "/tools/vlogan",
                "argv": ["-work", "xil_defaultlib", {"source_id": source_id}],
                "source_ids": [source_id],
                "cwd": "stage",
                "env": {},
                "shell": False,
                "authority_refs": [authority_ref],
            }
        )
    commands.append(
        {
            "order": len(commands),
            "phase": "elaborate",
            "tool_role": "functional_verification",
            "executable": "/tools/vcs",
            "argv": ["-top", "BoardTestbench", "-o", "simv"],
            "source_ids": [],
            "cwd": "stage",
            "env": {},
            "shell": False,
            "authority_refs": [authority_ref],
        }
    )
    plan["ordered_commands"] = commands
    simulation["vcs_compile_plan_sha256"] = canonical_contract_sha256(plan)

    hierarchy_report = simulation["execution_evidence"]["elaborated_hierarchy_report"]
    hierarchy_path = Path(hierarchy_report["path"])
    hierarchy_path.write_text(json.dumps(hierarchy), encoding="utf-8")
    hierarchy_sha256 = sha256_file(hierarchy_path)
    hierarchy_report["sha256"] = hierarchy_sha256
    for row in simulation["dynamic_evidence_records"]:
        if row.get("evidence_id") == "elaboration_evidence":
            row["sha256"] = hierarchy_sha256

    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
    return simulation


def _install_frozen_compute_slot_attestation(
    identity_path: Path,
    simulation_path: Path,
    identity: dict,
    simulation: dict,
) -> tuple[Path, dict]:
    prior = copy.deepcopy(simulation)
    prior["status"] = "fail"
    prior.pop("external_simulation_fixture", None)
    identity_sha256 = sha256_file(identity_path)
    plan = prior["vcs_compile_plan"]
    plan_sha256 = canonical_contract_sha256(plan)
    prior["vcs_compile_plan_sha256"] = plan_sha256
    execution = prior["execution_evidence"]
    execution.update(
        {
            "tool": "vcs",
            "tool_version": "test-vcs",
            "command_sha256": "c" * 64,
            "source_identity_sha256": identity_sha256,
            "source_closure_sha256": prior["source_closure_sha256"],
            "compute_slot_abi_sha256": prior["compute_slot_abi_sha256"],
            "timing_contract_sha256": prior["timing_contract_sha256"],
            "axi_interfaces_sha256": prior["axi_interfaces_sha256"],
            "vcs_compile_plan_sha256": plan_sha256,
            "compile": {"exit_code": 1},
        }
    )
    prior_preflight = validate_exact_board_preflight(identity_path, simulation_path)
    if prior_preflight["status"] != "pass":
        raise AssertionError(prior_preflight["blockers"])

    certificate_dir = identity_path.parent / "certificates"
    certificate_dir.mkdir(parents=True, exist_ok=True)
    projection_sha256 = "d" * 64
    remote_stage_root = "/tmp/spatialaccagent_test"
    job = {
        "schema_version": "spatialaccagent.board_remote_job_identity.v1",
        "compile_command": "vlogan sources; vcs -o simv BoardTestbench",
        "compile_source_set_sha256": prior["compile_source_set_sha256"],
        "execution_outputs": prior["execution_outputs"],
        "payload": [],
        "preflight_manifest_projection_sha256": projection_sha256,
        "remote_stage_root": remote_stage_root,
        "simulate_command": "./simv",
        "source_closure_sha256": prior["source_closure_sha256"],
        "source_identity_sha256": identity_sha256,
        "tool_profile": plan["tool_binding"],
        "top_module": prior["top_module"],
        "vcs_compile_plan": copy.deepcopy(plan),
        "vcs_compile_plan_sha256": plan_sha256,
        "verified_compile_source_ids": sorted(prior["compile_source_ids"]),
    }
    fingerprint = canonical_contract_sha256(job)
    remote_workdir = (
        f"{remote_stage_root}/{fingerprint[:12]}_{int(fingerprint[12:], 16)}"
    )
    job["input_fingerprint_sha256"] = fingerprint
    job["remote_workdir"] = remote_workdir
    execution["job_id"] = remote_workdir

    job_path = certificate_dir / "job.json"
    job_path.write_text(json.dumps(job), encoding="utf-8")
    prior_path = certificate_dir / "prior.json"
    prior_path.write_text(json.dumps(prior), encoding="utf-8")
    runner_path = Path(__file__).resolve().parents[1] / "scripts" / "verification" / "case_board_vcs_functional.py"
    runner = {
        "status": "fail",
        "phase": "remote_vcs",
        "validation_mode": "compute_slot_axi",
        "exact_board_preflight_passed": True,
        "exact_board_preflight": prior_preflight,
        "vcs_compile_plan_sha256": plan_sha256,
        "input_fingerprint_sha256": fingerprint,
        "runner_implementation_sha256": sha256_file(runner_path),
        "preflight_manifest_projection_sha256": projection_sha256,
        "remote_workdir": remote_workdir,
        "remote_job_recovery_contract": {
            "status": "pass",
            "job_contract_sha256": sha256_file(job_path),
        },
        "compile": {
            "status": "fail",
            "returncode": 1,
            "remote_state": "done",
            "transport": "detached_remote_job_with_short_ssh_polling",
            "remote_command": job["compile_command"],
            "launch": {
                "status": "pass",
                "returncode": 0,
                "stdout_tail": "SPATIALACC_REMOTE_JOB_STARTED pid=1\n",
            },
        },
    }
    runner_path_snapshot = certificate_dir / "runner.json"
    runner_path_snapshot.write_text(json.dumps(runner), encoding="utf-8")

    facts_path = Path(identity["vivado_facts_path"])
    replacement_text = "/tools/vlogan changed.sv\n/tools/vcs -top BoardTestbench -o simv\n"
    replacement_context_sha256 = hashlib.sha256(
        replacement_text.encode("utf-8")
    ).hexdigest()
    replacement_facts = {
        "simulation": {
            "simulator_export_contexts": [
                {
                    "text": replacement_text,
                    "sha256": replacement_context_sha256,
                }
            ]
        }
    }
    facts_path.write_text(json.dumps(replacement_facts), encoding="utf-8")
    observed_facts_sha256 = sha256_file(facts_path)
    simulation["status"] = "ready"
    simulation["frozen_compute_slot_identity_attestation"] = {
        "schema_version": FROZEN_COMPUTE_SLOT_IDENTITY_ATTESTATION_SCHEMA_VERSION,
        "status": "pass",
        "source_identity_sha256": identity_sha256,
        "attested_vivado_facts_sha256": identity["vivado_facts_sha256"],
        "observed_replaced_live_fact_bundle_sha256": observed_facts_sha256,
        "vcs_compile_plan_sha256": plan_sha256,
        "attested_simulator_export_context_sha256s": plan[
            "compile_authority"
        ]["simulator_export_context_sha256s"],
        "prior_executed_manifest": {
            "path": str(prior_path),
            "sha256": sha256_file(prior_path),
        },
        "prior_vcs_runner_report": {
            "path": str(runner_path_snapshot),
            "sha256": sha256_file(runner_path_snapshot),
        },
        "prior_vcs_job_contract": {
            "path": str(job_path),
            "sha256": sha256_file(job_path),
        },
        "required_passed_checks": sorted(
            FROZEN_COMPUTE_SLOT_IDENTITY_REQUIRED_CHECKS
        ),
    }
    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
    return facts_path, simulation


def _add_runtime_constant_evidence(
    root: Path,
    simulation_path: Path,
    simulation: dict,
) -> dict:
    image_path = root / "runtime_constants.u32.bin"
    image_path.write_bytes(bytes(range(8)))
    image_sha = sha256_file(image_path)
    connected_sha = "8" * 64
    layer_bindings = [
        {
            "layer_index": layer_index,
            "segment_id": "runtime_segment_0",
            "byte_offset": 0,
            "byte_count": 8,
            "word_offset": 0,
            "word_count": 2,
            "sha256": image_sha,
            "stage_bindings": [],
        }
        for layer_index in range(7)
    ]
    runtime_manifest = {
        "schema_version": "spatialaccagent.board_runtime_image_manifest.v1",
        "status": "pass",
        "accelerator_scope": "transformer_blocks_only",
        "scope_coverage_complete": True,
        "target_layer_count": 7,
        "connected_runtime_stream_contract_sha256": connected_sha,
        "path": str(image_path),
        "sha256": image_sha,
        "image_sha256": image_sha,
        "byte_count": 8,
        "total_bytes": 8,
        "word_count": 2,
        "unique_segments": [
            {
                "segment_id": "runtime_segment_0",
                "byte_offset": 0,
                "byte_count": 8,
                "word_offset": 0,
                "word_count": 2,
                "sha256": image_sha,
                "layer_indices": list(range(7)),
            }
        ],
        "layer_bindings": layer_bindings,
        "deduplication_policy": {
            "cross_layer_sharing_is_never_assumed": True,
            "shared_segment_requires_equal_recomputed_bytes": True,
            "different_streams_remain_distinct": True,
        },
    }
    runtime_manifest["manifest_contract_sha256"] = canonical_contract_sha256(
        runtime_manifest
    )
    manifest_path = root / "board_runtime_image_manifest.json"
    manifest_path.write_text(json.dumps(runtime_manifest), encoding="utf-8")
    load_schedule = [
        {
            **{
                key: row[key]
                for key in (
                    "layer_index",
                    "segment_id",
                    "byte_offset",
                    "byte_count",
                    "word_offset",
                    "word_count",
                    "sha256",
                )
            },
            "loader_address_start": 0,
            "loader_address_count": row["word_count"],
            "last_word_address": row["word_count"] - 1,
            "complete_before_kernel_start": True,
        }
        for row in layer_bindings
    ]
    loader_abi = {
        "valid_port": "runtime_valid",
        "ready_port": "runtime_ready",
        "addr_port": "runtime_addr",
        "data_port": "runtime_data",
        "last_port": "runtime_last",
        "data_width_bits": 32,
    }
    runtime_plan = {
        "schema_version": "spatialaccagent.board_memory_runtime_plan.v1",
        "status": "ready",
        "runtime_constants": {
            "enabled": True,
            "connected_runtime_stream_contract_sha256": connected_sha,
            "loader_abi": loader_abi,
            "load_schedule": load_schedule,
            "full_runtime_image_manifest": runtime_manifest,
        },
    }
    runtime_plan["validation"] = {
        "status": "pass",
        "target_layer_count": 7,
        "errors": [],
    }
    runtime_plan["contract_sha256"] = canonical_contract_sha256(
        {
            key: value
            for key, value in runtime_plan.items()
            if key not in {"contract_sha256", "validation"}
        }
    )
    plan_path = root / "board_memory_runtime_plan.json"
    plan_path.write_text(json.dumps(runtime_plan), encoding="utf-8")

    integration = simulation["board_integration_contract"]
    integration["board_memory_runtime_contract_sha256"] = sha256_file(plan_path)
    integration["full_runtime_image_manifest_sha256"] = sha256_file(manifest_path)
    integration["full_runtime_image_sha256"] = image_sha
    integration["runtime_constants"] = {
        "enabled": True,
        "all_target_layers": True,
        "complete_before_kernel_start": True,
        "runtime_plan_contract_sha256": runtime_plan["contract_sha256"],
        "runtime_image_manifest_sha256": sha256_file(manifest_path),
        "runtime_image_manifest_contract_sha256": runtime_manifest[
            "manifest_contract_sha256"
        ],
        "runtime_image_sha256": image_sha,
        "connected_runtime_stream_contract_sha256": connected_sha,
        "loader_abi_sha256": canonical_contract_sha256(loader_abi),
        "load_schedule_sha256": canonical_contract_sha256(load_schedule),
        "evidence_refs": ["generated_control_facts"],
    }
    simulation["runtime_constant_binding"] = {
        "enabled": True,
        "board_memory_runtime_contract": {
            "path": str(plan_path),
            "sha256": sha256_file(plan_path),
        },
        "runtime_image_manifest": {
            "path": str(manifest_path),
            "sha256": sha256_file(manifest_path),
        },
        "runtime_image": {
            "path": str(image_path),
            "sha256": image_sha,
            "byte_count": image_path.stat().st_size,
        },
    }
    simulation.setdefault("artifacts", {})["runtime_image"] = {
        "path": str(image_path),
        "sha256": image_sha,
        "byte_count": image_path.stat().st_size,
    }
    simulation.setdefault("vcs", {}).setdefault("runtime_plusargs", {})[
        "RUNTIME_CONSTANTS"
    ] = "runtime_image"
    simulation["board_integration_contract_sha256"] = canonical_contract_sha256(
        integration
    )
    simulation["pipeline_overlap_results"][
        "board_integration_contract_sha256"
    ] = simulation["board_integration_contract_sha256"]
    simulation["execution_outputs"]["runtime_loader_report"] = {
        "path": "evidence/runtime_loader.json",
        "schema_version": "test.runtime_loader.v1",
    }
    layers = [
        {
            "layer_index": row["layer_index"],
            "segment_id": row["segment_id"],
            "segment_sha256": row["sha256"],
            "expected_word_count": row["word_count"],
            "accepted_word_count": row["word_count"],
            "accepted_address_count": row["loader_address_count"],
            "first_accepted_address": row["loader_address_start"],
            "last_accepted_address": row["last_word_address"],
            "address_sequence_contiguous": True,
            "address_sequence_unique": True,
            "data_matches_image_segment": True,
            "last_asserted_on_final_accept": True,
            "load_complete_cycle": 100 + row["layer_index"] * 10,
            "kernel_start_cycle": 101 + row["layer_index"] * 10,
        }
        for row in load_schedule
    ]
    report_payload = {
        "status": "pass",
        "runtime_plan_contract_sha256": runtime_plan["contract_sha256"],
        "runtime_image_manifest_contract_sha256": runtime_manifest[
            "manifest_contract_sha256"
        ],
        "runtime_image_sha256": image_sha,
        "loader_abi_sha256": canonical_contract_sha256(loader_abi),
        "load_schedule_sha256": canonical_contract_sha256(load_schedule),
        "target_layer_count": 7,
        "all_layers_loaded_exactly_once": True,
        "kernel_start_before_load_complete_observed": False,
        "layers": layers,
    }
    report_artifact = _write(
        root / "executed" / "runtime_loader.json", json.dumps(report_payload)
    )
    simulation["runtime_loader_results"] = {
        **report_payload,
        "evidence_refs": ["runtime_loader_evidence"],
        "structured_report": {
            **report_artifact,
            "relative_path": "evidence/runtime_loader.json",
        },
    }
    simulation["dynamic_evidence_records"].append(
        {
            "evidence_id": "runtime_loader_evidence",
            "evidence_kind": "runtime_loader_report",
            "schema_version": "test.runtime_loader.v1",
            **report_artifact,
        }
    )
    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
    return simulation


def _promote_identity_to_v2_with_selector_coverage(
    identity_path: Path, identity: dict
) -> tuple[Path, Path, Path]:
    root = identity_path.parent
    closure_rows = identity["selected_simulation_source_closure"]["source_files"]
    source_ids = [row["source_id"] for row in closure_rows]
    object_ids = ["fact.cell.0", "fact.pin.0"]
    facts = {
        "schema_version": "test.vivado_facts.v2",
        "status": "pass",
        "objects": [
            {
                "object_id": object_ids[0],
                "kind": "cell",
                "members": [{"object_id": object_ids[1], "kind": "pin"}],
            }
        ],
        "simulation": {
            "source_files": [{"source_id": source_id} for source_id in source_ids]
        },
    }
    facts_path = root / "v2_vivado_facts.json"
    facts_path.write_text(json.dumps(facts), encoding="utf-8")
    facts_sha256 = sha256_file(facts_path)

    worker = {
        "schema_version": "spatialaccagent.stage_worker_record.v0",
        "agent": "exact_board_interface_selector_map_000_agent",
        "output": {
            "reviewed_object_ids": object_ids,
            "reviewed_source_ids": source_ids,
        },
    }
    worker_path = root / "llm" / "selector_map_000.json"
    worker_path.parent.mkdir(parents=True, exist_ok=True)
    worker_path.write_text(json.dumps(worker), encoding="utf-8")
    semantic_fingerprint = canonical_contract_sha256(
        {"object_ids": object_ids, "source_ids": source_ids}
    )
    checkpoint = {
        "schema_version": "spatialaccagent.board_interface_selection_map_checkpoint.v1",
        "status": "pass",
        "chunk_count": 1,
        "chunks": [
            {
                "chunk_index": 0,
                "chunk_count": 1,
                "agent": worker["agent"],
                "semantic_fingerprint": semantic_fingerprint,
                "record_file": worker_path.name,
                "record_sha256": sha256_file(worker_path),
                "last_materialization_source": "exact_prompt",
                "origin_exact_prompt_validated": True,
            }
        ],
    }
    checkpoint_path = root / "llm" / "exact_board_interface_selector_map_checkpoint.json"
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    worker_row = {
        "phase": "map",
        "agent": worker["agent"],
        "path": str(worker_path),
        "sha256": sha256_file(worker_path),
        "chunk_index": 0,
        "semantic_fingerprint": semantic_fingerprint,
        "reuse_authority": {
            "checkpoint_chunk_index": 0,
            "checkpoint_semantic_fingerprint": semantic_fingerprint,
            "materialization_source": "exact_prompt",
        },
        "reviewed_object_count": len(object_ids),
        "reviewed_source_count": len(source_ids),
        "reviewed_object_ids_sha256": canonical_contract_sha256(sorted(object_ids)),
        "reviewed_source_ids_sha256": canonical_contract_sha256(sorted(source_ids)),
    }
    ledger = {
        "schema_version": "spatialaccagent.board_interface_selection_coverage.v1",
        "status": "pass",
        "input_vivado_fact_canonical_sha256": canonical_contract_sha256(facts),
        "map_semantic_checkpoint": {
            "path": str(checkpoint_path),
            "sha256": sha256_file(checkpoint_path),
        },
        "complete_coverage": {
            "reviewed_object_ids": object_ids,
            "reviewed_source_ids": source_ids,
            "reviewed_object_count": len(object_ids),
            "reviewed_source_count": len(source_ids),
            "reviewed_object_ids_sha256": canonical_contract_sha256(sorted(object_ids)),
            "reviewed_source_ids_sha256": canonical_contract_sha256(sorted(source_ids)),
            "all_fact_and_source_units_reviewed": True,
        },
        "worker_records": [worker_row],
    }
    ledger_path = root / "llm" / "exact_board_interface_selector_progressive_coverage.json"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    coverage_ref = {"path": str(ledger_path), "sha256": sha256_file(ledger_path)}

    identity["schema_version"] = "spatialaccagent.exact_sample_board_source_identity.v2"
    identity["vivado_facts_path"] = str(facts_path)
    identity["vivado_facts_sha256"] = facts_sha256
    identity["discovery_provenance"]["input_fact_bundle"] = {
        "path": str(facts_path),
        "sha256": facts_sha256,
    }
    identity["discovery_provenance"]["progressive_selector_coverage"] = coverage_ref
    identity_path.write_text(json.dumps(identity), encoding="utf-8")
    return facts_path, ledger_path, worker_path


def _materializer_case(root: Path) -> tuple[Path, dict, dict, Path]:
    authority_root = root / "authority"
    identity_path, _, identity, simulation = _case(authority_root)
    run_dir = root / "run"
    target_identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
    target_identity_path.parent.mkdir(parents=True, exist_ok=True)

    export_text = "/tools/vlogan -work xil_defaultlib source.sv\n/tools/vcs -top BoardTestbench -o simv\n"
    export_artifact = _write(authority_root / "vivado_export_commands.sh", export_text)
    facts = {
        "schema_version": "test.vivado_facts.v1",
        "status": "pass",
        "simulation": {
            "simulator_export_contexts": [
                {
                    "remote_path": "/sample/export/compile.sh",
                    "sha256": export_artifact["sha256"],
                    "text": export_text,
                }
            ]
        },
    }
    facts_path = target_identity_path.parent / "vivado_structured_facts.json"
    facts_path.write_text(json.dumps(facts), encoding="utf-8")
    identity["vivado_facts_path"] = str(facts_path)
    identity["vivado_facts_sha256"] = sha256_file(facts_path)
    target_identity_path.write_text(json.dumps(identity), encoding="utf-8")
    source_fixture_reference = simulation["external_simulation_fixture"]
    source_fixture_path = Path(source_fixture_reference["path"])
    fixture_path = target_identity_path.parent / "external_simulation_fixture.json"
    fixture_path.write_bytes(source_fixture_path.read_bytes())
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture_context_hashes = [
        row["sha256"]
        for row in fixture["compile_authority"]["export_contexts"]
    ]

    board_root = run_dir / "generated" / "board_integration"
    kernel_root = run_dir / "generated" / "semantic_harness"
    source_by_id = {row["source_id"]: row for row in simulation["source_files"]}
    generated_rows: dict[str, dict] = {}
    for source_id in (
        "slot_adapter",
        "generated_harness",
        "generated_kernel",
        "board_testbench",
        "axi_monitor",
    ):
        source = source_by_id[source_id]
        target_root = kernel_root if source_id == "generated_kernel" else board_root
        target = target_root / Path(source["path"]).name
        artifact = _write(target, Path(source["path"]).read_text(encoding="utf-8"))
        generated_rows[source_id] = {
            **source,
            **artifact,
        }

    harness = copy.deepcopy(simulation["multilayer_harness"])
    harness["source_files"] = [
        generated_rows[row["source_id"]] for row in harness["source_files"]
    ]
    testbench = copy.deepcopy(simulation["testbench"])
    testbench.update(generated_rows["board_testbench"])
    monitor_contract = copy.deepcopy(simulation["protocol_monitor_contract"])
    monitor_contract["monitors"][0]["source_files"] = [generated_rows["axi_monitor"]]
    evidence_records = copy.deepcopy(simulation["generated_evidence_records"])
    for row in evidence_records:
        row["source_sha256"] = generated_rows[row["source_id"]]["sha256"]

    model_path = run_dir / "input" / "model_config.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps({"num_hidden_layers": 7}), encoding="utf-8")
    tool_profile = {
        "schema_version": "test.tool_profile.v1",
        "tools": [
            {
                "role": "functional_verification",
                "name": "vcs",
                "host": "vcs.test",
                "port": 22,
                "executable": "/tools/vcs",
            }
        ],
    }
    tool_profile_path = run_dir / "input" / "tool_profile.json"
    tool_profile_path.write_text(json.dumps(tool_profile), encoding="utf-8")

    tensor_hashes = ["1" * 64, "2" * 64]
    catalog = {
        "schema_version": "test.catalog.v1",
        "status": "pass",
        "accelerator_scope": "transformer_blocks_only",
        "scope_coverage_complete": True,
        "source_checkpoint_sha256": "3" * 64,
        "target_layer_count": 7,
        "tensor_count": 2,
        "tensors": [
            {"name": "layer.0.a", "source_slice_sha256": tensor_hashes[0]},
            {"name": "layer.1.a", "source_slice_sha256": tensor_hashes[1]},
        ],
    }
    catalog_path = run_dir / "verification" / "model_weights" / "transformer_block_weight_catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    memory_path = run_dir / "generated" / "chisel" / "memory" / "memory_layout.json"
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(json.dumps({"regions": [{"name": "weights", "base": 4096}]}), encoding="utf-8")

    input_artifact = _write(run_dir / "verification" / "semantic_testbench" / "board" / "input.memh", "01\n")
    expected_artifact = _write(run_dir / "verification" / "semantic_testbench" / "board" / "expected.memh", "02\n")
    semantic = {
        "schema_version": "test.semantic.v1",
        "status": "ready",
        "board": {
            "all_target_layer_reference_captured": True,
            "expected_target_layers": 7,
            "input_vector": input_artifact,
            "expected_output": expected_artifact,
        },
    }
    semantic_path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    semantic_path.write_text(json.dumps(semantic), encoding="utf-8")
    board_data = run_dir / "generated" / "board_integration" / "data"
    weight_artifact = _write(
        board_data / "transformer_block_weights.u32.bin", "03\n04\n"
    )
    weight_manifest = {
        "status": "pass",
        "path": weight_artifact["path"],
        "image_sha256": weight_artifact["sha256"],
        "total_bytes": Path(weight_artifact["path"]).stat().st_size,
        "layer_segments": [],
        "source_checkpoint_sha256": catalog["source_checkpoint_sha256"],
        "accelerator_scope": "transformer_blocks_only",
        "scope_coverage_complete": True,
        "accelerator_weight_catalog_sha256": sha256_file(catalog_path),
        "packed_tensor_hashes": tensor_hashes,
    }
    weight_manifest["manifest_contract_sha256"] = canonical_contract_sha256(
        weight_manifest
    )
    weight_manifest_path = board_data / "full_weight_image_manifest.json"
    weight_manifest_path.write_text(json.dumps(weight_manifest), encoding="utf-8")
    weight_artifact.update(weight_manifest)
    weight_artifact["sha256"] = weight_manifest["image_sha256"]
    runtime_contract = {
        "schema_version": "spatialaccagent.board_memory_runtime_plan.v1",
        "status": "ready",
        "runtime_constants": {"enabled": False},
    }
    runtime_contract["validation"] = {
        "status": "pass",
        "errors": [],
        "target_layer_count": 7,
    }
    runtime_contract["contract_sha256"] = canonical_contract_sha256(
        {
            key: value
            for key, value in runtime_contract.items()
            if key not in {"contract_sha256", "validation"}
        }
    )
    runtime_contract_path = (
        run_dir
        / "generated"
        / "board_integration"
        / "board_memory_runtime_contract.json"
    )
    runtime_contract_path.write_text(json.dumps(runtime_contract), encoding="utf-8")

    integration = copy.deepcopy(simulation["board_integration_contract"])
    integration.update(
        {
            "source_closure_sha256": identity["selected_simulation_source_closure_sha256"],
            "compute_slot_abi_sha256": identity["compute_slot_abi_sha256"],
            "timing_contract_sha256": identity["timing_contract_sha256"],
            "axi_interfaces_sha256": identity["axi_interfaces_sha256"],
            "memory_layout_sha256": sha256_file(memory_path),
            "board_memory_runtime_contract_sha256": sha256_file(
                runtime_contract_path
            ),
            "full_weight_image_manifest_sha256": sha256_file(
                weight_manifest_path
            ),
            "full_weight_image_sha256": weight_manifest["image_sha256"],
        }
    )
    compile_source_ids = [
        row["source_id"]
        for row in identity["selected_simulation_source_closure"]["source_files"]
        if row["source_id"] != "sample_slot"
    ] + source_fixture_reference["selected_source_ids"] + list(generated_rows)
    authority_ref = export_artifact["sha256"]
    compile_commands = [
        {
            "order": index,
            "phase": "compile",
            "tool_role": "functional_verification",
            "executable": "/tools/vlogan",
            "argv": ["-work", "xil_defaultlib", {"source_id": source_id}],
            "source_ids": [source_id],
            "cwd": "stage",
            "env": {},
            "shell": False,
            "authority_refs": (
                fixture_context_hashes
                if source_id in source_fixture_reference["selected_source_ids"]
                else [authority_ref]
            ),
        }
        for index, source_id in enumerate(compile_source_ids)
    ]
    compile_commands.append(
        {
            "order": len(compile_commands),
            "phase": "elaborate",
            "tool_role": "functional_verification",
            "executable": "/tools/vcs",
            "argv": ["-top", "BoardTestbench", "-o", "simv"],
            "source_ids": [],
            "cwd": "stage",
            "env": {},
            "shell": False,
            "authority_refs": [authority_ref],
        }
    )
    compile_plan = {
        "schema_version": "spatialaccagent.vcs_compile_plan.v1",
        "status": "ready",
        "compile_authority": {
            "vivado_facts_path": str(facts_path),
            "vivado_facts_sha256": identity["vivado_facts_sha256"],
            "simulator_export_context_sha256s": [authority_ref],
            "external_fixture_contract_sha256": fixture["contract_sha256"],
            "external_fixture_export_context_sha256s": fixture_context_hashes,
        },
        "tool_binding": tool_profile["tools"][0],
        "top_module": "BoardTestbench",
        "output": "simv",
        "ordered_commands": compile_commands,
    }
    manifest = {
        "all_target_layers": True,
        "bound_layer_count": 7,
        "board_consumed_tensor_hashes": tensor_hashes,
        "board_integration_contract": integration,
        "board_simulation_preflight_plan": {
            "external_simulation_fixture": {
                "selected_source_ids": copy.deepcopy(
                    source_fixture_reference["selected_source_ids"]
                ),
                "model_instance": copy.deepcopy(
                    source_fixture_reference["model_instance"]
                ),
            },
            "source_replacements": copy.deepcopy(simulation["source_replacements"]),
            "testbench": testbench,
            "top_module": "BoardTestbench",
            "protocol_monitor_contract": monitor_contract,
            "generated_evidence_records": evidence_records,
            "execution_outputs": copy.deepcopy(simulation["execution_outputs"]),
            "artifacts": {"weight_image": weight_artifact},
            "pass_regex": "BOARD PASS",
            "rtl_output_file": "rtl_output.memh",
            "boundary_trace_file": "boundary_trace.json",
            "vcs_compile_plan": compile_plan,
            "vcs": {
                "compile_args": [],
                "runtime_plusargs": {
                    "INPUT": "input",
                    "WEIGHTS": "weight_image",
                    "EXPECTED": "expected_output",
                },
            },
        },
    }
    return run_dir, manifest, harness, Path(testbench["path"])


class ExactBoardAcceptanceContractTest(TestCase):
    def test_debug_observability_is_adaptive_and_fail_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            valid = validate_exact_board_preflight(identity_path, simulation_path)
            self.assertEqual(valid["status"], "pass", valid["blockers"])

            variants = {
                "missing": lambda candidate: candidate["testbench"].pop(
                    "debug_observability_contract"
                ),
                "synthesis_impact": lambda candidate: candidate["testbench"][
                    "debug_observability_contract"
                ].__setitem__(
                    "synthesis_impact", "debug_registers"
                ),
                "stale_probe_source": lambda candidate: candidate["testbench"][
                    "debug_observability_contract"
                ]["probes"][0].__setitem__("source_sha256", "0" * 64),
            }
            expected = {
                "missing": "debug_observability_contract is missing",
                "synthesis_impact": "synthesis_impact is not none",
                "stale_probe_source": "source_sha256 does not bind",
            }
            for name, mutate in variants.items():
                with self.subTest(name=name):
                    candidate = copy.deepcopy(simulation)
                    mutate(candidate)
                    simulation_path.write_text(
                        json.dumps(candidate), encoding="utf-8"
                    )
                    preflight = validate_exact_board_preflight(
                        identity_path, simulation_path
                    )
                    self.assertEqual(preflight["status"], "pass", preflight["blockers"])
                    report = validate_exact_board_acceptance(
                        identity_path, simulation_path
                    )
                    self.assertEqual(report["status"], "fail")
                    self.assertTrue(
                        any(expected[name] in value for value in report["blockers"]),
                        report["blockers"],
                    )

    def test_identity_only_gate_uses_the_same_exact_contract(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, _, _, _ = _case(Path(temp_dir))
            result = validate_exact_board_identity(identity_path)
            self.assertEqual(result["status"], "pass", result["blockers"])

            identity = json.loads(identity_path.read_text(encoding="utf-8"))
            identity["discovery_provenance"]["mode"] = "static"
            identity_path.write_text(json.dumps(identity, indent=2), encoding="utf-8")
            result = validate_exact_board_identity(identity_path)
            self.assertEqual(result["status"], "fail")
            self.assertTrue(any("mode must be llm" in value for value in result["blockers"]))

    def test_exact_identity_v2_accepts_hash_bound_full_selector_coverage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, _, identity, _ = _case(Path(temp_dir))
            _, ledger_path, _ = _promote_identity_to_v2_with_selector_coverage(
                identity_path, identity
            )

            report = validate_exact_board_identity(identity_path)
            self.assertEqual(report["status"], "pass", report["blockers"])
            check = next(
                row
                for row in report["checks"]
                if row["name"] == "progressive_selector_full_coverage"
            )
            self.assertEqual(check["status"], "pass", check["blockers"])
            self.assertEqual(check["ledger_path"], str(ledger_path))
            self.assertEqual(check["reviewed_object_count"], 2)
            self.assertEqual(check["reviewed_source_count"], 4)
            self.assertEqual(check["worker_record_count"], 1)
            self.assertEqual(check["map_semantic_checkpoint_chunk_count"], 1)

    def test_exact_identity_v2_selector_coverage_fails_closed_on_stale_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in (
                "missing_reference",
                "ledger_byte_tamper",
                "stale_fact_hash",
                "stale_source_coverage",
                "worker_byte_tamper",
            ):
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, _, identity, _ = _case(root)
                    _, ledger_path, worker_path = _promote_identity_to_v2_with_selector_coverage(
                        identity_path, identity
                    )
                    identity = json.loads(identity_path.read_text(encoding="utf-8"))
                    if name == "missing_reference":
                        del identity["discovery_provenance"]["progressive_selector_coverage"]
                        identity_path.write_text(json.dumps(identity), encoding="utf-8")
                    elif name == "ledger_byte_tamper":
                        ledger_path.write_text(
                            ledger_path.read_text(encoding="utf-8") + "\n",
                            encoding="utf-8",
                        )
                    elif name == "worker_byte_tamper":
                        worker_path.write_text(
                            worker_path.read_text(encoding="utf-8") + "\n",
                            encoding="utf-8",
                        )
                    else:
                        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
                        if name == "stale_fact_hash":
                            ledger["input_vivado_fact_canonical_sha256"] = "0" * 64
                        else:
                            reviewed = ledger["complete_coverage"]["reviewed_source_ids"][:-1]
                            ledger["complete_coverage"]["reviewed_source_ids"] = reviewed
                            ledger["complete_coverage"]["reviewed_source_count"] = len(reviewed)
                            ledger["complete_coverage"]["reviewed_source_ids_sha256"] = (
                                canonical_contract_sha256(sorted(reviewed))
                            )
                        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
                        identity["discovery_provenance"]["progressive_selector_coverage"][
                            "sha256"
                        ] = sha256_file(ledger_path)
                        identity_path.write_text(json.dumps(identity), encoding="utf-8")

                    report = validate_exact_board_identity(identity_path)
                    self.assertEqual(report["status"], "fail")
                    expected = {
                        "missing_reference": "progressive_selector_coverage is required",
                        "ledger_byte_tamper": "artifact hash does not match",
                        "stale_fact_hash": "current Vivado fact canonical hash",
                        "stale_source_coverage": "complete source coverage differs",
                        "worker_byte_tamper": "worker_records[0] artifact hash does not match",
                    }[name]
                    self.assertTrue(
                        any(expected in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_exact_identity_v2_map_checkpoint_provenance_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in (
                "missing_checkpoint_reference",
                "checkpoint_byte_tamper",
                "semantic_fingerprint_mismatch",
                "reuse_authority_mismatch",
                "checkpoint_record_binding_mismatch",
            ):
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, _, identity, _ = _case(root)
                    _, ledger_path, _ = _promote_identity_to_v2_with_selector_coverage(
                        identity_path, identity
                    )
                    identity = json.loads(identity_path.read_text(encoding="utf-8"))
                    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
                    checkpoint_path = Path(ledger["map_semantic_checkpoint"]["path"])
                    if name == "missing_checkpoint_reference":
                        del ledger["map_semantic_checkpoint"]
                    elif name == "checkpoint_byte_tamper":
                        checkpoint_path.write_text(
                            checkpoint_path.read_text(encoding="utf-8") + "\n",
                            encoding="utf-8",
                        )
                    elif name == "semantic_fingerprint_mismatch":
                        ledger["worker_records"][0]["semantic_fingerprint"] = "0" * 64
                    elif name == "reuse_authority_mismatch":
                        ledger["worker_records"][0]["reuse_authority"][
                            "materialization_source"
                        ] = "semantic_checkpoint"
                    else:
                        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
                        checkpoint["chunks"][0]["record_sha256"] = "0" * 64
                        checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
                        ledger["map_semantic_checkpoint"]["sha256"] = sha256_file(
                            checkpoint_path
                        )
                    if name != "checkpoint_byte_tamper":
                        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
                        identity["discovery_provenance"]["progressive_selector_coverage"][
                            "sha256"
                        ] = sha256_file(ledger_path)
                        identity_path.write_text(json.dumps(identity), encoding="utf-8")

                    report = validate_exact_board_identity(identity_path)
                    self.assertEqual(report["status"], "fail")
                    expected = {
                        "missing_checkpoint_reference": "map_semantic_checkpoint is missing",
                        "checkpoint_byte_tamper": "map_semantic_checkpoint artifact hash does not match",
                        "semantic_fingerprint_mismatch": (
                            "semantic_fingerprint differs from its map checkpoint chunk"
                        ),
                        "reuse_authority_mismatch": (
                            "reuse_authority does not bind its current map checkpoint chunk"
                        ),
                        "checkpoint_record_binding_mismatch": (
                            "sha256 differs from its map checkpoint record_sha256"
                        ),
                    }[name]
                    self.assertTrue(
                        any(expected in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_exact_identity_v2_accepts_hash_bound_history_checkpoint_record(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "history_checkpoint"
            identity_path, _, identity, _ = _case(root)
            _, ledger_path, _ = _promote_identity_to_v2_with_selector_coverage(
                identity_path, identity
            )
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            checkpoint_path = Path(ledger["map_semantic_checkpoint"]["path"])
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            worker = ledger["worker_records"][0]
            current_path = Path(worker["path"])
            history_dir = checkpoint_path.parent / "history"
            history_dir.mkdir()
            archived_path = history_dir / f"{current_path.stem}.archived{current_path.suffix}"
            archived_path.write_bytes(current_path.read_bytes())
            current_path.unlink()
            worker["path"] = str(archived_path)
            worker["sha256"] = sha256_file(archived_path)
            checkpoint["chunks"][0]["record_artifact_path"] = str(
                archived_path.relative_to(checkpoint_path.parent)
            )
            checkpoint["chunks"][0]["record_sha256"] = sha256_file(archived_path)
            checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
            ledger["map_semantic_checkpoint"]["sha256"] = sha256_file(
                checkpoint_path
            )
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            identity["discovery_provenance"]["progressive_selector_coverage"][
                "sha256"
            ] = sha256_file(ledger_path)
            identity_path.write_text(json.dumps(identity), encoding="utf-8")

            report = validate_exact_board_identity(identity_path)

        self.assertEqual(report["status"], "pass", report["blockers"])

    def test_complete_generic_exact_board_contract_passes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, _ = _case(Path(temp_dir))
            report = validate_exact_board_acceptance(identity_path, simulation_path)
            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertTrue(all(row["status"] == "pass" for row in report["checks"]))
            self.assertEqual(report["replaced_sample_source_ids"], ["sample_slot"])
            self.assertNotIn("sample_slot", report["verified_compile_source_ids"])
            self.assertIn("slot_adapter", report["verified_compile_source_ids"])
            self.assertEqual(
                report["external_fixture_source_ids"], ["external-fixture-source"]
            )

    def test_compute_slot_axi_mode_accepts_generated_only_boundary_validation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, identity, simulation = _case(
                Path(temp_dir)
            )
            simulation = _convert_case_to_compute_slot_axi(
                identity_path,
                simulation_path,
                identity,
                simulation,
                keep_optional_fixture_reference=True,
            )

            preflight = validate_exact_board_preflight(identity_path, simulation_path)
            self.assertEqual(preflight["status"], "pass", preflight["blockers"])
            self.assertEqual(
                set(preflight["verified_compile_source_ids"]),
                set(simulation["generated_source_ids"]),
            )
            self.assertEqual(preflight["preserved_sample_source_ids"], [])
            self.assertEqual(preflight["external_fixture_source_ids"], [])
            fixture_check = next(
                row
                for row in preflight["checks"]
                if row["name"] == "external_simulation_fixture_binding"
            )
            self.assertFalse(fixture_check["required"])

            acceptance = validate_exact_board_acceptance(
                identity_path, simulation_path
            )
            self.assertEqual(
                acceptance["status"], "pass", acceptance["blockers"]
            )

    def test_frozen_compute_slot_authority_does_not_mask_current_source_tamper(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, identity, simulation = _case(
                Path(temp_dir)
            )
            simulation = _convert_case_to_compute_slot_axi(
                identity_path,
                simulation_path,
                identity,
                simulation,
            )
            _, simulation = _install_frozen_compute_slot_attestation(
                identity_path,
                simulation_path,
                identity,
                simulation,
            )

            recovered = validate_exact_board_preflight(
                identity_path, simulation_path
            )
            self.assertEqual(recovered["status"], "pass", recovered["blockers"])
            frozen_check = next(
                row
                for row in recovered["checks"]
                if row["name"] == "frozen_compute_slot_identity_attestation"
            )
            self.assertEqual(frozen_check["status"], "pass")
            plan_check = next(
                row
                for row in recovered["checks"]
                if row["name"] == "canonical_vcs_compile_plan"
            )
            self.assertTrue(plan_check["frozen_vivado_export_authority_reused"])

            physical = copy.deepcopy(simulation)
            physical["validation_mode"] = "exact_sample_physical_ddr"
            simulation_path.write_text(json.dumps(physical), encoding="utf-8")
            rejected_physical = validate_exact_board_preflight(
                identity_path, simulation_path
            )
            self.assertEqual(rejected_physical["status"], "fail")
            self.assertTrue(
                any(
                    "permitted only for compute_slot_axi" in blocker
                    for blocker in rejected_physical["blockers"]
                ),
                rejected_physical["blockers"],
            )

            source_path = Path(simulation["source_files"][0]["path"])
            source_path.write_text(
                source_path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            tampered = validate_exact_board_preflight(identity_path, simulation_path)
            self.assertEqual(tampered["status"], "fail")
            self.assertTrue(
                any("source hash does not match file" in value for value in tampered["blockers"]),
                tampered["blockers"],
            )

    def test_compute_slot_axi_mode_rejects_rtl_substitution_or_fixture_compile(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in ("rtl_substitution", "fixture_compile"):
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, simulation_path, identity, simulation = _case(root)
                    fixture_source = next(
                        row
                        for row in simulation["source_files"]
                        if row["source_id"] == "external-fixture-source"
                    )
                    simulation = _convert_case_to_compute_slot_axi(
                        identity_path, simulation_path, identity, simulation
                    )
                    if name == "rtl_substitution":
                        simulation["testbench"]["axi_transaction_memory_model"][
                            "replaces_compute_slot_rtl"
                        ] = True
                        expected = "may not replace compute-slot RTL"
                    else:
                        simulation["source_files"].append(fixture_source)
                        simulation["compile_source_ids"].append(
                            fixture_source["source_id"]
                        )
                        simulation["compile_source_set_sha256"] = (
                            compile_source_set_fingerprint(simulation["source_files"])
                        )
                        expected = "must contain only the generated/certified boundary source set"
                    simulation_path.write_text(
                        json.dumps(simulation), encoding="utf-8"
                    )

                    report = validate_exact_board_preflight(
                        identity_path, simulation_path
                    )
                    self.assertEqual(report["status"], "fail")
                    self.assertTrue(
                        any(expected in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_external_fixture_preflight_rejects_stale_or_unselected_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in ("stale_contract", "unselected_source"):
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, simulation_path, _, simulation = _case(root)
                    if name == "stale_contract":
                        reference = simulation["external_simulation_fixture"]
                        fixture_path = Path(reference["path"])
                        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
                        fixture["status"] = "fail"
                        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
                        reference["sha256"] = sha256_file(fixture_path)
                        expected = "external simulation fixture status is not pass"
                    else:
                        simulation["external_simulation_fixture"]["selected_source_ids"] = [
                            "not-authorized"
                        ]
                        expected = "selected_source_ids are not exact compile-authority IDs"
                    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

                    report = validate_exact_board_preflight(identity_path, simulation_path)
                    self.assertEqual(report["status"], "fail")
                    self.assertTrue(
                        any(expected in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_external_fixture_preflight_rejects_port_testbench_or_vcs_drift(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in (
                "physical_binding",
                "clock_authority",
                "role_exclusivity",
                "testbench_binding",
                "vcs_authority",
            ):
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, simulation_path, _, simulation = _case(root)
                    if name == "physical_binding":
                        model = simulation["external_simulation_fixture"]["model_instance"]
                        model["physical_port_bindings"].pop()
                        simulation["testbench"]["external_memory_component"] = copy.deepcopy(
                            model
                        )
                        expected = "do not exactly cover provider pins"
                    elif name in {"clock_authority", "role_exclusivity"}:
                        model = simulation["external_simulation_fixture"]["model_instance"]
                        clock_binding = next(
                            row
                            for row in model["physical_port_bindings"]
                            if row["binding_role"] == "exact_timing_clock_driver"
                        )
                        if name == "clock_authority":
                            clock_binding["timing_clock_name"] = "not-authorized"
                            expected = "is not an identity timing clock domain"
                        else:
                            clock_binding["target_port"] = "not-mutually-exclusive"
                            expected = "must contain timing_clock_name and no target_port"
                        simulation["testbench"]["external_memory_component"] = copy.deepcopy(
                            model
                        )
                    elif name == "testbench_binding":
                        simulation["testbench"][
                            "external_simulation_fixture_contract_sha256"
                        ] = "0" * 64
                        expected = "testbench does not bind the external fixture contract hash"
                    else:
                        fixture_source_id = simulation["external_simulation_fixture"][
                            "selected_source_ids"
                        ][0]
                        command = next(
                            row
                            for row in simulation["vcs_compile_plan"]["ordered_commands"]
                            if fixture_source_id in row["source_ids"]
                        )
                        command["authority_refs"] = simulation["vcs_compile_plan"][
                            "compile_authority"
                        ]["simulator_export_context_sha256s"]
                        simulation["vcs_compile_plan_sha256"] = canonical_contract_sha256(
                            simulation["vcs_compile_plan"]
                        )
                        expected = "external fixture sources are not bound to their export context"
                    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

                    report = validate_exact_board_preflight(identity_path, simulation_path)
                    self.assertEqual(report["status"], "fail")
                    self.assertTrue(
                        any(expected in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_external_fixture_acceptance_requires_one_real_hierarchy_instance(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in ("missing", "mapping", "forced_calibration"):
                with self.subTest(name=name):
                    identity_path, simulation_path, _, simulation = _case(
                        Path(temp_dir) / name
                    )
                    instances = simulation["elaborated_hierarchy"]["instances"]
                    external = next(
                        row
                        for row in instances
                        if row.get("binding_role") == "external_memory_component"
                    )
                    if name == "missing":
                        instances.remove(external)
                        expected = "exactly one external memory component instance"
                    elif name == "mapping":
                        external["physical_port_bindings"][0]["target_port"] = "drift"
                        expected = "does not bind every physical provider pin"
                    else:
                        external["calibration_forced"] = True
                        expected = "external memory hierarchy instance forces calibration"
                    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

                    report = validate_exact_board_acceptance(
                        identity_path, simulation_path
                    )
                    self.assertEqual(report["status"], "fail")
                    self.assertTrue(
                        any(expected in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_runtime_constants_preflight_binds_plan_manifest_image_and_loader_abi(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            identity_path, simulation_path, _, simulation = _case(root)
            simulation = _add_runtime_constant_evidence(root, simulation_path, simulation)

            preflight_only = copy.deepcopy(simulation)
            preflight_only["status"] = "ready"
            preflight_only.pop("runtime_loader_results")
            preflight_only["dynamic_evidence_records"] = [
                row
                for row in preflight_only["dynamic_evidence_records"]
                if row.get("evidence_kind") != "runtime_loader_report"
            ]
            simulation_path.write_text(json.dumps(preflight_only), encoding="utf-8")
            report = validate_exact_board_preflight(identity_path, simulation_path)

            self.assertEqual(report["status"], "pass", report["blockers"])
            check = next(
                row
                for row in report["checks"]
                if row["name"] == "runtime_constant_image_and_loader_binding"
            )
            self.assertEqual(check["status"], "pass", check["blockers"])
            self.assertTrue(check["enabled"])

    def test_runtime_constants_preflight_rejects_image_or_loader_binding_tamper(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in ("image", "loader_abi", "staged_artifact"):
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, simulation_path, _, simulation = _case(root)
                    simulation = _add_runtime_constant_evidence(
                        root, simulation_path, simulation
                    )
                    if name == "image":
                        Path(
                            simulation["runtime_constant_binding"]["runtime_image"][
                                "path"
                            ]
                        ).write_bytes(b"tampered")
                    elif name == "loader_abi":
                        simulation["board_integration_contract"]["runtime_constants"][
                            "loader_abi_sha256"
                        ] = "0" * 64
                        simulation["board_integration_contract_sha256"] = (
                            canonical_contract_sha256(
                                simulation["board_integration_contract"]
                            )
                        )
                        simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
                    else:
                        simulation["artifacts"]["runtime_image"]["sha256"] = "0" * 64
                        simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

                    report = validate_exact_board_preflight(
                        identity_path, simulation_path
                    )
                    self.assertEqual(report["status"], "fail")
                    expected = {
                        "image": "artifact hash does not match",
                        "loader_abi": "loader_abi_sha256",
                        "staged_artifact": "artifacts.runtime_image differs",
                    }[name]
                    self.assertTrue(
                        any(expected in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_runtime_loader_acceptance_requires_exact_data_and_load_before_start(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in ("pass", "data_mismatch", "early_start"):
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, simulation_path, _, simulation = _case(root)
                    simulation = _add_runtime_constant_evidence(
                        root, simulation_path, simulation
                    )
                    if name == "data_mismatch":
                        simulation["runtime_loader_results"]["layers"][0][
                            "data_matches_image_segment"
                        ] = False
                    elif name == "early_start":
                        layer = simulation["runtime_loader_results"]["layers"][0]
                        layer["kernel_start_cycle"] = layer["load_complete_cycle"]
                    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

                    report = validate_exact_board_acceptance(
                        identity_path, simulation_path
                    )
                    if name == "pass":
                        self.assertEqual(report["status"], "pass", report["blockers"])
                    else:
                        self.assertEqual(report["status"], "fail")
                        expected = (
                            "data_matches_image_segment"
                            if name == "data_mismatch"
                            else "load_complete_cycle < kernel_start_cycle"
                        )
                        self.assertTrue(
                            any(expected in blocker for blocker in report["blockers"]),
                            report["blockers"],
                        )

    def test_canonical_vcs_compile_plan_hash_is_exported_by_preflight(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            report = validate_exact_board_preflight(identity_path, simulation_path)
            plan_hash = canonical_contract_sha256(simulation["vcs_compile_plan"])

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(report["vcs_compile_plan_sha256"], plan_hash)
            check = next(row for row in report["checks"] if row["name"] == "canonical_vcs_compile_plan")
            self.assertEqual(check["status"], "pass", check["blockers"])
            self.assertEqual(check["sha256"], plan_hash)

    def test_vcs_compile_plan_rejects_shell_control_and_arbitrary_absolute_literals(self) -> None:
        with TemporaryDirectory() as temp_dir:
            mutations = {
                "shell": lambda command: command.update({"shell": True}),
                "control": lambda command: command["argv"].insert(0, "&&"),
                "absolute": lambda command: command["argv"].insert(0, "-I/tmp/unbound"),
            }
            expected = {
                "shell": ".shell must be false",
                "control": "unsafe literal token",
                "absolute": "arbitrary absolute path",
            }
            for name, mutate in mutations.items():
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, simulation_path, _, simulation = _case(root)
                    mutate(simulation["vcs_compile_plan"]["ordered_commands"][0])
                    simulation["vcs_compile_plan_sha256"] = canonical_contract_sha256(
                        simulation["vcs_compile_plan"]
                    )
                    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

                    report = validate_exact_board_preflight(identity_path, simulation_path)
                    self.assertEqual(report["status"], "fail")
                    self.assertTrue(
                        any(expected[name] in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_vcs_compile_plan_accepts_vcs_timescale_literal(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            command = simulation["vcs_compile_plan"]["ordered_commands"][0]
            command["argv"].insert(0, "-timescale=1ns/1ps")
            simulation["vcs_compile_plan_sha256"] = canonical_contract_sha256(
                simulation["vcs_compile_plan"]
            )
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

            report = validate_exact_board_preflight(identity_path, simulation_path)

            self.assertEqual(report["status"], "pass", report["blockers"])

    def test_vcs_compile_plan_rejects_duplicate_and_replaced_source_tokens(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in ("duplicate", "replaced"):
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, simulation_path, _, simulation = _case(root)
                    command = simulation["vcs_compile_plan"]["ordered_commands"][0]
                    if name == "duplicate":
                        source_id = command["source_ids"][0]
                        command["argv"].append({"source_id": source_id})
                        command["source_ids"].append(source_id)
                    else:
                        command["argv"][-1] = {"source_id": "sample_slot"}
                        command["source_ids"] = ["sample_slot"]
                    simulation["vcs_compile_plan_sha256"] = canonical_contract_sha256(
                        simulation["vcs_compile_plan"]
                    )
                    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

                    report = validate_exact_board_preflight(identity_path, simulation_path)
                    self.assertEqual(report["status"], "fail")
                    self.assertTrue(
                        any("every transformed source ID exactly once" in value for value in report["blockers"]),
                        report["blockers"],
                    )
                    if name == "replaced":
                        self.assertTrue(
                            any("replaced sample-project source ID" in value for value in report["blockers"])
                        )

    def test_vcs_compile_plan_rejects_unbound_driver_tool_and_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            mutations = {
                "driver": lambda plan: plan["ordered_commands"][0].update(
                    {"executable": "/bin/bash"}
                ),
                "export_authority": lambda plan: plan["ordered_commands"][0].update(
                    {"executable": "/tools/vhdlan"}
                ),
                "tool_binding": lambda plan: plan["tool_binding"].update(
                    {"host": "different.test"}
                ),
                "tool_profile_hash": lambda plan: plan.update(
                    {"tool_profile_sha256": "0" * 64}
                ),
            }
            expected = {
                "driver": "not a vcs/vlogan/vhdlan driver",
                "export_authority": "not authorized by current tool_profile or referenced Vivado export",
                "tool_binding": "tool_binding.host does not match current tool_profile",
                "tool_profile_hash": "does not uniquely bind the current run tool_profile",
            }
            for name, mutate in mutations.items():
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, simulation_path, _, simulation = _case(root)
                    mutate(simulation["vcs_compile_plan"])
                    simulation["vcs_compile_plan_sha256"] = canonical_contract_sha256(
                        simulation["vcs_compile_plan"]
                    )
                    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

                    report = validate_exact_board_preflight(identity_path, simulation_path)
                    self.assertEqual(report["status"], "fail")
                    self.assertTrue(
                        any(expected[name] in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_vcs_compile_plan_rejects_compile_elaboration_top_and_output_drift(self) -> None:
        with TemporaryDirectory() as temp_dir:
            for name in ("order", "top", "output"):
                with self.subTest(name=name):
                    root = Path(temp_dir) / name
                    identity_path, simulation_path, _, simulation = _case(root)
                    plan = simulation["vcs_compile_plan"]
                    if name == "order":
                        plan["ordered_commands"] = [
                            plan["ordered_commands"][-1],
                            *plan["ordered_commands"][:-1],
                        ]
                        for index, command in enumerate(plan["ordered_commands"]):
                            command["order"] = index
                    elif name == "top":
                        plan["top_module"] = "OtherBoardTestbench"
                        plan["ordered_commands"][-1]["argv"][1] = "OtherBoardTestbench"
                    else:
                        plan["output"] = "other_simv"
                        plan["ordered_commands"][-1]["argv"][-1] = "other_simv"
                    simulation["vcs_compile_plan_sha256"] = canonical_contract_sha256(plan)
                    simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

                    report = validate_exact_board_preflight(identity_path, simulation_path)
                    self.assertEqual(report["status"], "fail")
                    expected = {
                        "order": "must end with exactly one elaboration command",
                        "top": "does not bind the board testbench top",
                        "output": "must be the safe simulator artifact simv",
                    }[name]
                    self.assertTrue(
                        any(expected in blocker for blocker in report["blockers"]),
                        report["blockers"],
                    )

    def test_vcs_compile_plan_declared_hash_cannot_be_stale(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            simulation["vcs_compile_plan"]["ordered_commands"][0]["cwd"] = "new_stage"
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")

            report = validate_exact_board_preflight(identity_path, simulation_path)
            self.assertEqual(report["status"], "fail")
            self.assertTrue(
                any("vcs_compile_plan_sha256 does not match" in value for value in report["blockers"])
            )

    def test_framework_materializes_ready_exact_board_preflight(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, manifest, harness, _ = _materializer_case(Path(temp_dir))
            report = materialize_exact_board_preflight_manifest(manifest, harness, run_dir)
            materialized = json.loads(Path(report["manifest"]).read_text(encoding="utf-8"))

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(materialized["status"], "ready")
            self.assertEqual(report["exact_board_preflight"]["status"], "pass")
            self.assertEqual(
                materialized["compile_source_ids"],
                [
                    source_id
                    for row in materialized["vcs_compile_plan"]["ordered_commands"]
                    if row["phase"] == "compile"
                    for source_id in row["source_ids"]
                ],
            )
            self.assertEqual(
                report["vcs_compile_plan_sha256"],
                canonical_contract_sha256(materialized["vcs_compile_plan"]),
            )
            self.assertNotIn("sample_slot", materialized["compile_source_ids"])

    def test_framework_preserves_nested_testbench_top_module(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, manifest, harness, _ = _materializer_case(Path(temp_dir))
            plan = manifest["board_simulation_preflight_plan"]
            flat_testbench = plan["testbench"]
            plan["testbench"] = {
                "top_module": flat_testbench["top_module"],
                "source": flat_testbench,
            }

            report = materialize_exact_board_preflight_manifest(
                manifest, harness, run_dir
            )
            materialized = json.loads(
                Path(report["manifest"]).read_text(encoding="utf-8")
            )

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(
                materialized["testbench"]["top_module"],
                plan["top_module"],
            )

    def test_framework_normalizes_deterministic_preflight_schema_aliases(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, manifest, harness, _ = _materializer_case(Path(temp_dir))
            capture_path = (
                run_dir
                / "verification"
                / "board_runtime_capture"
                / "layer_runtime_capture_contract.json"
            )
            capture_path.parent.mkdir(parents=True, exist_ok=True)
            capture_path.write_text("{}\n", encoding="utf-8")
            plan = manifest["board_simulation_preflight_plan"]
            testbench = plan["testbench"]
            report_output = {
                "path": "evidence/testbench_ast_scan.json",
                "schema_version": "test.ast_scan.v1",
            }
            testbench["forbidden_construct_scan"] = {
                "status": "planned",
                "required": True,
                "method": "hdl_ast",
                "tool": {
                    "name": "hdl-ast-scan",
                    "version_argv": ["hdl-ast-scan", "--version"],
                    "version_regex": r"^hdl-ast-scan [0-9]+$",
                },
                "invocation": {
                    "argv": ["--report", report_output["path"]],
                    "cwd": "stage",
                },
                "required_checks": ["legacy_forbidden_construct_check"],
                "report_output": report_output,
            }
            plan["execution_outputs"]["testbench_ast_scan_report"] = copy.deepcopy(
                report_output
            )
            monitor = plan["protocol_monitor_contract"]["monitors"][0]
            monitor["fatal_checks"] = [value["kind"] for value in monitor.pop("checks")]
            plan["protocol_monitor_contract"].pop("all_axi_interfaces_covered")
            monitor["structured_report"]["required_fields"] = ["status", "violations"]
            plan["execution_outputs"]["protocol_reports"] = plan[
                "execution_outputs"
            ].pop("protocol_monitor_reports")

            first = materialize_exact_board_preflight_manifest(manifest, harness, run_dir)
            materialized = json.loads(Path(first["manifest"]).read_text(encoding="utf-8"))
            second = materialize_exact_board_preflight_manifest(manifest, harness, run_dir)

            self.assertEqual(first["status"], "pass", first["blockers"])
            self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
            scan = materialized["testbench"]["forbidden_construct_scan"]
            self.assertEqual(
                set(scan["required_checks"]),
                {
                    "forced_calibration_assignments",
                    "behavioral_memory_models",
                    "synthetic_latency_constructs",
                },
            )
            self.assertEqual(
                sum(value.count("{source}") for value in scan["invocation"]["argv"]),
                1,
            )
            self.assertEqual(
                sum(value.count("{report}") for value in scan["invocation"]["argv"]),
                1,
            )
            normalized_monitor = materialized["protocol_monitor_contract"]["monitors"][0]
            self.assertTrue(materialized["protocol_monitor_contract"]["all_axi_interfaces_covered"])
            self.assertTrue(
                all(
                    value["enabled"] is True and value["severity"] == "fatal"
                    for value in normalized_monitor["checks"]
                )
            )
            self.assertIn(
                "transaction_counts",
                normalized_monitor["structured_report"]["required_fields"],
            )
            self.assertIn(
                "protocol_monitor_reports", materialized["execution_outputs"]
            )
            self.assertNotIn("protocol_reports", materialized["execution_outputs"])
            self.assertEqual(
                materialized["board_integration_contract"][
                    "full_layer_runtime_capture_contract_sha256"
                ],
                hashlib.sha256(capture_path.read_bytes()).hexdigest(),
            )

    def test_framework_projects_compute_slot_memory_contract_from_plan(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, manifest, harness, _ = _materializer_case(Path(temp_dir))
            plan = manifest["board_simulation_preflight_plan"]
            plan["validation_mode"] = "compute_slot_axi"
            plan.pop("external_simulation_fixture", None)
            plan["testbench"].pop("axi_transaction_memory_model", None)
            plan["compute_slot_axi_transaction_memory_model"] = {
                "status": "ready",
                "contract_driven": True,
                "boundary": "compute_slot_axi",
                "replaces_compute_slot_rtl": False,
            }

            report = materialize_exact_board_preflight_manifest(manifest, harness, run_dir)
            materialized = json.loads(Path(report["manifest"]).read_text(encoding="utf-8"))
            memory_model = materialized["testbench"]["axi_transaction_memory_model"]

            self.assertEqual(memory_model["status"], "ready")
            self.assertTrue(memory_model["contract_driven"])
            self.assertFalse(memory_model["replaces_compute_slot_rtl"])
            self.assertEqual(memory_model["boundary"], "compute_slot_axi")
            self.assertFalse(
                any(
                    "transaction memory model is not" in blocker
                    or "transaction memory model may not replace" in blocker
                    for blocker in report["blockers"]
                ),
                report["blockers"],
            )

    def test_framework_accepts_axi_protocol_report_alias(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, manifest, harness, _ = _materializer_case(Path(temp_dir))
            plan = manifest["board_simulation_preflight_plan"]
            monitor_report = plan["protocol_monitor_contract"]["monitors"][0][
                "structured_report"
            ]
            plan["execution_outputs"]["axi_protocol_report"] = {
                "path": monitor_report["path"],
                "schema_version": monitor_report["schema_version"],
            }

            report = materialize_exact_board_preflight_manifest(manifest, harness, run_dir)

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertNotIn(
                "board execution output paths are not unique", report["blockers"]
            )

    def test_framework_preflight_fails_closed_on_generated_source_tamper(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, manifest, harness, testbench_path = _materializer_case(Path(temp_dir))
            testbench_path.write_text("module TamperedBoardTestbench; endmodule\n", encoding="utf-8")

            report = materialize_exact_board_preflight_manifest(manifest, harness, run_dir)

            self.assertEqual(report["status"], "incomplete")
            self.assertTrue(any("board testbench source hash mismatch" in value for value in report["blockers"]))
            materialized = json.loads(Path(report["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(materialized["status"], "incomplete")

    def test_framework_preflight_fails_closed_when_ordered_compile_plan_is_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, manifest, harness, _ = _materializer_case(Path(temp_dir))
            del manifest["board_simulation_preflight_plan"]["vcs_compile_plan"]

            report = materialize_exact_board_preflight_manifest(manifest, harness, run_dir)

            self.assertEqual(report["status"], "incomplete")
            self.assertTrue(any("vcs_compile_plan.ordered_commands" in value for value in report["blockers"]))

    def test_preflight_does_not_require_unproduced_execution_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            simulation["status"] = "ready"
            simulation.pop("execution_evidence")
            simulation.pop("elaborated_hierarchy")
            simulation.pop("protocol_monitor_results")
            simulation.pop("pipeline_overlap_results")
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            report = validate_exact_board_preflight(identity_path, simulation_path)
            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertNotIn(
                "elaborated_exact_top_and_accelerator_binding",
                {row["name"] for row in report["checks"]},
            )
            acceptance = validate_exact_board_acceptance(identity_path, simulation_path)
            self.assertEqual(acceptance["status"], "fail")
            self.assertTrue(any("elaborated_hierarchy" in blocker for blocker in acceptance["blockers"]))

    def test_legacy_weak_identity_fails_closed_with_explicit_fields(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            identity_path = root / "identity.json"
            simulation_path = root / "simulation.json"
            identity_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "exact_user_sample_wrapper": True,
                        "simulation_hashes_match_source": True,
                        "wrapper_axi_data_width_match": True,
                        "top_module": "AnyTop",
                    }
                ),
                encoding="utf-8",
            )
            simulation_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "exact_sample_wrapper_unmodified": True,
                        "source_identity_sha256": sha256_file(identity_path),
                    }
                ),
                encoding="utf-8",
            )
            report = validate_exact_board_acceptance(identity_path, simulation_path)
            self.assertEqual(report["status"], "fail")
            blockers = "\n".join(report["blockers"])
            self.assertIn("selected_simulation_source_closure", blockers)
            self.assertIn("compute_slot_abi", blockers)
            self.assertIn("timing_contract", blockers)
            self.assertIn("axi_interfaces", blockers)
            self.assertIn("elaborated_hierarchy", blockers)
            self.assertIn("protocol_monitor_contract", blockers)

    def test_non_llm_or_uncited_discovery_cannot_pass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, identity, simulation = _case(Path(temp_dir))
            identity["discovery_provenance"]["mode"] = "regex"
            identity["compute_slot_abi"]["required_ports"][0]["evidence_refs"] = []
            identity["compute_slot_abi_sha256"] = canonical_contract_sha256(identity["compute_slot_abi"])
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            simulation["source_identity_sha256"] = sha256_file(identity_path)
            simulation["compute_slot_abi_sha256"] = identity["compute_slot_abi_sha256"]
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_preflight(identity_path, simulation_path)["blockers"]
            self.assertIn("identity.discovery_provenance.mode must be llm", blockers)
            self.assertTrue(any("required_ports[0].evidence_refs" in blocker for blocker in blockers))

    def test_compute_slot_control_abi_requires_bitfields_signals_and_timing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, identity, simulation = _case(Path(temp_dir))
            del identity["compute_slot_abi"]["control_abi"]["timing"]["done_relation_to_valid"]
            identity["compute_slot_abi_sha256"] = canonical_contract_sha256(identity["compute_slot_abi"])
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            simulation["source_identity_sha256"] = sha256_file(identity_path)
            simulation["compute_slot_abi_sha256"] = identity["compute_slot_abi_sha256"]
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_preflight(identity_path, simulation_path)["blockers"]
            self.assertIn(
                "identity.compute_slot_abi.control_abi.timing.done_relation_to_valid is missing",
                blockers,
            )

    def test_derived_done_and_disabled_axi_sidebands_are_exact_contracts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, _, identity, _ = _case(Path(temp_dir))
            signals = identity["compute_slot_abi"]["control_abi"]["signals"]
            signals["done"] = {
                **copy.deepcopy(signals["count"]),
                "binding_kind": "derived_from_physical_port",
                "semantic": "counter_nonzero",
                "derived_from_role": "count",
                "predicate": "value != 0",
            }
            axi = identity["axi_interfaces"][0]
            axi["byte_order"] = "physical_byte_lane_order_preserved"
            axi["qos_width_bits"] = 0
            axi["region_width_bits"] = 0
            for channel in ("aw", "ar"):
                axi["signal_map"][channel]["qos"] = None
                axi["signal_map"][channel]["region"] = None
            identity["compute_slot_abi_sha256"] = canonical_contract_sha256(
                identity["compute_slot_abi"]
            )
            identity["axi_interfaces_sha256"] = canonical_contract_sha256(
                identity["axi_interfaces"]
            )
            identity_path.write_text(json.dumps(identity), encoding="utf-8")

            self.assertEqual(validate_exact_board_identity(identity_path)["status"], "pass")

    def test_testbench_cannot_replace_exact_memory_with_behavioral_ddr(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            simulation["testbench"]["behavioral_ddr_substitute"] = True
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_preflight(identity_path, simulation_path)["blockers"]
            self.assertIn("simulation.testbench.behavioral_ddr_substitute must be false", blockers)

    def test_generated_control_facts_cannot_reference_sample_evidence_namespace(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            simulation["board_integration_contract"]["scheduler"]["evidence_refs"] = ["sample_project_facts"]
            simulation["board_integration_contract_sha256"] = canonical_contract_sha256(
                simulation["board_integration_contract"]
            )
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_preflight(identity_path, simulation_path)["blockers"]
            self.assertTrue(any("board_integration_contract.scheduler.evidence_refs" in blocker for blocker in blockers))

    def test_post_run_protocol_result_requires_typed_dynamic_evidence_ref(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            simulation["protocol_monitor_results"]["interfaces"][0]["evidence_refs"] = [
                "compile_log_evidence"
            ]
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_acceptance(identity_path, simulation_path)["blockers"]
            self.assertTrue(any("wrong dynamic evidence kind" in blocker for blocker in blockers))

    def test_synthesis_source_cannot_enter_compile_closure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, identity, simulation = _case(Path(temp_dir))
            identity["selected_simulation_source_closure"]["source_files"][1]["role"] = "bd_synth"
            identity["selected_simulation_source_closure_sha256"] = source_closure_fingerprint(
                identity["selected_simulation_source_closure"]["source_files"]
            )
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            simulation["source_identity_sha256"] = sha256_file(identity_path)
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            report = validate_exact_board_acceptance(identity_path, simulation_path)
            self.assertTrue(any("synthesis-only" in blocker for blocker in report["blockers"]))

    def test_wrapper_bd_memory_or_ip_source_cannot_be_replaced(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, identity, simulation = _case(Path(temp_dir))
            identity["compute_slot_abi"]["replaced_source_ids"] = ["bd"]
            identity["compute_slot_abi_sha256"] = canonical_contract_sha256(identity["compute_slot_abi"])
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            simulation["source_identity_sha256"] = sha256_file(identity_path)
            simulation["compute_slot_abi_sha256"] = identity["compute_slot_abi_sha256"]
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_preflight(identity_path, simulation_path)["blockers"]
            self.assertTrue(any("protected wrapper/BD/memory/IP source: bd" in blocker for blocker in blockers))

    def test_uncontracted_generated_source_cannot_enter_compile_set(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            identity_path, simulation_path, _, simulation = _case(root)
            rogue = {
                "source_id": "rogue",
                "role": "generated_accelerator",
                **_write(root / "rogue.sv", "module Rogue; endmodule\n"),
                "dependencies": [],
                "declared_modules": ["Rogue"],
            }
            simulation["source_files"].append(rogue)
            simulation["compile_source_ids"].append("rogue")
            simulation["compile_source_set_sha256"] = compile_source_set_fingerprint(simulation["source_files"])
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_preflight(identity_path, simulation_path)["blockers"]
            self.assertTrue(any("verified sample-closure transformation" in blocker for blocker in blockers))

    def test_recursive_closure_rejects_unknown_dependency(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, identity, simulation = _case(Path(temp_dir))
            identity["selected_simulation_source_closure"]["source_files"][0]["dependencies"] = ["missing_ip"]
            identity["selected_simulation_source_closure_sha256"] = source_closure_fingerprint(
                identity["selected_simulation_source_closure"]["source_files"]
            )
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            simulation["source_identity_sha256"] = sha256_file(identity_path)
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_acceptance(identity_path, simulation_path)["blockers"]
            self.assertTrue(any("unresolved internal dependencies" in blocker for blocker in blockers))

    def test_elaboration_must_contain_generated_accelerator(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            simulation["elaborated_hierarchy"]["instances"] = [
                row
                for row in simulation["elaborated_hierarchy"]["instances"]
                if "generated_accelerator" not in row.get("binding_roles", [])
            ]
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_acceptance(identity_path, simulation_path)["blockers"]
            self.assertIn(
                "elaborated hierarchy does not contain exactly one generated accelerator instance",
                blockers,
            )

    def test_monitor_contract_requires_every_fatal_axi_check(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            simulation["protocol_monitor_contract"]["monitors"][0]["checks"].pop()
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_acceptance(identity_path, simulation_path)["blockers"]
            self.assertTrue(any("lacks fatal checks" in blocker for blocker in blockers))

    def test_multilayer_board_contract_requires_overlap_mechanisms(self) -> None:
        with TemporaryDirectory() as temp_dir:
            identity_path, simulation_path, _, simulation = _case(Path(temp_dir))
            del simulation["board_integration_contract"]["background_prefetch"]
            simulation_path.write_text(json.dumps(simulation), encoding="utf-8")
            blockers = validate_exact_board_acceptance(identity_path, simulation_path)["blockers"]
            self.assertIn("simulation.board_integration_contract.background_prefetch is missing", blockers)

    def test_hierarchical_axi_gate_uses_exact_board_contract(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            identity_path, simulation_path, _, _ = _case(Path(temp_dir) / "artifacts")
            target_identity = run_dir / "verification" / "board_interface" / "board_source_identity.json"
            target_simulation = run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
            target_identity.parent.mkdir(parents=True, exist_ok=True)
            target_simulation.parent.mkdir(parents=True, exist_ok=True)
            target_identity.write_text(identity_path.read_text(encoding="utf-8"), encoding="utf-8")
            simulation = json.loads(simulation_path.read_text(encoding="utf-8"))
            simulation["source_identity_sha256"] = sha256_file(target_identity)
            target_simulation.write_text(json.dumps(simulation), encoding="utf-8")
            report = check_axi_ddr_interface(run_dir)
            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(report["acceptance_contract_schema_version"], "spatialaccagent.exact_board_preflight.v1")

    def test_builtin_and_user_adapters_declare_exact_board_capabilities(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            adapter = qwen2_hf_case_adapter({"model_type": "qwen2"}, root / "run")
            discovery = set(adapter["tools"]["board_interface_discovery"]["capabilities"])
            acceptance = set(adapter["tools"]["axi_ddr_interface"]["capabilities"])
            self.assertTrue(EXACT_BOARD_DISCOVERY_CAPABILITIES.issubset(discovery))
            self.assertTrue(EXACT_BOARD_ACCEPTANCE_CAPABILITIES.issubset(acceptance))

            user_path = root / "case_adapter.json"
            user_path.write_text("{}", encoding="utf-8")
            user = normalize_user_adapter({"tools": {}}, user_path, root / "user_run")
            self.assertEqual(user["status"], "incomplete")
            self.assertTrue(any("exact-board tool role" in error for error in user["errors"]))

    def test_builtin_adapter_uses_materialized_board_testbench_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            testbench = (
                run_dir
                / "generated"
                / "board_integration"
                / "exact_board_testbench.sv"
            )
            testbench.parent.mkdir(parents=True)
            testbench.write_text("module exact_board_testbench; endmodule\n", encoding="utf-8")
            manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps({"testbench": {"path": str(testbench)}}),
                encoding="utf-8",
            )

            adapter = qwen2_hf_case_adapter({"model_type": "qwen2"}, run_dir)

            self.assertEqual(adapter["paths"]["testbench"], str(testbench))
            self.assertIn(
                str(testbench),
                adapter["tools"]["deadlock_axi_check"]["argv"],
            )
