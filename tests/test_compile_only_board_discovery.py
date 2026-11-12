import copy
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from accagent.framework import board_acceptance_contract as contract
from accagent.framework.stage_repair_execute import (
    BOARD_INTEGRATION_REPAIR_SCHEMA, BOARD_SIGNAL_ANALYSIS_REPAIR_SCHEMA,
    board_integration_repair_context, board_integration_prompt_rules,
    current_board_control_source_context,
    exact_board_address_mapping_evidence,
    physical_compute_slot_port_declaration_evidence,
    expand_agent_text_repeats, apply_agent_file_edits, exact_board_agent_task,
    runtime_only_observation_output,
)
from accagent.framework.llm_io import validate_schema
from accagent.framework.stage_llm import (
    _compact_exact_board_generation_kernel_inputs,
    _compact_verilog_module_interface,
    compact_verification_capability_repair_package,
    compact_board_post_vcs_repair_package,
    compact_retry_prompt,
    compact_exact_board_integration_context,
    exact_board_compact_request_errors,
)
from scripts.verification import sample_project_board_interface_impl as impl
from tests import test_sample_project_board_interface_discovery as fixtures
from tests.test_board_acceptance_contract import _case


class CompileOnlyBoardDiscoveryTests(unittest.TestCase):
    def test_current_board_control_context_follows_hash_bound_vivado_cell_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            board_dir = run / "verification" / "board_interface"
            sample_dir = board_dir / "sample_project_sources"
            sample_dir.mkdir(parents=True)
            selected_source = sample_dir / "cfg_controller.v"
            selected_text = (
                "module cfg_controller;\n"
                "  always @(posedge s_axi_aclk) begin\n"
                "    if (write_addr == 6'd25) cfg_data_valid <= 1'b1;\n"
                "  end\n"
                "endmodule\n"
            )
            selected_source.write_text(selected_text, encoding="utf-8")
            unrelated_source = sample_dir / "unrelated.v"
            unrelated_text = "module unrelated; endmodule\n"
            unrelated_source.write_text(unrelated_text, encoding="utf-8")
            facts = {
                "objects": [
                    {
                        "kind": "net",
                        "object_id": "vivado:net:cfg-valid",
                        "path": "/cfg_controller_cfg_data_valid",
                        "members": [
                            {"kind": "pin", "path": "/cfg_controller/cfg_data_valid"},
                            {"kind": "pin", "path": "/cnn_core_0/cfg_data_valid"},
                        ],
                    },
                    {
                        "kind": "pin",
                        "object_id": "vivado:pin:cfg-valid",
                        "path": "/cfg_controller/cfg_data_valid",
                        "owner_path": "/cfg_controller",
                        "properties": {"DIR": "O"},
                    },
                    {
                        "kind": "pin",
                        "object_id": "vivado:pin:cfg-valid-sink",
                        "path": "/cnn_core_0/cfg_data_valid",
                        "owner_path": "/cnn_core_0",
                        "properties": {"DIR": "I"},
                    },
                    {
                        "kind": "cell",
                        "object_id": "vivado:cell:cfg-controller",
                        "path": "/cfg_controller",
                    },
                ]
            }
            facts_path = board_dir / "vivado_board_facts.json"
            facts_path.write_text(json.dumps(facts), encoding="utf-8")
            selected_sha = hashlib.sha256(selected_text.encode()).hexdigest()
            unrelated_sha = hashlib.sha256(unrelated_text.encode()).hexdigest()
            identity = {
                "status": "pass",
                "simulation_hashes_match_source": True,
                "vivado_facts_path": str(facts_path.resolve()),
                "vivado_facts_sha256": hashlib.sha256(facts_path.read_bytes()).hexdigest(),
                "compute_slot_abi": {
                    "control_abi": {
                        "port_classifications": [{
                            "name": "cfg_data_valid",
                            "classification": "control",
                            "direction": "input",
                            "width_bits": 1,
                            "semantic_role": "configuration valid",
                            "evidence_refs": ["vivado:pin:cfg-valid", "vivado:net:cfg-valid"],
                        }]
                    }
                },
                "selected_simulation_source_closure": {"source_files": [
                    {
                        "source_id": "sample-source:cfg-controller",
                        "local_path": str(selected_source),
                        "local_sha256": selected_sha,
                        "sha256": selected_sha,
                        "hashes_match": True,
                        "file_type": "Verilog",
                        "language": "Verilog",
                        "owner_cell_ids": ["vivado:cell:cfg-controller"],
                    },
                    {
                        "source_id": "sample-source:unrelated",
                        "local_path": str(unrelated_source),
                        "local_sha256": unrelated_sha,
                        "sha256": unrelated_sha,
                        "hashes_match": True,
                        "file_type": "Verilog",
                        "language": "Verilog",
                        "owner_cell_ids": ["vivado:cell:other"],
                    },
                ]},
            }

            context = current_board_control_source_context(run, identity)

        self.assertEqual(context["status"], "pass")
        self.assertEqual(
            [row["source_id"] for row in context["sources"]],
            ["sample-source:cfg-controller"],
        )
        self.assertIn("cfg_data_valid <= 1'b1", context["sources"][0]["content"])
        self.assertEqual(
            context["sources"][0]["owner_cells"][0]["control_ports"],
            ["cfg_data_valid"],
        )
        generation_inputs = {
            "verification_capability_repair_package": {
                "exact_board_integration_repair_context": {
                    "adaptive_design_inputs": {
                        "kernel_binding_design_inputs": {
                            "current_sample_board_control_sources": context,
                        }
                    }
                }
            }
        }
        compacted = _compact_exact_board_generation_kernel_inputs(generation_inputs)
        compacted_text = json.dumps(compacted)
        self.assertIn("cfg_data_valid <= 1'b1", compacted_text)
        self.assertIn(selected_sha, compacted_text)

    def test_physical_control_port_projection_uses_hash_bound_source_line(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "slot.v"
            source.write_text(
                "module slot(clk, cfg_done);\n"
                "input wire clk;\n"
                "input wire cfg_done;\n"
                "endmodule\n"
            )
            expected_source = source.read_text()
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            identity = {
                "compute_slot_abi": {
                    "slot_module": "slot",
                    "required_ports": [
                        {"name": "cfg_done", "direction": "input", "width_bits": 1}
                    ],
                    "control_abi": {"port_classifications": [
                        {"name": "cfg_done", "direction": "input", "width_bits": 1}
                    ]},
                },
                "selected_simulation_source_closure": {"source_files": [{
                    "closure_role": "compute_slot_implementation",
                    "declared_modules": ["slot"],
                    "hashes_match": True,
                    "local_path": str(source),
                    "local_sha256": digest,
                    "source_id": "sample:slot",
                }]},
            }
            evidence = physical_compute_slot_port_declaration_evidence(identity)
        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["ports"][0]["source_declarations"][0]["direction"], "input")
        self.assertEqual(evidence["ports"][0]["source_declarations"][0]["line"], 3)
        self.assertEqual(evidence["source_content"], expected_source)
        self.assertEqual(hashlib.sha256(evidence["source_content"].encode()).hexdigest(), digest)

    def test_address_mapping_projection_binds_selected_slot_route_and_translation(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            facts_path = run / "verification/board_interface/vivado_board_facts.json"
            identity_path = run / "verification/board_interface/board_source_identity.json"
            profile_path = run / "input/target_board_profile.json"
            sacg_path = run / "repair/sacg_state.json"
            source_path = run / "board_input.docx"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_bytes(b"board address reference")
            def write_json(path: Path, value: object) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding="utf-8")

            facts = {
                "objects": [
                    {
                        "kind": "cell",
                        "object_id": "vivado:cell:slot",
                        "path": "/slot",
                        "bd_path": "/project/design.bd",
                        "properties": {
                            "CONFIG.ADDR_OFFSET_H": "0x00000008",
                            "CONFIG.ADDR_OFFSET_L": "0x00000000",
                        },
                    },
                    {
                        "kind": "interface_pin",
                        "object_id": "vivado:interface_pin:slot_axi",
                        "path": "/slot/ddr_axi",
                        "properties": {
                            "CONFIG.PROTOCOL": "AXI4",
                            "CONFIG.ADDR_WIDTH": "37",
                            "CONFIG.DATA_WIDTH": "512",
                        },
                        "connected_nets": [{"path": "/slot_axi_net"}],
                    },
                    {
                        "kind": "interface_net",
                        "path": "/slot_axi_net",
                        "members": [
                            {"path": "/slot/ddr_axi"},
                            {"path": "/axi_0/S00_AXI"},
                        ],
                    },
                    {
                        "kind": "interface_pin",
                        "object_id": "vivado:interface_pin:axi_input",
                        "path": "/axi_0/S00_AXI",
                    },
                    {
                        "kind": "cell",
                        "object_id": "vivado:cell:xbar",
                        "path": "/axi_0/xbar",
                        "properties": {
                            "CONFIG.ADDR_WIDTH": "37",
                            "CONFIG.DATA_WIDTH": "512",
                            "CONFIG.M00_A00_BASE_ADDR": "0x0800000000",
                            "CONFIG.M00_A00_ADDR_WIDTH": "35",
                        },
                    },
                    {
                        "kind": "interface_pin",
                        "object_id": "vivado:interface_pin:xbar_m00",
                        "path": "/axi_0/xbar/M00_AXI",
                        "properties": {"CONFIG.ADDR_WIDTH": "37", "CONFIG.DATA_WIDTH": "512"},
                        "connected_nets": [{"path": "/ddr_net"}],
                    },
                    {
                        "kind": "interface_net",
                        "path": "/ddr_net",
                        "members": [
                            {"path": "/axi_0/xbar/M00_AXI"},
                            {"path": "/ddr0/S_AXI"},
                        ],
                    },
                    {
                        "kind": "interface_pin",
                        "object_id": "vivado:interface_pin:ddr",
                        "path": "/ddr0/S_AXI",
                        "properties": {"CONFIG.ADDR_WIDTH": "35", "CONFIG.DATA_WIDTH": "512"},
                    },
                ],
            }
            write_json(facts_path, facts)
            facts_sha = hashlib.sha256(facts_path.read_bytes()).hexdigest()
            identity = {
                "vivado_facts_sha256": facts_sha,
                "compute_slot_abi": {"selected_cell_id": "vivado:cell:slot"},
            }
            write_json(identity_path, identity)
            profile = {
                "memory_system": {
                    "address_map": {"ddr_base": "0x2800000000"},
                    "axi_addr_width_bits": 37,
                    "axi_data_width_bits": 512,
                }
            }
            write_json(profile_path, profile)
            write_json(
                sacg_path,
                {
                    "evidence": {
                        "field": "board.reference_example_pcie_address_translation",
                        "id": "evidence.field.0010",
                        "source": str(source_path),
                        "excerpt": "0x2000000000 + 0x0800000000 = 0x2800000000",
                        "value": {
                            "channel0_pcie_base": "0x2000000000",
                            "example_ddr0_local_base": "0x0800000000",
                            "example_pcie_ddr0_start": "0x2800000000",
                        },
                    }
                },
            )

            projection = exact_board_address_mapping_evidence(run, identity, profile)

        self.assertEqual(projection["status"], "ready")
        self.assertEqual(projection["selected_compute_slot"]["slot_local_base"], "0x800000000")
        self.assertEqual(projection["vivado_connected_axi_routes"][0]["interconnect_input"], "/axi_0/S00_AXI")
        self.assertEqual(projection["translation_reference_examples"][0]["source_sha256"],
                         hashlib.sha256(b"board address reference").hexdigest())
        self.assertTrue(projection["candidate_translation"]["reference_matches_derived_host_window_base"])
        address_contract = projection["slot_axi_address_contract"]
        self.assertEqual(address_contract["status"], "bound")
        self.assertEqual(address_contract["adapter_address_domain"], "compute_slot_axi")
        self.assertEqual(address_contract["slot_axi_addr_width_bits"], 37)
        self.assertEqual(address_contract["profile_global_ddr_base"], "0x2800000000")
        self.assertFalse(address_contract["profile_global_base_fits_slot_axi_width"])
        self.assertEqual(
            address_contract["matching_interconnect_segments"][0]["base_address"],
            "0x0800000000",
        )
        self.assertEqual(
            address_contract["host_visible_mapping"]["derived_host_window_base"],
            "0x2000000000",
        )

    def test_address_mapping_projection_rejects_unbound_vivado_facts(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            facts_path = run / "verification/board_interface/vivado_board_facts.json"
            facts_path.parent.mkdir(parents=True)
            facts_path.write_text(json.dumps({"objects": []}), encoding="utf-8")
            identity = {
                "vivado_facts_sha256": "stale-facts-hash",
                "compute_slot_abi": {"selected_cell_id": "vivado:cell:slot"},
            }

            projection = exact_board_address_mapping_evidence(
                run,
                identity,
                {"memory_system": {"address_map": {"ddr_base": "0x2800000000"}}},
            )

        self.assertEqual(projection["status"], "unavailable")
        self.assertIn("current-run board identity does not bind the Vivado facts hash",
                      projection["blockers"])

    def test_compact_board_context_preserves_address_mapping_evidence(self):
        evidence = {"status": "ready", "selected_compute_slot": {"cell_id": "cell-1"}}
        compact = compact_exact_board_integration_context(
            {"adaptive_design_inputs": {"exact_board_address_mapping_evidence": evidence}}
        )
        self.assertEqual(
            compact["adaptive_design_inputs"]["exact_board_address_mapping_evidence"],
            evidence,
        )

        post_vcs = compact_board_post_vcs_repair_package(
            {
                "current_board_vcs_feedback": {
                    "runner_report": {"value": {"compile": {"status": "fail"}}}
                },
                "exact_board_integration_repair_context": {
                    "adaptive_design_inputs": {
                        "exact_board_address_mapping_evidence": evidence
                    }
                },
            }
        )
        self.assertEqual(
            post_vcs["exact_board_integration_repair_context"]["adaptive_design_inputs"][
                "exact_board_address_mapping_evidence"
            ],
            evidence,
        )

    def test_board_prompt_requires_current_address_translation_evidence(self):
        prompt = "\n".join(board_integration_prompt_rules("create"))
        self.assertIn("exact_board_address_mapping_evidence", prompt)
        self.assertIn("must not be driven on a narrower slot AXI port", prompt)
        self.assertIn("slot_axi_address_contract.status is bound", prompt)
        self.assertIn("using slot_local_base plus allocated byte offsets", prompt)
        self.assertIn("Keep host_visible_mapping separate", prompt)

    def test_full_semantic_policy_requests_exact_board_ddr_runtime(self):
        with patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "full_semantic_simulation"}):
            rules = "\n".join(board_integration_prompt_rules("create"))
            task = exact_board_agent_task("create")

        self.assertIn("full_semantic_simulation", rules)
        self.assertIn("exact_sample_physical_ddr", rules)
        self.assertIn("real target-model Transformer-block weight catalog", rules)
        self.assertIn("exact sample-board AXI/DDR runtime integration", task)
        self.assertNotIn("Do not run the generated simulation executable", rules)

    def test_nested_experiment_uses_run_local_tool_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            experiment = Path(tmp) / "experiment"
            run = experiment / "B0/run"
            prior_run = Path(tmp) / "prior_run"
            for root in (experiment, run, prior_run):
                (root / "input").mkdir(parents=True)
                (root / "input/tool_profile.json").write_text('{"tools": []}\n')
            profiles = contract._candidate_tool_profiles(
                run / "verification/board_interface/board_source_identity.json",
                run / "verification/board_simulation/board_simulation_manifest.json",
                prior_run / "verification/board_interface/vivado_board_facts.json",
            )
            self.assertEqual(profiles, [(run / "input/tool_profile.json").resolve()])

    def test_runtime_observation_keeps_manifest_referenced_generated_testbench(self):
        run = Path("/run")
        tb = run / "generated/board_integration/board_compile_tb.sv"
        output = {
            "status": "ready_to_apply",
            "adaptive_observation_decision": {
                "mode": "deepen_simulation_observation",
            },
            "file_edits": [
                {
                    "path": str(run / "generated/board_integration/adapter.sv"),
                    "operation": "create",
                    "content": "module adapter; endmodule\n",
                },
                {
                    "path": str(tb),
                    "operation": "create",
                    "content": "module board_compile_tb; endmodule\n",
                },
                {
                    "path": str(run / "generated/memory/dut_weight_binding_manifest.json"),
                    "operation": "create",
                    "json_content": {
                        "board_simulation_preflight_plan": {
                            "testbench": {
                                "source": {
                                    "path": str(tb),
                                    "source_id": "generated-board-compile-tb",
                                    "role": "generated_accelerator",
                                }
                            }
                        }
                    },
                },
            ],
        }
        normalized = runtime_only_observation_output(output)
        self.assertEqual(len(normalized["file_edits"]), 3)

    def test_runtime_observation_drops_existing_observation_only_testbench_edit(self):
        output = {
            "status": "ready_to_apply",
            "adaptive_observation_decision": {
                "mode": "deepen_simulation_observation",
            },
            "file_edits": [
                {
                    "path": "/run/generated/board_integration/debug_tb.sv",
                    "operation": "replace",
                    "content": "module debug_tb; endmodule\n",
                },
            ],
        }
        normalized = runtime_only_observation_output(output)
        self.assertEqual(normalized["file_edits"], [])

    def test_compile_only_compact_request_omits_runtime_observation_rules(self):
        with patch("accagent.framework.stage_llm.exact_board_compact_request_errors", return_value=[]):
            prompt = compact_retry_prompt(
                "exact_board_integration_generation_agent", "repair_execution",
                exact_board_agent_task("repair"),
                {"verification_capability_repair_package": {
                    "verification_scope": "board_axi_ddr_closure",
                    "current_board_vcs_feedback": {"status": "ready"},
                }}, BOARD_INTEGRATION_REPAIR_SCHEMA,
                prompt_rules=board_integration_prompt_rules("repair"),
            )
        self.assertIn("entire certified family", prompt)
        self.assertIn("repeat_expansions", prompt)
        self.assertIn("replace the complete run-local adapter", prompt)
        self.assertIn("do not use tie-offs, empty stubs", prompt)
        self.assertNotIn("Layer-3 observation must be unconditional", prompt)
        self.assertNotIn("current_signal_epoch is the only dynamic hardware evidence", prompt)
        self.assertIn("scalar field_observations only from current_board_vcs_feedback", prompt)
        self.assertIn("copy every old_text anchor byte-for-byte", prompt)
        self.assertIn("Do not resend unchanged RTL", prompt)
        self.assertIn("checking the supplied declarations and references", prompt)

    def test_compile_only_repair_schema_accepts_interface_evidence_and_empty_replace_text(self):
        output = {
            "agent": "exact_board_integration_generation_agent",
            "stage": "repair_execution",
            "status": "ready_to_apply",
            "summary": "Fix the current kernel interface binding.",
            "root_cause": "The adapter names do not match the certified kernel interface.",
            "causal_prediction": {
                "intervention_family": "Correct the source-bound interface connection.",
                "target_frontier_id": "vcs_compile_tile_service_binding",
                "expected_progress_changes": [
                    {"metric": "VCS compile", "relation": "reach_at_least", "value": 1}
                ],
                "falsified_if": "The current VCS compile still reports an undefined port.",
                "evidence_refs": ["/current_compiler_module_interfaces/0/ordered_port_groups"],
            },
            "adaptive_observation_decision": {
                "schema_version": "spatialaccagent.adaptive_observation_routing.v1",
                "mode": "direct_tool_failure",
                "frontier_id": "vcs_compile_tile_service_binding",
                "evidence_refs": ["/current_board_vcs_feedback/diagnosis"],
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/failure_evidence/first_real_error",
                        "observed_value": "Error-[UPIMI-E] Undefined port in module instantiation",
                        "semantic_role": "error",
                        "interpretation": "VCS rejected a kernel port name.",
                    },
                    {
                        "evidence_pointer": "/current_compiler_module_interfaces/0/ordered_port_groups/0/name",
                        "observed_value": "io_tile_0_request_valid",
                        "semantic_role": "contract",
                        "interpretation": "The current kernel interface exposes this tile client port.",
                    },
                ],
            },
            "file_edits": [
                {
                    "path": "/run/generated/board_integration/compute_slot_adapter.sv",
                    "operation": "replace_text",
                    "expected_sha256": "current-source-hash",
                    "text_replacements": [{"old_text": "old port", "new_text": "current port"}],
                    "rationale": "Bind the adapter to the current kernel interface.",
                }
            ],
            "requested_validation": [],
            "blocked_reasons": [],
            "approval_required_for": [],
        }

        validate_schema(output, BOARD_SIGNAL_ANALYSIS_REPAIR_SCHEMA, "exact_board_integration_generation_agent")

    def test_agent_numbered_source_expansion_keeps_literal_sv_braces(self):
        edit = {"path": "adapter.sv", "operation": "replace_text", "content": "",
                "text_replacements": [{"old_text": "// ports", "new_text": "@@PORTS@@"}],
                "repeat_expansions": [{"marker": "@@PORTS@@", "first_index": 2,
                    "last_index": 4, "template": "wire [7:0] p_{index} = {a[{index_plus_10}], b};\n"}]}
        expanded = expand_agent_text_repeats(edit)
        self.assertEqual(expanded["text_replacements"][0]["new_text"],
                         "".join(f"wire [7:0] p_{i} = {{a[{i + 10}], b}};\n" for i in range(2, 5)))
        self.assertNotIn("repeat_expansions", expanded)
        self.assertEqual(edit["text_replacements"][0]["new_text"], "@@PORTS@@")
        for bad in [dict(edit, path="manifest.json"),
                    dict(edit, content="@@PORTS@@"),
                    dict(edit, repeat_expansions=[dict(edit["repeat_expansions"][0], last_index=100_000)])]:
            with self.assertRaises(ValueError):
                expand_agent_text_repeats(bad)

    def test_agent_numbered_source_expansion_uses_normal_patch_executor(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp).resolve()
            target = run / "generated/board_integration/adapter.sv"
            target.parent.mkdir(parents=True)
            target.write_text("module Adapter;\n// ports\nendmodule\n")
            prior_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            result = apply_agent_file_edits({"status": "ready_to_apply", "file_edits": [{
                "path": str(target), "operation": "replace_text", "content": "",
                "expected_sha256": prior_hash,
                "text_replacements": [{"old_text": "// ports", "new_text": "@@PORTS@@"}],
                "repeat_expansions": [{"marker": "@@PORTS@@", "first_index": 0,
                    "last_index": 36026, "template": "wire [31:0] scale_{index}; // loadable channel metadata configuration storage connection\n"}],
            }]}, run, run / "repair_execution", allowed_exact_files={target},
                allow_board_integration=True, require_exact_source_hash=True)
            self.assertEqual(result["status"], "pass", result)
            source = target.read_text()
            self.assertIn("wire [31:0] scale_36026;", source)
            self.assertEqual(source.count("wire [31:0] scale_"), 36027)
            self.assertGreater(len(source.encode()), 2_000_000)
            self.assertNotIn("@@PORTS@@", source)

            # An ordinary oversized edit still uses the existing bound.
            rejected = apply_agent_file_edits({"status": "ready_to_apply", "file_edits": [{
                "path": str(target), "operation": "replace", "content": source + "// changed\n",
                "expected_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }]}, run, run / "repair_execution", allowed_exact_files={target},
                allow_board_integration=True, require_exact_source_hash=True)
            self.assertIn("implementation patch exceeds the 2 MB bounded-repair limit", rejected["blockers"])
            self.assertEqual(target.read_text(), source)

            # A small anchored edit to an already large board adapter is not
            # a multi-megabyte LLM payload and must remain executable.
            edited = apply_agent_file_edits({"status": "ready_to_apply", "file_edits": [{
                "path": str(target), "operation": "replace_text",
                "expected_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "text_replacements": [{"old_text": "wire [31:0] scale_36026;",
                                       "new_text": "wire [31:0] scale_36026 = cfg;"}],
            }]}, run, run / "repair_execution", allowed_exact_files={target},
                allow_board_integration=True, require_exact_source_hash=True)
            self.assertEqual(edited["status"], "pass", edited)
            self.assertIn("scale_36026 = cfg", target.read_text())

    def test_compile_only_repair_schema_accepts_interface_evidence_and_omitted_empty_content(self):
        output = {
            "agent": "exact_board_integration_generation_agent",
            "stage": "repair_execution",
            "status": "ready_to_apply",
            "summary": "Fix the current kernel interface binding.",
            "root_cause": "The adapter names do not match the certified kernel interface.",
            "causal_prediction": {
                "intervention_family": "Correct the source-bound interface connection.",
                "target_frontier_id": "vcs_compile_tile_service_binding",
                "expected_progress_changes": [
                    {"metric": "VCS compile", "relation": "reach_at_least", "value": 1}
                ],
                "falsified_if": "The current VCS compile still reports an undefined port.",
                "evidence_refs": ["/current_compiler_module_interfaces/0/ordered_port_groups"],
            },
            "adaptive_observation_decision": {
                "schema_version": "spatialaccagent.adaptive_observation_routing.v1",
                "mode": "direct_tool_failure",
                "frontier_id": "vcs_compile_tile_service_binding",
                "evidence_refs": ["/current_board_vcs_feedback/diagnosis"],
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/failure_evidence/first_real_error",
                        "observed_value": "Error-[UPIMI-E] Undefined port in module instantiation",
                        "semantic_role": "error",
                        "interpretation": "VCS rejected a kernel port name.",
                    },
                    {
                        "evidence_pointer": "/current_compiler_module_interfaces/0/ordered_port_groups/0/name",
                        "observed_value": "io_tile_0_request_valid",
                        "semantic_role": "contract",
                        "interpretation": "The current kernel interface exposes this tile client port.",
                    },
                ],
            },
            "file_edits": [
                {
                    "path": "/run/generated/board_integration/compute_slot_adapter.sv",
                    "operation": "replace_text",
                    "expected_sha256": "current-source-hash",
                    "text_replacements": [{"old_text": "old port", "new_text": "current port"}],
                    "rationale": "Bind the adapter to the current kernel interface.",
                }
            ],
            "requested_validation": [],
            "blocked_reasons": [],
            "approval_required_for": [],
        }

        validate_schema(
            output,
            BOARD_SIGNAL_ANALYSIS_REPAIR_SCHEMA,
            "exact_board_integration_generation_agent",
        )

    def test_compile_repair_keeps_kernel_interface_and_scale_design_inputs(self):
        adaptive = {
            "kernel_binding_design_inputs": {
                "certified_top_sources": [{"interface_contract": {
                    "ordered_port_groups": [{"name": "io_scale", "width": 32}],
                }}],
                "current_generator_sources": [{"content": "scale source semantics"}],
            },
            "target_board_profile": {"value": {"memory_system": {"address_map": {"ddr_base": "0x2800000000"}}}},
            "shared_board_source_index": {"rows": [{"source_id": "board-source"}]},
            "exact_board_source_identity": {"value": {"status": "pass"}},
            "model_derived_memory_layout": {"value": {"weight_storage_terms": ["scales"]}},
            "full_weight_image_manifest": {"value": {"scale_consumer_binding": "qkv"}},
        }
        result = compact_board_post_vcs_repair_package({
            "current_board_vcs_feedback": {"runner_report": {"value": {
                "compile": {"status": "fail"},
            }}},
            "exact_board_integration_repair_context": {"adaptive_design_inputs": copy.deepcopy(adaptive)},
        })
        self.assertEqual(result["exact_board_integration_repair_context"]["adaptive_design_inputs"], adaptive)

    def test_deterministic_preflight_repair_can_create_its_missing_manifest(self):
        manifest_authority_path = (
            "accagent/runs/test_run/generated/memory/dut_weight_binding_manifest.json"
        )
        manifest_path = str((Path.cwd() / manifest_authority_path).resolve())
        source_path = "/run/generated/board_integration/accelerator.sv"
        source_text = "module generated_accelerator; endmodule\n"
        source_sha256 = hashlib.sha256(source_text.encode()).hexdigest()
        inputs = {
            "verification_capability_repair_package": {
                "generation_phase_contract": {
                    "status": "repair_deterministic_preflight",
                    "current_preflight_feedback_ready": True,
                },
                "current_board_preflight_feedback": {
                    "status": "ready",
                    "blockers": ["the binding manifest is missing"],
                },
                "exact_board_integration_repair_context": {
                    "status": "ready",
                    "required_binding_manifest": manifest_path,
                    "required_generated_root": "/run/generated/board_integration",
                },
                "repair_source_bundle": {
                    "documents": [
                        {
                            "path": source_path,
                            "sha256": source_sha256,
                            "content": source_text,
                        }
                    ],
                    "editable_contract": {
                        "allowed_exact_files": [manifest_authority_path],
                        "current_board_source_files": [
                            {
                                "path": source_path,
                                "sha256": source_sha256,
                            }
                        ],
                        "board_manifest_rewrite_authority": {
                            "target_file": {"path": manifest_authority_path}
                        },
                    },
                },
            }
        }
        certified_top = (
            "module CertifiedTop(\n"
            "  input clock,\n"
            "  input [31:0] data,\n"
            "  output [31:0] result\n"
            ");\n"
            + ("wire unused;\n" * 80_000)
            + "endmodule\n"
        )
        inputs["verification_capability_repair_package"][
            "exact_board_integration_repair_context"
        ]["adaptive_design_inputs"] = {
            "kernel_binding_design_inputs": {
                "certified_top_sources": [
                    {
                        "path": "/run/generated/KernelTop.sv",
                        "sha256": hashlib.sha256(certified_top.encode()).hexdigest(),
                        "size_bytes": len(certified_top.encode()),
                        "content": certified_top,
                    }
                ],
                "current_generator_sources": [],
            }
        }
        inputs["verification_capability_repair_package"][
            "repair_source_bundle"
        ]["editable_contract"]["board_manifest_rewrite_authority"] = {
            "target_file": {"path": manifest_authority_path},
            "stage2_vcs_compile_authority": {
                "module_declaration": certified_top,
            }
        }
        prompt = compact_retry_prompt(
            "exact_board_integration_generation_agent",
            "repair_execution",
            "Create the missing binding manifest from current exact-board evidence",
            inputs,
            BOARD_INTEGRATION_REPAIR_SCHEMA,
        )
        self.assertIn(manifest_path, prompt)
        self.assertIn("repair_deterministic_preflight", prompt)
        self.assertLess(len(prompt.encode()), 100_000)
        self.assertIn('"port_count":3', prompt)
        self.assertIn('"numeric_port_ranges_expand_losslessly":true', prompt)
        self.assertNotIn("wire unused;", prompt)
        preflight_rules = "\n".join(board_integration_prompt_rules("preflight_repair"))
        self.assertIn("Certified kernels already supplied by the current compile authority", preflight_rules)
        self.assertIn("sample-source IDs that the selected compile plan does not include", preflight_rules)

    def test_preflight_accepts_hash_bound_read_only_adapter_projection(self):
        manifest_path = str(
            (Path.cwd() / "accagent/runs/test_run/generated/memory/weights.json").resolve()
        )
        adapter_path = str(
            (Path.cwd() / "accagent/runs/test_run/generated/board_integration/adapter.sv").resolve()
        )
        adapter = (
            "`timescale 1ns/1ps\n\nmodule compute_slot_adapter (\n"
            "  input wire clock,\n"
            "  output wire ready\n"
            ");\n"
            + "  wire unused;\n" * 5000
            + "endmodule\n"
        )
        digest = hashlib.sha256(adapter.encode()).hexdigest()
        compacted = _compact_exact_board_generation_kernel_inputs({
            "verification_capability_repair_package": {
                "generation_phase_contract": {"status": "repair_deterministic_preflight"},
                "current_board_preflight_feedback": {"status": "ready"},
                "exact_board_integration_repair_context": {
                    "status": "ready",
                    "required_binding_manifest": manifest_path,
                    "adaptive_design_inputs": {
                        "kernel_binding_design_inputs": {}
                    },
                },
                "repair_source_bundle": {
                    "editable_contract": {
                        "allowed_exact_files": [manifest_path],
                        "current_board_source_files": [{"path": adapter_path, "sha256": digest}],
                        "board_manifest_rewrite_authority": {
                            "target_file": {"path": manifest_path}
                        },
                    },
                    "documents": [
                        {"path": adapter_path, "sha256": digest, "content": adapter},
                        {"path": manifest_path, "sha256": "a" * 64, "content": "{}\n"},
                    ],
                },
            }
        })
        package = compacted["verification_capability_repair_package"]

        self.assertEqual(exact_board_compact_request_errors(compacted), [])
        projected = package["repair_source_bundle"]["documents"][0]
        self.assertNotIn("content", projected)
        self.assertEqual(projected["content_projection"]["source_sha256"], digest)
        projected["content_projection"]["source_sha256"] = "b" * 64
        self.assertIn(
            "deterministic-preflight projected board source hash differs: " + adapter_path,
            exact_board_compact_request_errors(compacted),
        )

    def test_large_certified_top_is_projected_to_complete_ordered_port_ranges(self):
        ports = ["  input clock,"]
        ports.extend(f"  input [7:0] io_weight_{index}," for index in range(2048))
        ports.extend(f"  output [31:0] io_result_{index}," for index in range(64))
        source_text = "module KernelTop(\n" + "\n".join(ports) + "\n);\nendmodule\n"
        interface = _compact_verilog_module_interface(source_text)
        self.assertEqual(interface["module"], "KernelTop")
        self.assertEqual(interface["port_count"], 2113)
        self.assertTrue(interface["policy"]["port_order_preserved"])
        self.assertEqual(
            interface["ordered_port_groups"][1],
            {
                "direction": "input",
                "packed_width": "[7:0]",
                "name_pattern": "io_weight_{index}",
                "first_index": 0,
                "last_index": 2047,
                "count": 2048,
                "order_start": 1,
            },
        )

        import hashlib

        source = {
            "path": "/run/generated/KernelTop.sv",
            "sha256": hashlib.sha256(source_text.encode()).hexdigest(),
            "size_bytes": len(source_text.encode()),
            "content": source_text,
        }
        inputs = {
            "verification_capability_repair_package": {
                "generation_phase_contract": {
                    "status": "generation_required_before_probe"
                },
                "exact_board_integration_repair_context": {
                    "status": "ready",
                    "required_binding_manifest": "/run/generated/manifest.json",
                    "adaptive_design_inputs": {
                        "kernel_binding_design_inputs": {
                            "status": "design_required",
                            "certified_top_sources": [source],
                            "current_generator_sources": [],
                        }
                    },
                },
                "repair_source_bundle": {
                    "editable_contract": {
                        "board_manifest_rewrite_authority": {
                            "stage2_vcs_compile_authority": {
                                "module_declaration": (
                                    source_text + ("// compile-plan detail\n" * 1000)
                                ),
                            }
                        }
                    }
                },
            }
        }
        compacted = _compact_exact_board_generation_kernel_inputs(inputs)
        projected = compacted["verification_capability_repair_package"][
            "exact_board_integration_repair_context"
        ]["adaptive_design_inputs"]["kernel_binding_design_inputs"][
            "certified_top_sources"
        ][0]
        self.assertNotIn("content", projected)
        self.assertEqual(projected["sha256"], source["sha256"])
        self.assertEqual(projected["interface_contract"]["port_count"], 2113)
        prompt = compact_retry_prompt(
            "exact_board_integration_generation_agent",
            "repair_execution",
            "Create the exact-board adapter",
            inputs,
            BOARD_INTEGRATION_REPAIR_SCHEMA,
        )
        self.assertLess(len(prompt.encode()), 100_000)
        self.assertNotIn("io_weight_2047", prompt)
        self.assertIn('"last_index":2047', prompt)
        self.assertIn('"source_bytes":', prompt)
        self.assertIn('"numeric_port_ranges_expand_losslessly":true', prompt)

    def test_compact_interface_accepts_multiple_explicit_ansi_ports_per_line(self):
        source_text = (
            "module BoardAdapter (\n"
            " input wire clk_300M, input wire clk_600M,\n"
            " input wire [703:0] cfg_data, input wire cfg_data_valid, input wire cfg_done,\n"
            " output logic [3:0] ddr_awid, output logic [36:0] ddr_awaddr\n"
            ");\nendmodule\n"
        )

        interface = _compact_verilog_module_interface(source_text)

        self.assertEqual(interface["module"], "BoardAdapter")
        self.assertEqual(interface["port_count"], 7)
        self.assertEqual(
            [
                (port["direction"], port.get("packed_width", ""), port.get("name"))
                for port in interface["ordered_port_groups"]
            ],
            [
                ("input", "", "clk_300M"),
                ("input", "", "clk_600M"),
                ("input", "[703:0]", "cfg_data"),
                ("input", "", "cfg_data_valid"),
                ("input", "", "cfg_done"),
                ("output", "[3:0]", "ddr_awid"),
                ("output", "[36:0]", "ddr_awaddr"),
            ],
        )

    def test_large_parameterized_generated_adapter_is_compacted_with_its_ansi_abi(self):
        adapter = (
            "module BoardAdapter #(\n"
            "  parameter integer DEPTH = 16,\n"
            "  parameter integer WIDTH = $clog2((DEPTH + 1))\n"
            ") (\n"
            "  input logic clock,\n"
            "  input logic [WIDTH-1:0] address,\n"
            "  output logic ready\n"
            ");\n"
            + "  logic unused;\n" * 5000
            + "endmodule\n"
        )
        adapter_path = "/run/generated/board_integration/board_compute_slot_adapter.sv"
        digest = hashlib.sha256(adapter.encode()).hexdigest()
        compacted = _compact_exact_board_generation_kernel_inputs(
            {
                "verification_capability_repair_package": {
                    "exact_board_integration_repair_context": {
                        "adaptive_design_inputs": {
                            "kernel_binding_design_inputs": {
                                "certified_top_sources": [],
                                "current_generator_sources": [],
                            }
                        }
                    },
                    "repair_source_bundle": {
                        "documents": [
                            {
                                "path": adapter_path,
                                "sha256": digest,
                                "content": adapter,
                            }
                        ]
                    }
                }
            }
        )

        projected = compacted["verification_capability_repair_package"][
            "repair_source_bundle"
        ]["documents"][0]
        self.assertNotIn("content", projected)
        self.assertEqual(projected["content_projection"]["source_sha256"], digest)
        self.assertEqual(
            projected["content_projection"]["interface_contract"]["module"],
            "BoardAdapter",
        )
        self.assertEqual(
            projected["content_projection"]["interface_contract"]["port_count"],
            3,
        )

    def test_repeated_compaction_preserves_selected_board_source_bodies(self):
        sources = [
            {'path': '/sources/top.v', 'sha256': 'a' * 64, 'closure_role': 'exact_sample_top'},
            {'path': '/sources/slot.v', 'sha256': 'b' * 64, 'closure_role': 'compute_slot_implementation'},
        ]
        documents = [dict(row, content=f'module selected_{index}; endmodule\n', truncated=False)
                     for index, row in enumerate(sources)]
        package = {
            'verification_scope': 'board_axi_ddr_closure',
            'generation_phase_contract': {'status': 'generation_required_before_probe'},
            'exact_board_integration_repair_context': {
                'status': 'ready',
                'required_binding_manifest': '/generated/memory/dut_weight_binding_manifest.json',
                'adaptive_design_inputs': {
                    'kernel_binding_design_inputs': {
                        'status': 'design_required',
                        'current_generator_sources': [{'path': '/generated/Block.scala',
                                                      'content': 'operator.io.tile <> io.tile(0)'}],
                    },
                    'exact_board_source_identity': {'value': {
                        'selected_simulation_source_closure': {'source_files': sources},
                    }},
                },
            },
            'repair_source_bundle': {'documents': documents, 'editable_contract': {}},
        }
        result = compact_verification_capability_repair_package(package)
        for _ in range(2):
            result = compact_verification_capability_repair_package(result)
            contents = {row['path']: row.get('content')
                        for row in result['repair_source_bundle']['documents']}
            for row in documents:
                self.assertEqual(row['content'], contents.get(row['path']))
        prompt = compact_retry_prompt(
            'exact_board_integration_generation_agent', 'repair_execution', 'Create the connected design',
            {'verification_capability_repair_package': result}, BOARD_INTEGRATION_REPAIR_SCHEMA,
        )
        self.assertIn('module selected_0', prompt)
        self.assertIn('module selected_1', prompt)
        self.assertIn('operator.io.tile <> io.tile(0)', prompt)

    def test_exact_board_prompt_projects_only_reusable_template_bodies(self):
        generated_content = "object GeneratedAxiDdrTop { val layers = 24 }\n"
        generated_sha = hashlib.sha256(generated_content.encode()).hexdigest()
        template_content = (
            "package spatialaccagent.templates\n"
            "class WeightTileCache extends Module {\n"
            "  val io = IO(new Bundle {\n"
            "    val request = Input(UInt(32.W))\n"
            "    val response = Output(UInt(64.W))\n"
            "  })\n"
            "}\n"
            + "// reusable implementation body\n" * 3000
        )
        template_sha = hashlib.sha256(template_content.encode()).hexdigest()
        inputs = {
            "verification_capability_repair_package": {
                "generation_phase_contract": {
                    "status": "generation_required_before_probe"
                },
                "exact_board_integration_repair_context": {
                    "status": "ready",
                    "required_binding_manifest": "/run/generated/manifest.json",
                    "adaptive_design_inputs": {
                        "kernel_binding_design_inputs": {
                            "certified_top_sources": [],
                            "current_generator_sources": [
                                {
                                    "path": "/run/generated/chisel/GeneratedAxiDdrTop.scala",
                                    "sha256": generated_sha,
                                    "content": generated_content,
                                },
                                {
                                    "path": "/run/generated/chisel/src/main/scala/spatialaccagent/templates/WeightTileCache.scala",
                                    "sha256": template_sha,
                                    "content": template_content,
                                },
                            ],
                        }
                    },
                }
            }
        }

        prompt = compact_retry_prompt(
            "exact_board_integration_generation_agent",
            "repair_execution",
            "Create the exact-board adapter",
            inputs,
            BOARD_INTEGRATION_REPAIR_SCHEMA,
        )

        self.assertLess(len(prompt.encode()), 100_000)
        self.assertIn(generated_content.strip(), prompt)
        self.assertNotIn("reusable implementation body", prompt)
        self.assertIn(template_sha, prompt)
        self.assertIn('"name":"WeightTileCache"', prompt)
        self.assertIn('"val request = Input(UInt(32.W))"', prompt)
        self.assertIn('"full_hash_bound_source_remains_on_disk":true', prompt)

    def test_exact_board_prompt_keeps_certified_kernel_owner_template_body(self):
        import hashlib

        kernel_source = (
            "module GPT2PreLNBlock (\n"
            "  input clock\n"
            ");\n"
            "endmodule\n"
        )
        kernel_digest = hashlib.sha256(kernel_source.encode()).hexdigest()
        template_source = (
            "package spatialaccagent.templates\n"
            "class GPT2PreLNBlock extends DecoderBlock {\n"
            "  qkv.io.tile <> io.tile(0)\n"
            "  ffn.io.upWeight <> io.ffnUpWeight\n"
            "}\n"
        )
        template_digest = hashlib.sha256(template_source.encode()).hexdigest()
        reusable_source = "class ReusableHelper { val lanes = 16 }\n"
        reusable_digest = hashlib.sha256(reusable_source.encode()).hexdigest()
        inputs = {
            "verification_capability_repair_package": {
                "generation_phase_contract": {
                    "status": "generation_required_before_probe"
                },
                "exact_board_integration_repair_context": {
                    "status": "ready",
                    "required_binding_manifest": "/run/generated/manifest.json",
                    "adaptive_design_inputs": {
                        "kernel_binding_design_inputs": {
                            "certified_top_sources": [{
                                "path": "/run/GPT2PreLNBlock.sv",
                                "sha256": kernel_digest,
                                "content": kernel_source,
                            }],
                            "current_generator_sources": [
                                {
                                    "path": "/run/templates/DecoderBlock.scala",
                                    "sha256": template_digest,
                                    "content": template_source,
                                },
                                {
                                    "path": "/run/templates/ReusableHelper.scala",
                                    "sha256": reusable_digest,
                                    "content": reusable_source,
                                },
                            ],
                        }
                    }
                }
            }
        }

        prompt = compact_retry_prompt(
            "exact_board_integration_generation_agent",
            "repair_execution",
            "Create the exact-board adapter",
            inputs,
            BOARD_INTEGRATION_REPAIR_SCHEMA,
        )
        kernel_inputs = _compact_exact_board_generation_kernel_inputs(inputs)[
            "verification_capability_repair_package"
        ]["exact_board_integration_repair_context"]["adaptive_design_inputs"][
            "kernel_binding_design_inputs"
        ]
        owner, reusable = kernel_inputs["current_generator_sources"]

        self.assertEqual(owner["content"], template_source)
        self.assertEqual(owner["implementation_contract_for"], ["GPT2PreLNBlock"])
        self.assertEqual(owner["implementation_source_sha256"], template_digest)
        self.assertNotIn("content", reusable)
        self.assertEqual(reusable["content_projection"]["source_sha256"], reusable_digest)
        self.assertIn("qkv.io.tile <> io.tile(0)", prompt)
        self.assertIn("ffn.io.upWeight <> io.ffnUpWeight", prompt)
        self.assertNotIn("class ReusableHelper", prompt)

    def test_exact_board_prompt_keeps_reachable_template_consumers(self):
        kernel = "module Kernel(input clock); endmodule\n"
        templates = {
            "Top.scala": "class Kernel extends Base { val op = new Op }\n",
            "Base.scala": "class Base { val helper = new Helper }\n",
            "Op.scala": "class Op { val weight = new WeightConsumer }\n",
            "WeightConsumer.scala": "class WeightConsumer { val packing = 4 }\n",
            "Helper.scala": "class Helper {}\n",
            "Other.scala": "class Other {}\n",
        }
        sources = [
            {"path": f"/run/templates/{name}", "content": content,
             "sha256": hashlib.sha256(content.encode()).hexdigest()}
            for name, content in templates.items()
        ]
        inputs = {"verification_capability_repair_package": {
            "exact_board_integration_repair_context": {"adaptive_design_inputs": {
                "kernel_binding_design_inputs": {
                    "certified_top_sources": [{"path": "/run/Kernel.sv", "content": kernel,
                        "sha256": hashlib.sha256(kernel.encode()).hexdigest()}],
                    "current_generator_sources": sources,
                }
            }}
        }}
        result = _compact_exact_board_generation_kernel_inputs(inputs)
        retained = result["verification_capability_repair_package"][
            "exact_board_integration_repair_context"]["adaptive_design_inputs"][
                "kernel_binding_design_inputs"]["current_generator_sources"]
        by_name = {Path(row["path"]).name: row for row in retained}
        for name in ("Top.scala", "Base.scala", "Op.scala", "WeightConsumer.scala", "Helper.scala"):
            self.assertEqual(by_name[name]["content"], templates[name])
        self.assertNotIn("content", by_name["Other.scala"])

    def test_read_only_generated_board_rtl_is_projected_but_manifest_stays_editable(self):
        adapter_content = (
            "`timescale 1ns/1ps\n\nmodule compute_slot_adapter (\n"
            "  input wire clk,\n"
            "  input wire [31:0] data\n"
            ");\n"
            + "  // generated internal logic\n" * 3000
            + "endmodule\n"
        )
        adapter_sha = hashlib.sha256(adapter_content.encode()).hexdigest()
        manifest_content = '{"schema_version":"test"}\n'
        manifest_sha = hashlib.sha256(manifest_content.encode()).hexdigest()
        adapter_path = "/run/generated/board_integration/compute_slot_adapter.sv"
        manifest_path = "/run/generated/memory/dut_weight_binding_manifest.json"
        inputs = {
            "verification_capability_repair_package": {
                "exact_board_integration_repair_context": {
                    "adaptive_design_inputs": {
                        "kernel_binding_design_inputs": {}
                    }
                },
                "repair_source_bundle": {
                    "editable_contract": {"allowed_exact_files": [manifest_path]},
                    "documents": [
                        {
                            "path": adapter_path,
                            "sha256": adapter_sha,
                            "content": adapter_content,
                        },
                        {
                            "path": manifest_path,
                            "sha256": manifest_sha,
                            "content": manifest_content,
                        },
                    ],
                },
            }
        }

        compacted = _compact_exact_board_generation_kernel_inputs(inputs)
        documents = compacted["verification_capability_repair_package"][
            "repair_source_bundle"
        ]["documents"]
        projected_adapter, editable_manifest = documents

        self.assertNotIn("content", projected_adapter)
        self.assertEqual(projected_adapter["sha256"], adapter_sha)
        self.assertTrue(
            projected_adapter["content_projection"]["full_hash_bound_source_remains_on_disk"]
        )
        self.assertEqual(
            projected_adapter["content_projection"]["interface_contract"]["module"],
            "compute_slot_adapter",
        )
        self.assertEqual(editable_manifest["content"], manifest_content)

        inputs["verification_capability_repair_package"]["repair_source_bundle"][
            "editable_contract"
        ]["allowed_exact_files"].append(adapter_path)
        editable_compacted = _compact_exact_board_generation_kernel_inputs(inputs)
        editable_adapter = editable_compacted["verification_capability_repair_package"][
            "repair_source_bundle"
        ]["documents"][0]
        self.assertEqual(editable_adapter["content"], adapter_content)

    def test_exact_board_generation_omits_only_hash_identical_duplicate_source_bodies(self):
        generated_content = (
            "object GeneratedKernel { val lanes = 8 }\n"
            + "// hash-bound source body\n" * 1024
        )
        generated_sha = hashlib.sha256(generated_content.encode()).hexdigest()
        wrapper_content = "module sample_wrapper(input clock); endmodule\n"
        wrapper_sha = hashlib.sha256(wrapper_content.encode()).hexdigest()
        inputs = {
            "verification_capability_repair_package": {
                "exact_board_integration_repair_context": {
                    "adaptive_design_inputs": {
                        "kernel_binding_design_inputs": {
                            "current_generator_sources": [
                                {
                                    "path": "/run/generated/GeneratedKernel.scala",
                                    "sha256": generated_sha,
                                    "content": generated_content,
                                }
                            ],
                            "certified_top_sources": [],
                        }
                    }
                },
                "repair_source_bundle": {
                    "documents": [
                        {
                            "path": "accagent/framework/templates/GeneratedKernel.scala",
                            "sha256": generated_sha,
                            "content": generated_content,
                        },
                        {
                            "path": "/sample/board_wrapper.sv",
                            "sha256": wrapper_sha,
                            "content": wrapper_content,
                        },
                    ]
                },
            }
        }

        compacted = _compact_exact_board_generation_kernel_inputs(inputs)
        package = compacted["verification_capability_repair_package"]
        bundle = package["repair_source_bundle"]
        kernel = package["exact_board_integration_repair_context"][
            "adaptive_design_inputs"
        ]["kernel_binding_design_inputs"]

        self.assertEqual(
            [row["path"] for row in bundle["documents"]],
            ["/sample/board_wrapper.sv"],
        )
        self.assertEqual(
            bundle["duplicate_documents_supplied_by_current_generator_sources"],
            [
                {
                    "path": "accagent/framework/templates/GeneratedKernel.scala",
                    "sha256": generated_sha,
                    "content_supplied_by": "/run/generated/GeneratedKernel.scala",
                }
            ],
        )
        self.assertEqual(
            kernel["current_generator_sources"][0]["content"], generated_content
        )
        self.assertEqual(bundle["documents"][0]["content"], wrapper_content)
        self.assertLess(
            len(json.dumps(compacted, separators=(",", ":")).encode()),
            len(json.dumps(inputs, separators=(",", ":")).encode()),
        )

    def test_generation_context_defers_runtime_without_hiding_physical_blockers(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch('accagent.framework.stage_repair_execute.exact_board_memory_runtime_authority',
                   side_effect=AssertionError('runtime images are not compile prerequisites')):
            result = board_integration_repair_context({}, Path(directory))
        self.assertTrue(result['runtime_materialization_deferred'])
        self.assertIn('exact board-source identity has not passed', result['blockers'])
        self.assertNotIn('complete Transformer-block weight catalog is unavailable', result['blockers'])
        prompt = '\n'.join(board_integration_prompt_rules())
        self.assertIn('connected synthesizable accelerator integration', prompt)
        self.assertIn('required_binding_manifest', prompt)
        self.assertIn('Do not invent separate verification/case_hierarchy manifests', prompt)
        self.assertIn('Sources under diagnostics/reference are historical and cannot override current evidence', prompt)
        self.assertIn("scale/shift loading path and configuration address map are design outputs", prompt)
        self.assertIn("Never substitute guessed numeric constants", prompt)

    def test_identity_preflight_keeps_source_and_physical_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            identity_path, _, identity, _ = _case(Path(directory))
            identity.update(validation_policy='vcs_compile_only', functional_semantics_claimed=False,
                            deferred_runtime_evidence=['runtime behavior is unverified'])
            abi = identity['compute_slot_abi']
            abi['control_abi'] = {'port_classifications': [
                dict(port, fact_port_id=port['port_id']) for port in abi['required_ports']
            ]}
            identity['compute_slot_abi_sha256'] = contract.canonical_contract_sha256(abi)
            timing = identity['timing_contract']
            for key in ('timescale', 'timeprecision', 'startup_sequence', 'memory_timing_model'):
                timing.pop(key, None)
            for row in timing['resets']:
                row.pop('minimum_assert_cycles', None)
            for interface in identity['axi_interfaces']:
                interface.pop('supports_unaligned_access', None)
                interface['parameter_evidence_refs'].pop('supports_unaligned_access', None)
            identity['axi_interfaces_sha256'] = contract.canonical_contract_sha256(identity['axi_interfaces'])
            identity['timing_contract_sha256'] = contract.canonical_contract_sha256(timing)
            identity_path.write_text(json.dumps(identity))
            result = contract.validate_exact_board_identity(identity_path)
            self.assertEqual('pass', result['status'], result['blockers'])
            abi['port_bindings'][0]['width_bits'] = 999
            identity['compute_slot_abi_sha256'] = contract.canonical_contract_sha256(abi)
            identity_path.write_text(json.dumps(identity))
            self.assertEqual('fail', contract.validate_exact_board_identity(identity_path)['status'])

    def test_contract_defers_runtime_but_keeps_physical_binding(self):
        full = impl.board_interface_domain_output_contract()
        bounded = impl.board_interface_domain_output_contract(compile_only=True)
        self.assertIn('control_sequence', full['control_abi']['required_fields'])
        self.assertNotIn('control_sequence', bounded['control_abi']['required_fields'])
        self.assertIn('port_bindings', bounded['compute_slot_abi'])
        self.assertIn('signal_fact_map', bounded['axi_interfaces'])
        self.assertFalse(bounded['top_level']['passing_values']['functional_semantics_claimed'])

    def test_missing_runtime_semantics_needs_explicit_compile_policy(self):
        fixture = fixtures.ControlAbiTests()
        facts, cell = fixture.facts()
        control = {'port_classifications': fixture.control('source')['port_classifications']}
        self.assertEqual([], impl._validate_control(control, cell, facts, {}, [], compile_only=True))
        self.assertTrue(impl._validate_control(control, cell, facts, {}, []))
        wrong = copy.deepcopy(control)
        wrong['port_classifications'][0]['width_bits'] = 97
        self.assertTrue(impl._validate_control(wrong, cell, facts, {}, [], compile_only=True))
        wrong = copy.deepcopy(control)
        wrong['port_classifications'].pop()
        self.assertTrue(impl._validate_control(wrong, cell, facts, {}, [], compile_only=True))

    def test_compile_timing_rejects_wrong_frequency_and_polarity(self):
        cell = {'object_id': 'cell', 'kind': 'cell', 'path': '/slot', 'bd_path': '/design'}
        objects = [cell]
        for name, props in [('clk', {'TYPE': 'clk', 'CONFIG.FREQ_HZ': '100000000'}),
                            ('rst', {'TYPE': 'rst', 'CONFIG.POLARITY': 'ACTIVE_LOW'}),
                            ('cal', {'TYPE': 'undef'})]:
            objects.append({'object_id': name, 'kind': 'pin', 'path': '/slot/' + name,
                            'owner_path': '/slot', 'bd_path': '/design', 'properties': props,
                            'connected_nets': [{'kind': 'net', 'path': '/' + name}]})
        facts = {'objects': objects}
        timing = {'clock_domains': [{'fact_port_id': 'clk', 'name': 'clk',
                                    'frequency_hz': 100000000, 'period_ps': 10000, 'evidence_refs': ['clk']}],
                  'resets': [{'fact_port_id': 'rst', 'name': 'rst', 'active_level': 0, 'evidence_refs': ['rst']}],
                  'calibration': [{'fact_port_id': 'cal', 'name': 'cal', 'evidence_refs': ['cal']}]}
        self.assertEqual([], impl._validate_compile_timing(timing, cell, facts))
        timing['resets'][0]['active_level'] = 1
        self.assertTrue(impl._validate_compile_timing(timing, cell, facts))
        timing['resets'][0]['active_level'] = 0
        timing['clock_domains'][0]['period_ps'] = 4000
        self.assertTrue(impl._validate_compile_timing(timing, cell, facts))
        timing['clock_domains'][0]['period_ps'] = 10000
        timing['calibration'][0]['evidence_refs'].append('invented:pin')
        self.assertTrue(impl._validate_compile_timing(timing, cell, facts))

    def test_compile_identity_cannot_certify_runtime(self):
        identity = {'validation_policy': 'vcs_compile_only', 'functional_semantics_claimed': False}
        self.assertTrue(contract.compile_only_board_contract(identity))
        self.assertFalse(contract.compile_only_board_contract({'validation_policy': 'vcs_compile_only'}))
        with patch.object(contract, '_validate_exact_board_contract', return_value={'status': 'pass'}), \
             patch.object(contract, '_load_json_object', return_value=(identity, [])):
            result = contract.validate_exact_board_acceptance(Path('identity'), Path('simulation'))
        self.assertEqual('fail', result['status'])
        self.assertIn('runtime semantics', result['blockers'][0])
