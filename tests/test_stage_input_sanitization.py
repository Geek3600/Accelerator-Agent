from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from accagent.framework import stage_input
from accagent.framework.stage_input import (
    bind_task_qor_targets,
    bind_discovered_board_resource_budget,
    canonical_tool_role,
    design_space_physical_candidate_errors,
    design_space_stream_packing_errors,
    framework_physical_candidate_domain_seed,
    merge_board_profile_field_evidence,
    merge_tool_profile_bindings,
    parse_vivado_resource_budget,
    prompt_field_evidence_summary,
    redact_sensitive_text,
    remote_probe_workdir_expr,
    sanitize_llm_payload,
    task_qor_hard_constraints,
    task_qor_targets,
    task_timing_optimization_request,
)


class StageInputSanitizationTest(unittest.TestCase):
    @staticmethod
    def board_input_case() -> dict:
        return {
            "task_card": {"target_model": "generic-decoder", "design_goal": "compile and synthesize"},
            "model_config": {"block": {"operator_sequence": ["attention"]}},
            "numeric_policy": {
                "default_rules": {"weight_dtype": "int4", "activation_dtype": "int8", "acc_dtype": "int32", "scale_dtype": "int32", "rounding": "nearest_even", "saturation": True},
                "tolerance": {"stage": {"enabled": True}, "system": {"enabled": True}, "comparison": {"atol": 1, "rtol": 1, "max_mismatch_fraction": 1}},
            },
            "template_metadata": {"templates": [{"id": "attention"}]},
            "design_space": {"search_params": {"lanes": [8]}},
            "target_board_profile": {
                "board": {"fpga_part": "target-part"},
                "memory_system": {"hbm_channels": 32, "axi_data_width_bits": 256, "axi_data_bytes": 32},
                "runtime_interface": {"control_protocol": "axi_lite"},
            },
            "field_evidence": {"policy": {"llm_semantic_confirmation_required": True}, "evidence": []},
            "case_adapter": {"status": "ready"},
            "tool_profile": {"tools": [{"name": name, "scope": "remote", "host": "eda@example.org", "executable": f"/eda/{name}"} for name in ("vivado", "vcs")]},
            "tool_availability": {"tools": [{"name": name, "available": True, "version_probe": {"ok": True}, "flow_probe": {"ok": True}} for name in ("vivado", "vcs")]},
        }

    def test_compile_only_intake_accepts_hbm_without_host_runtime_script(self) -> None:
        with patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}):
            errors, _ = stage_input.validate_inputs(self.board_input_case())
        self.assertEqual(errors, [])

    def test_runtime_intake_still_requires_host_runtime_script(self) -> None:
        with patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "full_semantic_simulation"}):
            errors, _ = stage_input.validate_inputs(self.board_input_case())
        self.assertEqual(errors, ["target_board_profile.runtime_interface missing board_run_command"])

    def test_compile_only_intake_still_requires_memory_topology(self) -> None:
        items = self.board_input_case()
        items["target_board_profile"]["memory_system"].pop("hbm_channels")
        with patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}):
            errors, _ = stage_input.validate_inputs(items)
        self.assertEqual(errors, ["target_board_profile.memory_system missing memory channel count"])

    def test_board_runtime_tool_requirement_matches_verification_policy(self) -> None:
        for policy, required in (("vcs_compile_only", False), ("full_semantic_simulation", True)):
            with self.subTest(policy=policy), tempfile.TemporaryDirectory() as tmp:
                input_dir = Path(tmp) / "input"
                input_dir.mkdir()
                with patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": policy}):
                    protocols = stage_input.prepare_tool_protocols(
                        {"runtime_interface": {}}, {}, "", Path(tmp), input_dir, {},
                    )
                runtime = next(item for item in protocols["tools"] if item["name"] == "board_runtime")
                self.assertEqual(runtime["required"], required)
                self.assertEqual(runtime["execution"]["argv"], [])

    def test_board_profile_schema_requires_downstream_axi_field_names(self) -> None:
        profile = {
            "schema_version": "test", "board": {}, "shell": {},
            "memory_system": {"canonical_axi_data_width_bits": 512, "canonical_axi_bytes_per_beat": 64},
            "runtime_interface": {}, "board_pass_criteria": {}, "notes": [],
        }
        with self.assertRaisesRegex(ValueError, "axi_data_width_bits"):
            stage_input.validate_schema(profile, stage_input.BOARD_PROFILE_SCHEMA)
        profile["memory_system"].update(axi_data_width_bits=512, axi_data_bytes=64)
        stage_input.validate_schema(profile, stage_input.BOARD_PROFILE_SCHEMA)

    def test_board_evidence_summary_retains_all_source_backed_interface_facts(self) -> None:
        evidence = {
            "policy": {"llm_semantic_confirmation_required": True},
            "evidence": [
                {"field": "board.fpga_part", "value": "xcu280-fsvh2892-2L-e", "source": "board.md", "chunk_id": "board:1", "excerpt": "U280"},
                {"field": "memory_system.hbm_interface", "value": {"default_pseudo_channels": 32, "per_channel_data_width_bits": 256}, "source": "shell.sv", "chunk_id": "board:2", "excerpt": "hbm interface"},
                {"field": "memory_system.gamma_interface", "value": {"data_width_bits": 512}, "source": "shell.sv", "chunk_id": "board:2", "excerpt": "gamma interface"},
                {"field": "board.clock_reset_domains", "value": [{"clock": "core_clk", "reset": "core_rst_n"}], "source": "shell.sv", "chunk_id": "board:2", "excerpt": "clock"},
            ],
        }

        summary = prompt_field_evidence_summary(evidence)
        fields = {item["field"] for item in summary["selected_fields"]}
        self.assertTrue({"board.fpga_part", "memory_system.hbm_interface", "memory_system.gamma_interface", "board.clock_reset_domains"} <= fields)
        hbm = next(item for item in summary["selected_fields"] if item["field"] == "memory_system.hbm_interface")
        self.assertEqual(hbm["evidence"][0]["value"]["per_channel_data_width_bits"], 256)

    def test_board_prompt_distinguishes_core_refill_from_physical_port(self) -> None:
        profile = {
            "memory_system": {
                "axi_data_width_bits": 512, "axi_data_bytes": 64,
                "physical_interfaces": {"hbm": {"data_width_bits": 256}},
            },
            "runtime_interface": {}, "shell": {},
        }
        with patch.object(stage_input, "llm_json", return_value=profile) as llm:
            result = stage_input.prepare_board_profile({}, {"selected_fields": []}, {}, Path("unused"))
        prompt = llm.call_args.args[1]
        self.assertIn("use that logical width for these two fields", prompt)
        self.assertIn("Do not narrow core stream lanes", prompt)
        self.assertEqual(result["memory_system"]["axi_data_width_bits"], 512)
        self.assertEqual(result["memory_system"]["physical_interfaces"]["hbm"]["data_width_bits"], 256)

    def test_tool_profile_gets_original_documents_when_evidence_omits_endpoints(self) -> None:
        original = "Tool hosted on eda@example.org; executable /opt/custom/bin/vcs"
        with patch.object(stage_input, "llm_json", return_value={"tools": []}) as llm:
            stage_input.prepare_tool_profile(
                {}, {}, {"selected_fields": []}, Path("."),
                tool_materials_text=original,
            )
        prompt = llm.call_args.args[1]
        self.assertIn(original, prompt)
        self.assertIn("<tool_materials_text>", prompt)
        self.assertIn("missing field in the extracted evidence summary", prompt)

    def test_evidence_domain_can_cite_complete_material_outside_candidate_summary(self) -> None:
        original = "### chunk:tools:000001 source:custom.md\nExplicit tool host eda@example.org"
        with patch.object(stage_input, "llm_json", return_value={"evidence": []}) as llm:
            stage_input.prepare_field_evidence_domain(
                domain="tool", domain_materials_text=original,
                source_prefixes=("tool.",), regex_candidates={"evidence": []},
                out_dir=Path("."),
            )
        prompt = llm.call_args.args[1]
        self.assertIn(original, prompt)
        self.assertIn("not a limit on the evidence you can extract", prompt)
        self.assertNotIn("return only evidence supported by those excerpts", prompt)

    def test_board_profile_derives_xdma_device_templates_from_explicit_runtime_facts(self) -> None:
        profile = {
            "runtime_interface": {
                "control_protocol": "xdma_raw_register_and_ddr",
                "xdma_id_default": 1,
            }
        }

        result = merge_board_profile_field_evidence(profile, {"selected_fields": []})

        self.assertEqual(result["runtime_interface"]["h2c_device_template"], "/dev/xdma1_h2c_0")
        self.assertEqual(result["runtime_interface"]["c2h_device_template"], "/dev/xdma1_c2h_0")

    def test_board_profile_preserves_explicit_xdma_device_templates(self) -> None:
        profile = {
            "runtime_interface": {
                "control_protocol": "xdma_raw_register_and_ddr",
                "xdma_id_default": 1,
                "h2c_device_template": "/dev/xdma7_h2c_0",
                "c2h_device_template": "/dev/xdma7_c2h_0",
            }
        }

        result = merge_board_profile_field_evidence(profile, {"selected_fields": []})

        self.assertEqual(result["runtime_interface"]["h2c_device_template"], "/dev/xdma7_h2c_0")
        self.assertEqual(result["runtime_interface"]["c2h_device_template"], "/dev/xdma7_c2h_0")

    def test_tool_role_normalization_accepts_natural_language_separator(self) -> None:
        self.assertEqual(canonical_tool_role("functional verification"), "functional_verification")

        profile = {
            "schema_version": "test.tool_profile.v1",
            "tools": [{"name": "vcs", "role": "functional verification"}],
        }
        normalized = merge_tool_profile_bindings(profile, {}, {"selected_fields": []})
        self.assertEqual(normalized["tools"][0]["role"], "functional_verification")

    def test_framework_physical_domain_seed_is_complete_and_normalizable(self) -> None:
        errors = design_space_physical_candidate_errors(
            {"search_params": framework_physical_candidate_domain_seed()}
        )

        self.assertEqual(errors, [])

    def test_missing_lane_domain_is_sent_to_llm_repair(self) -> None:
        invalid = {"search_params": {}, "sources": {}, "notes": []}
        repaired = {**invalid, "search_params": framework_physical_candidate_domain_seed()}
        with patch.object(stage_input, "llm_json", side_effect=[invalid, repaired]) as llm, \
                patch.object(stage_input, "semantic_stream_contract", return_value={
                    "status": "ready", "required_stream_bits": [8, 32], "axi_data_width_bits": 512,
                }):
            result = stage_input.prepare_design_space(
                {"model_type": "generic"}, {"templates": []},
                {"memory_system": {"axi_data_width_bits": 512}},
                {"default_rules": {"weight_dtype": "int4", "activation_dtype": "int8", "acc_dtype": "int32"}},
                {}, Path("unused"),
            )
        self.assertEqual(llm.call_count, 2)
        self.assertIn("does not declare any physical lanes", llm.call_args_list[1].args[1])
        self.assertEqual(result["search_params"], repaired["search_params"])

    def test_design_space_rejects_candidate_count_without_physical_domain(self) -> None:
        errors = design_space_physical_candidate_errors(
            {
                "search_params": {
                    "candidate_universe": {
                        "base_compute_array_candidate_count": 41,
                        "physical_fifo_depth_values": [2, 4],
                        "activation_bank_count_values": [1, 2],
                    },
                    "lanes": {"candidate_values": [8, 16]},
                }
            }
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("physical candidate domain is incomplete", errors[0])

    def test_design_space_accepts_complete_stage4_candidate_domain(self) -> None:
        errors = design_space_physical_candidate_errors(
            {
                "search_params": {
                    "hardware_parameter_tuples": [
                        {
                            "lanes": 8,
                            "compute_array": {"rows": 2, "cols": 4},
                            "physical_fifo_depth": 16,
                            "activation_bank_count": 2,
                        }
                    ]
                }
            }
        )

        self.assertEqual(errors, [])

    def test_design_space_accepts_nested_candidate_dimension_domain(self) -> None:
        errors = design_space_physical_candidate_errors(
            {
                "search_params": {
                    "candidate_universe": {
                        "candidate_dimensions": {
                            "lanes": {"legal_values": [8, 16]},
                            "compute_array": {
                                "legal_row_col_pairs": [{"rows": 2, "cols": 4}]
                            },
                            "physical_fifo_depth": {"legal_values": [2, 4]},
                            "activation_bank_count": {"legal_values": [1, 2]},
                        }
                    }
                }
            }
        )

        self.assertEqual(errors, [])

    def test_design_space_rejects_nested_candidate_dimension_domain_missing_axis(self) -> None:
        errors = design_space_physical_candidate_errors(
            {
                "search_params": {
                    "candidate_universe": {
                        "candidate_dimensions": {
                            "lanes": {"legal_values": [8, 16]},
                            "compute_array": {
                                "legal_row_col_pairs": [{"rows": 2, "cols": 4}]
                            },
                            "physical_fifo_depth": {"legal_values": [2, 4]},
                        }
                    }
                }
            }
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("candidate_universe.candidate_dimensions", errors[0])

    def test_design_space_rejects_lane_domain_without_fp32_stream_coverage(self) -> None:
        errors = design_space_stream_packing_errors(
            {"search_params": {"lanes": [32]}},
            {"status": "ready", "required_stream_bits": [16, 32], "axi_data_width_bits": 512},
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("stream element width 32", errors[0])

    def test_design_space_accepts_lane_domain_covering_mixed_stream_widths(self) -> None:
        errors = design_space_stream_packing_errors(
            {"search_params": {"lanes": [8, 16, 32]}},
            {"status": "ready", "required_stream_bits": [16, 32], "axi_data_width_bits": 512},
        )

        self.assertEqual(errors, [])

    def test_design_space_stream_packing_accepts_lane_conditioned_candidate_universe(self) -> None:
        errors = design_space_stream_packing_errors(
            {
                "search_params": {
                    "candidate_universe": {
                        "lanes": {"legal_values": [8, 16]},
                        "compute_array": {
                            "legal_row_col_pairs_by_lanes": {
                                "8": [{"rows": 4, "cols": 4}],
                                "16": [{"rows": 4, "cols": 4}],
                            }
                        },
                        "physical_fifo_depth": {"legal_values": [2, 4]},
                        "activation_bank_count": {"legal_values": [1, 2]},
                    }
                }
            },
            {"status": "ready", "required_stream_bits": [16, 32], "axi_data_width_bits": 512},
        )

        self.assertEqual(errors, [])

    def test_sensitive_material_lines_are_removed_from_stage0_prompts(self) -> None:
        secret = "example-secret-value"
        text = f"remote host: build@example.org\npassword is {secret}\npasswordless login: true\n"

        redacted = redact_sensitive_text(text)

        self.assertNotIn(secret, redacted)
        self.assertIn("remote host: build@example.org", redacted)
        self.assertIn("passwordless login: true", redacted)

    def test_credential_field_evidence_is_not_persisted(self) -> None:
        payload = {
            "evidence": [
                {"field": "tool.remote.host", "value": "build@example.org"},
                {"field": "tool.remote.ssh_password", "value": "example-secret-value"},
            ],
            "tool_api_key": "another-secret",
        }

        sanitized = sanitize_llm_payload(payload)

        self.assertEqual(sanitized["evidence"], [{"field": "tool.remote.host", "value": "build@example.org"}])
        self.assertNotIn("tool_api_key", sanitized)

    def test_formal_campaign_qor_constraints_are_preserved_from_each_task_spec(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for campaign in ("20260921_gpt2", "20260921_qwen2", "20260921_llama"):
            targets = task_qor_targets(
                (root / "accagent" / "campaigns" / campaign / "task_spec.md").read_text(encoding="utf-8")
            )

            self.assertNotIn("clock_frequency_mhz", targets)
            self.assertEqual(targets["performance_tokens_per_second"], 200.0)
            self.assertEqual(targets["performance_comparison"], "target")
            self.assertEqual(targets["resource_budget"], "discovered_target_board")
            self.assertTrue(targets["power_report_required"])
            self.assertFalse(targets["power_limit_applies"])
            self.assertEqual(task_qor_hard_constraints(targets), [
                "lut_ff_bram_uram_dsp <= discovered_target_board_resource_budget",
                "power_w measured",
            ])

    def test_run_local_fmax_request_is_separate_from_initial_dse_targets(self) -> None:
        tasks = [
            (
                "After a legal candidate is verified, continue the run-local critical-path "
                "optimization loop until source-bound Vivado post-synthesis Fmax is at least 150 MHz.",
                150.0,
            ),
            (
                "For the current existing-design timing optimization, achieved clock frequency "
                "must be at least 100 MHz.",
                100.0,
            ),
            (
                "There is no minimum achieved clock requirement. Keep the 150 MHz timing-target envelope "
                "while maximizing throughput.",
                150.0,
            ),
        ]

        for task, frequency in tasks:
            self.assertNotIn("clock_frequency_mhz", task_qor_targets(task))
            self.assertEqual(
                task_timing_optimization_request(task),
                {"scope": "existing_design_timing", "clock_frequency_mhz": frequency, "source": "task_spec"},
            )

    def test_task_qor_constraints_override_an_incomplete_llm_design_space(self) -> None:
        targets = task_qor_targets(
            "Hard QoR constraints: achieved clock frequency must be at least 250 MHz; "
            "measured performance must be strictly greater than 170 token/s; LUT, FF, BRAM, "
            "URAM, and DSP usage must remain within the discovered target board resource budget. "
            "Measure and report power, but do not impose a power limit."
        )
        incomplete = {
            "schema_version": "spatialaccagent.design_space.v0",
            "status": "ready",
            "sources": {},
            "search_params": {"lanes": {"candidates": [8]}},
            "objectives": [],
            "hard_constraints": [],
            "notes": [],
        }

        with patch.object(stage_input, "llm_json", return_value=incomplete):
            with self.assertRaises(stage_input.InputPreparationError) as raised:
                stage_input.prepare_design_space(
                    {"model_type": "generic"},
                    {"library_id": "templates", "templates": []},
                    {"board": {"board_id": "target"}},
                    {"default_rules": {"weight_dtype": "fp16"}},
                    targets,
                    Path("unused"),
                )

        self.assertIn("physical candidate domain is incomplete", str(raised.exception))

    def test_incomplete_physical_domain_uses_llm_repair_before_stage0_acceptance(self) -> None:
        targets = task_qor_targets(
            "Hard QoR constraints: achieved clock frequency must be at least 250 MHz; "
            "measured performance must be strictly greater than 170 token/s; LUT, FF, BRAM, "
            "URAM, and DSP usage must remain within the discovered target board resource budget. "
            "Measure and report power, but do not impose a power limit."
        )
        incomplete = {
            "schema_version": "spatialaccagent.design_space.v0",
            "status": "ready_for_stage4",
            "sources": {},
            "search_params": {
                "candidate_universe": {"base_compute_array_candidate_count": 41},
                "lanes": {"candidate_values": [8, 16]},
            },
            "objectives": [],
            "hard_constraints": [],
            "notes": [],
        }
        repaired = {
            **incomplete,
            "search_params": framework_physical_candidate_domain_seed(),
        }

        with patch.object(stage_input, "llm_json", side_effect=[incomplete, repaired]) as llm:
            result = stage_input.prepare_design_space(
                {"model_type": "generic"},
                {"library_id": "templates", "templates": []},
                {"board": {"board_id": "target"}},
                {"default_rules": {"weight_dtype": "fp16"}},
                targets,
                Path("unused"),
            )

        self.assertEqual(llm.call_count, 2)
        initial_prompt = llm.call_args_list[0].args[1]
        repair_prompt = llm.call_args_list[1].args[1]
        self.assertIn("<framework_physical_domain_seed>", initial_prompt)
        self.assertIn('"legal_row_col_pairs"', initial_prompt)
        self.assertIn("<framework_physical_domain_seed>", repair_prompt)
        self.assertIn('"legal_row_col_pairs"', repair_prompt)
        self.assertEqual(result["qor_targets"], targets)
        self.assertEqual(
            result["hard_constraints"], task_qor_hard_constraints(targets)
        )

    def test_real_vivado_capacity_report_binds_the_target_board_budget(self) -> None:
        report = """
|        Site Type        | Used | Fixed | Prohibited | Available | Util% |
| CLB LUTs*               |    0 |     0 |          0 |   1182240 |  0.00 |
| CLB Registers           |    0 |     0 |          0 |   2364480 |  0.00 |
|   RAMB36/FIFO*          |    0 |     0 |          0 |      2160 |  0.00 |
|   RAMB18                |    0 |     0 |          0 |      4320 |  0.00 |
| URAM                    |    0 |     0 |          0 |       960 |  0.00 |
| DSPs                    |    0 |     0 |          0 |      6840 |  0.00 |
"""
        budget = parse_vivado_resource_budget(report)
        self.assertEqual(
            budget,
            {"lut": 1_182_240, "ff": 2_364_480, "bram": 2160, "bram36": 2160, "bram18": 4320, "uram": 960, "dsp": 6840},
        )

        board = bind_discovered_board_resource_budget(
            {"board": {"fpga_part": "target-part", "resource_budget": {}}},
            {"discovered_target_board_resource_budget": budget},
        )
        self.assertEqual(board["board"]["resource_budget"], budget)
        self.assertEqual(board["board"]["resource_budget_source"], "real_vivado_target_part_probe")

    def test_parallel_runs_use_distinct_remote_probe_directories(self) -> None:
        tool: dict[str, object] = {}

        first = remote_probe_workdir_expr(tool, "vivado", "formal/gpt2")
        second = remote_probe_workdir_expr(tool, "vivado", "formal/qwen2")

        self.assertEqual(
            first,
            "$HOME/workspace/spatialacc_stage0_tool_probe/vivado/formal_gpt2",
        )
        self.assertEqual(
            second,
            "$HOME/workspace/spatialacc_stage0_tool_probe/vivado/formal_qwen2",
        )
        self.assertNotEqual(first, second)

    def test_blank_remote_tool_endpoint_fields_bind_from_current_run_evidence(self) -> None:
        profile = {
            "schema_version": "spatialaccagent.tool_profile.v0",
            "tools": [
                {
                    "name": "vivado",
                    "role": "synthesis",
                    "scope": None,
                    "host": None,
                    "port": None,
                    "executable": "/home/EDA/Xilinx/Vivado/2021.1/bin/vivado",
                    "env": {},
                    "workdir": None,
                    "constraints": [],
                    "source": "tool materials",
                }
            ],
            "notes": [],
        }
        board = {"runtime_interface": {"remote_host": "eda@example.org", "remote_port": 22}}
        evidence = {
            "selected_fields": [
                {
                    "field": "tool.vivado.executable",
                    "evidence": [{"value": "/home/EDA/Xilinx/Vivado/2021.1/bin/vivado"}],
                }
            ]
        }

        result = merge_tool_profile_bindings(profile, board, evidence)
        vivado = result["tools"][0]

        self.assertEqual(vivado["host"], "eda@example.org")
        self.assertEqual(vivado["port"], 22)
        self.assertEqual(vivado["scope"], "remote")
        self.assertEqual(vivado["executable"], profile["tools"][0]["executable"])

    def test_explicit_tool_endpoint_fields_are_preserved(self) -> None:
        profile = {
            "tools": [
                {
                    "name": "vcs",
                    "scope": "remote",
                    "host": "existing@example.org",
                    "port": 2200,
                    "executable": "/eda/vcs",
                }
            ],
            "notes": [],
        }

        result = merge_tool_profile_bindings(
            profile,
            {"runtime_interface": {"remote_host": "other@example.org", "remote_port": 22}},
            {
                "selected_fields": [
                    {"field": "tool.vcs.host", "evidence": [{"value": "evidence@example.org"}]},
                    {"field": "tool.vcs.executable", "evidence": [{"value": "/evidence/vcs"}]},
                ]
            },
        )

        self.assertEqual(result["tools"][0]["host"], "existing@example.org")
        self.assertEqual(result["tools"][0]["port"], 2200)
        self.assertEqual(result["tools"][0]["executable"], "/eda/vcs")


if __name__ == "__main__":
    unittest.main()
