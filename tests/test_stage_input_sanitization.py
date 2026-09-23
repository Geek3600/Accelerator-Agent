from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from accagent.framework import stage_input
from accagent.framework.stage_input import (
    bind_task_qor_targets,
    bind_discovered_board_resource_budget,
    design_space_physical_candidate_errors,
    design_space_stream_packing_errors,
    framework_physical_candidate_domain_seed,
    merge_tool_profile_bindings,
    parse_vivado_resource_budget,
    redact_sensitive_text,
    remote_probe_workdir_expr,
    sanitize_llm_payload,
    task_qor_hard_constraints,
    task_qor_targets,
)


class StageInputSanitizationTest(unittest.TestCase):
    def test_framework_physical_domain_seed_is_complete_and_normalizable(self) -> None:
        errors = design_space_physical_candidate_errors(
            {"search_params": framework_physical_candidate_domain_seed()}
        )

        self.assertEqual(errors, [])

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

            self.assertEqual(targets["clock_frequency_mhz"], 250.0)
            self.assertEqual(targets["clock_frequency_comparison"], ">=")
            self.assertEqual(targets["performance_tokens_per_second"], 170.0)
            self.assertEqual(targets["performance_comparison"], ">")
            self.assertEqual(targets["resource_budget"], "discovered_target_board")
            self.assertTrue(targets["power_report_required"])
            self.assertFalse(targets["power_limit_applies"])
            self.assertEqual(
                task_qor_hard_constraints(targets),
                [
                    "clock_frequency_mhz >= 250",
                    "performance_tokens_per_second > 170",
                    "lut_ff_bram_uram_dsp <= discovered_target_board_resource_budget",
                    "power_w measured",
                ],
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
