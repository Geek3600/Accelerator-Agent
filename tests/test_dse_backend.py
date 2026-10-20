from __future__ import annotations

from argparse import Namespace
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.agent import is_formal_dse_backtrack
from accagent.framework.dse_ledger import (
    EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
    SYNTHESIS_APP_SHELL_SCOPE,
    SYNTHESIS_KERNEL_SCOPE,
    load_latest,
)
from accagent.framework.stage_backend import (
    backend_tool_report_digest,
    adapter_repair_board_source_context,
    builtin_backend_tool,
    build_plan,
    check_upstream_hierarchical_verification_closure,
    classify_qor_optimization,
    compact_report,
    normalize_tool_results,
    plan_backend_board,
    prompt_for_backend_recovery,
    record_exact_dse_measurement,
    roles_for_scope,
    run_backend_real_tools,
    repair_generated_compute_slot_adapter,
    validate_backend_recovery_actions,
    update_sacg,
)
from accagent.framework.tool_runner import execution_fingerprint, output_fingerprints
from accagent.framework.verification_evidence_contract import COMPILE_ONLY_POLICY


class DseBackendTest(unittest.TestCase):
    def test_synthesis_clock_uses_discovered_slot_without_qor_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = root / "contract.json"
            contract.write_text(json.dumps({"board_interface": {"clock": "slot_clk"}}))
            identity = root / "verification/board_interface/board_source_identity.json"
            identity.parent.mkdir(parents=True)
            identity.write_text(json.dumps({"timing_contract": {"clock_domains": [
                {"name": "slot_clk", "frequency_hz": 187500000}]}}))
            with patch("accagent.framework.stage_backend.app_shell_integration_contract_path", return_value=contract), \
                patch.dict("os.environ", {"SPATIALACC_CLOCK_TARGET_MHZ": ""}):
                tool = builtin_backend_tool("app_shell_runtime_bitstream", root, [])
            argv = tool["execution"]["argv"]
            self.assertEqual(argv[argv.index("--clock-target-mhz") + 1], "187.5")
            identity.unlink()
            with patch("accagent.framework.stage_backend.app_shell_integration_contract_path", return_value=contract), \
                patch.dict("os.environ", {"SPATIALACC_CLOCK_TARGET_MHZ": ""}):
                tool = builtin_backend_tool("app_shell_runtime_bitstream", root, [])
            self.assertNotIn("--clock-target-mhz", tool["execution"]["argv"])

    def test_successful_backend_proceeds_to_optimization_without_duplicate_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "verification/sacg_state.json"
            source.parent.mkdir()
            source.write_text("{}\n", encoding="utf-8")
            plan = {
                "qor_outputs": [], "final_design_pass": False,
                "final_design_pass_blockers": ["QoR optimization required"],
                "qor_optimization": {"decision": "dse_backtrack", "next_stage": "stage4.parameter_binding"},
            }
            tools = [{"checker": "real_tool.app_shell_runtime_bitstream", "status": "pass", "required": True}]
            with patch("accagent.framework.stage_backend.resolve_board_profile", return_value={}), patch(
                "accagent.framework.stage_backend.write_board_shell_contract"
            ), patch("accagent.framework.stage_backend.write_initial_app_shell_integration_contract"), patch(
                "accagent.framework.stage_backend.check_upstream_hierarchical_verification_closure", return_value={"status": "pass"}
            ), patch("accagent.framework.stage_backend.run_backend_real_tools", return_value=(tools, [])), patch(
                "accagent.framework.stage_backend.record_exact_dse_measurement", return_value={}
            ), patch("accagent.framework.stage_backend.exact_dse_campaign", return_value={}), patch(
                "accagent.framework.stage_backend.build_plan", return_value=plan
            ), patch("accagent.framework.stage_backend.generate_backend_package", return_value={"root": str(root), "files": []}), patch(
                "scripts.synthesis.app_shell_target_hint_synthesis.validated_stage6_selection", return_value={"status": "pass"}
            ), patch("accagent.framework.stage_backend.update_sacg", return_value="transition.backend") as update, patch(
                "accagent.framework.stage_backend.run_stage_agent", side_effect=AssertionError("no duplicate LLM audit")
            ), patch(
                "accagent.framework.stage_backend.generate_backend_bounded_recovery_actions", side_effect=AssertionError("no recovery for successful tools")
            ):
                _, report = plan_backend_board(Namespace(sacg_state=source))
        self.assertEqual(report["status"], "ready")
        self.assertTrue(report["scope_pass"])
        self.assertFalse(report["final_design_pass"])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["bounded_recovery_actions"]["next_stage"], "stage4.parameter_binding")
        self.assertTrue(update.call_args.args[-1])

    def test_current_backend_transition_ignores_retired_checkers_and_records_qor_backtrack(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.json"
            state = {
                "nodes": [{"id": "node.target_board"}],
                "invariants": [
                    {"id": f"invariant.{name}", "checker": f"real_tool.{name}",
                     "constraints": ["constraint.backend.real_tool_evidence"], "status": "fail"}
                    for name in ["case_runtime_abi_check", "app_shell_target_discovery_contract"]
                ],
            }
            state["invariants"].extend(
                {"id": f"invariant.{name}", "checker": name,
                 "constraints": ["constraint.backend.real_tool_evidence"], "status": "fail"}
                for name in ["backend_team_llm_check", "backend_closure_llm_check"]
            )
            state["invariants"].append({"id": "invariant.implementation_package_static",
                "checker": "implementation_package_static", "constraints": ["constraint.backend.package"],
                "status": "unknown"})
            source.write_text(json.dumps(state), encoding="utf-8")
            package = {"root": str(root), "board_shell_wrapper_rtl": str(root / "wrapper.sv")}
            Path(package["board_shell_wrapper_rtl"]).write_text("module Wrapper; endmodule\n", encoding="utf-8")
            for name, payload in {
                "board_shell_contract": {"status": "ready_for_generation"},
                "board_shell_wrapper_manifest": {"status": "pass"},
                "app_shell_integration_contract": {"status": "ready_for_generation"},
                "app_shell_target_selection_decision": {"decision": "approved_target"},
            }.items():
                path = root / f"{name}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                package[name] = str(path)
            recovery = root / "recovery.json"
            recovery.write_text('{"status": "pass"}\n', encoding="utf-8")
            plan = {
                "execution_scope": "all", "qor_outputs": [], "pass_criteria": {},
                "qor": {"measurement_scope": SYNTHESIS_KERNEL_SCOPE},
                "backend_package": package, "resolved_board_profile": {"path": str(source)},
                "real_tool_status": {"final_required_tools": ["app_shell_runtime_bitstream"]},
                "bounded_recovery_actions": {"path": str(recovery)},
                "upstream_hierarchy_gate": {"status": "pass"},
                "agent_gate_status": {"checks": []},
                "qor_optimization": {"decision": "dse_backtrack", "next_stage": "stage4.parameter_binding",
                                     "reason": "Measured resource budget exceeded", "misses": [{"metric": "uram"}]},
            }
            target = root / "backend" / "sacg_state.json"
            transition_id = update_sacg(source, target, root / "plan.json", plan,
                                       [{"checker": "real_tool.app_shell_runtime_bitstream", "status": "pass"}], True)
            updated = json.loads(target.read_text(encoding="utf-8"))
            plan["qor"] = {"measurement_scope": EXACT_TARGET_BOARD_APP_SHELL_SCOPE}
            with self.assertRaisesRegex(ValueError, "implementation_package_static"):
                update_sacg(source, root / "whole_board/sacg_state.json", root / "plan.json", plan,
                            [{"checker": "real_tool.app_shell_runtime_bitstream", "status": "pass"}], True)
        transition = next(row for row in updated["transitions"] if row["id"] == transition_id)
        self.assertEqual(transition["status"], "promoted")
        self.assertNotIn("real_tool.case_runtime_abi_check", transition["required_checkers"])
        self.assertNotIn("real_tool.app_shell_target_discovery_contract", transition["required_checkers"])
        self.assertIn("real_tool.app_shell_runtime_bitstream", transition["required_checkers"])
        self.assertNotIn("implementation_package_static", transition["required_checkers"])
        self.assertEqual(updated["memory"]["backtrack_requests"][-1]["target_stage"], "stage4.parameter_binding")

    def test_synthesis_cache_tracks_source_files_resources_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            files = [
                "backend_board/app_shell_integration_contract.json",
                "generated/chisel/vivado/GeneratedAxiDdrTop.sv",
                "generated/chisel/src/main/resources/weights.memh",
                "generated/chisel/simulation/fpga_ip_modules.txt",
                "generated/chisel/scripts/gen_xilinx_fp_ips_23.tcl",
            ]
            for relative in files:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")
            tool = builtin_backend_tool("app_shell_runtime_bitstream", root, {})
            for filename in [*tool["consumes"], *tool["produces"]]:
                path = Path(filename)
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    path.write_text("{}\n", encoding="utf-8")
            argv = tool["execution"]["argv"]
            fingerprint = execution_fingerprint(tool, argv, argv, Path.cwd(), Path.cwd(), {}, {}, None)
            outputs = output_fingerprints(tool, argv, Path.cwd(), Path.cwd())
            self.assertTrue(fingerprint["cache_reusable"])
            self.assertTrue(outputs["cache_reusable"])
            self.assertIn(str(root / files[2]), tool["consumes"])
            (root / files[2]).write_text("changed memory initialization\n", encoding="utf-8")
            changed = execution_fingerprint(tool, argv, argv, Path.cwd(), Path.cwd(), {}, {}, None)
            self.assertNotEqual(fingerprint["sha256"], changed["sha256"])
            (root / "generated/chisel/vivado/NewModule.sv").write_text("module NewModule; endmodule\n", encoding="utf-8")
            updated_tool = builtin_backend_tool("app_shell_runtime_bitstream", root, {})
            added = execution_fingerprint(updated_tool, argv, argv, Path.cwd(), Path.cwd(), {}, {}, None)
            self.assertNotEqual(changed["sha256"], added["sha256"])

    def test_synthesis_port_errors_enter_the_existing_adapter_repair_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "backend_board"
            report = output / "case_diagnostics/app_shell_runtime_vivado.json"
            report.parent.mkdir(parents=True)
            diagnostic = "ERROR: [Synth 8-448] named port connection does not exist [SpatialAccComputeSlotAdapter.sv:1]"
            tool = {"adapter_role": "app_shell_runtime_bitstream", "required": True}
            report.write_text(json.dumps({"commands": [{"returncode": 1, "stdout_tail": diagnostic}]}), encoding="utf-8")
            with patch("accagent.framework.stage_backend.backend_tools_for_scope", return_value=([tool], [])), patch(
                "scripts.synthesis.app_shell_target_hint_synthesis.validated_stage6_selection", return_value={}
            ), patch("accagent.framework.stage_backend.compute_slot_adapter_rtl_path", return_value=root / "SpatialAccComputeSlotAdapter.sv"), patch(
                "accagent.framework.stage_backend.run_tools", return_value=[{"status": "fail", "name": "app_shell_runtime_bitstream"}]
            ), patch("accagent.framework.stage_backend.repair_generated_compute_slot_adapter", return_value={"status": "pass", "source_changed": True}) as repair:
                results, _ = run_backend_real_tools({}, root, output, None, None)
            self.assertEqual(repair.call_args.args[2]["failure_diagnostics"], [diagnostic])
            self.assertTrue(results[0]["source_change_requires_stage6_refresh"])

    def test_default_backend_does_not_require_physical_runtime_abi_or_bitstream_check(self) -> None:
        self.assertNotIn("runtime_abi_check", roles_for_scope("all"))
        self.assertIn("stage7_metrics", roles_for_scope("all"))

    def test_backend_recovery_prompt_reuses_registered_audit_and_adapter_paths(self) -> None:
        prompt = prompt_for_backend_recovery(
            {
                "action_grounding_registry": {
                    "tool_roles": [
                        "sacg_memory_check",
                        "stage_retry_request",
                        "stage_backtrack_request",
                        "stage_artifact_trust_barrier",
                        "verification_action_audit",
                        "artifact_hash_check",
                        "case_compute_slot_adapter_generate",
                    ],
                    "acceptance_checkers": [],
                },
                "contracts": {},
                "backend_plan": {},
            }
        )

        self.assertIn("Do not declare a planned_tool or planned_checker", prompt)
        self.assertIn("case_compute_slot_adapter_generate bounded repair route", prompt)
        self.assertIn("Reuse current passing audit evidence", prompt)

    def test_adapter_task_receives_verified_board_sources_by_tool_artifact(self) -> None:
        from accagent.framework.stage_team import compact_candidate_artifact_for_worker

        context = {"status": "pass", "sources": [{"path": "loader.sv", "sha256": "abc"}]}
        candidate = {
            "stage": "backend_board",
            "exact_board_loader_source_context": context,
        }

        specialist = compact_candidate_artifact_for_worker(
            candidate,
            {
                "agent": "adapter_codegen_specialist",
                "expected_artifacts": [
                    "real_tool.case_compute_slot_adapter_generate report"
                ],
            },
        )
        unrelated = compact_candidate_artifact_for_worker(
            candidate,
            {
                "agent": "backend_implementation_specialist",
                "expected_artifacts": ["backend implementation report"],
            },
        )

        self.assertEqual(specialist["exact_board_loader_source_context"], context)
        self.assertNotIn("exact_board_loader_source_context", unrelated)

    def test_recovery_registry_drift_does_not_block_llm_action(self) -> None:
        action = {
            "id": "recover",
            "stage": "backend_board",
            "action_type": "read_only_diagnosis",
            "rationale": "inspect current tool evidence",
            "consumes": [],
            "produces": [],
            "tool_roles": ["new_tool_role_from_current_agent"],
            "acceptance_checkers": ["new_checker_from_current_agent"],
            "preconditions": [],
            "blocked_until": [],
            "requires_approval": False,
            "approval_boundary": [],
            "on_success": "continue",
            "on_failure": "report real tool failure",
        }
        self.assertEqual(
            validate_backend_recovery_actions(
                {"bounded_recovery_actions": [action]},
                {"contracts": {}, "backend_plan": {}},
            ),
            [],
        )

    def test_validated_board_selection_removes_redundant_final_target_tools(self) -> None:
        with patch(
            "accagent.framework.stage_backend.constraint_facts", return_value={}
        ), patch(
            "accagent.framework.stage_backend.artifact_path", return_value=Path("/missing-artifact.json")
        ), patch("accagent.framework.stage_backend.read_json", return_value={}):
            plan = build_plan({}, [], [], {}, validated_selection={"status": "pass"})
        missing = plan["real_tool_status"]["missing_final_tools"]
        self.assertNotIn("app_shell_target_discovery_contract", missing)
        self.assertNotIn("app_shell_target_hint_synthesis", missing)
        self.assertNotIn("app_shell_target_discovery_after_hint", missing)
        self.assertIn("app_shell_runtime_bitstream", missing)
        self.assertIn("case_stage7_metrics", missing)

    def test_validated_selection_supersedes_only_historical_discovery_failure(self) -> None:
        discovery = {"checker": "real_tool.app_shell_target_discovery_contract", "status": "fail"}
        implementation = {"checker": "real_tool.app_shell_runtime_bitstream", "status": "fail"}
        state = {"evidence": [discovery, implementation]}
        for selection_status, current_tools, discovery_failed in (
            ("pass", [], False),
            ("fail", [], True),
            ("pass", [discovery], True),
        ):
            with self.subTest(selection_status=selection_status, current_tools=current_tools), patch(
                "accagent.framework.stage_backend.constraint_facts", return_value={}
            ), patch(
                "accagent.framework.stage_backend.artifact_path", return_value=Path("/missing-artifact.json")
            ), patch("accagent.framework.stage_backend.read_json", return_value={}):
                plan = build_plan(state, current_tools, [], {}, validated_selection={"status": selection_status})
            failed = plan["real_tool_status"]["failed"]
            self.assertEqual(discovery["checker"] in failed, discovery_failed)
            self.assertIn(implementation["checker"], failed)
            self.assertFalse(plan["final_design_pass"])
        self.assertEqual(state["evidence"], [discovery, implementation])

    def test_backend_reuses_exact_board_selection_without_repeating_target_discovery(self) -> None:
        roles = ["compute_slot_adapter_generate", "app_shell_target_discovery_contract",
                 "app_shell_target_hint_synthesis", "app_shell_target_discovery_after_hint",
                 "app_shell_runtime_bitstream"]
        tools = [{"name": role, "adapter_role": role, "required": True} for role in roles]
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.stage_backend.backend_tools_for_scope", return_value=(tools, [])
        ), patch(
            "scripts.synthesis.app_shell_target_hint_synthesis.validated_stage6_selection",
            return_value={"status": "pass"},
        ), patch(
            "accagent.framework.stage_backend.run_tools",
            side_effect=lambda selected, *_args: [{"name": selected[0]["name"], "status": "pass"}],
        ) as runner:
            root = Path(temp_dir)
            results, blockers = run_backend_real_tools({}, root, root / "backend", None, None)
        self.assertEqual(runner.call_count, 2)
        self.assertEqual([row["checker"] for row in results], [
            "real_tool.compute_slot_adapter_generate", "real_tool.app_shell_runtime_bitstream",
        ])
        self.assertEqual(blockers, [])

    def test_compile_only_final_closure_uses_current_gates_not_retired_invariants(self) -> None:
        state = {"invariants": [{"checker": "verification_agent_decision_check", "status": "fail"}]}
        roles = ["case_board_shell_wrapper_generate", "case_compute_slot_adapter_generate",
                 "app_shell_runtime_bitstream", "case_runtime_abi_check", "case_stage7_metrics"]
        for policy, bitstream_status, final_pass in (
            (COMPILE_ONLY_POLICY, "pass", True),
            (COMPILE_ONLY_POLICY, "fail", False),
            ("full_semantic_simulation", "pass", True),
        ):
            tools = [{"checker": f"real_tool.{role}", "status": "pass", "required": True} for role in roles]
            tools[2]["status"] = bitstream_status
            tools[-1]["tool_report_digest"] = {
                "resources": {"lut": 100}, "power_w": 1,
                "clock_frequency_mhz": 250, "performance_tokens_per_second": 200,
            }
            with self.subTest(policy=policy, bitstream_status=bitstream_status), patch(
                "accagent.framework.stage_backend.constraint_facts", return_value={}
            ), patch(
                "accagent.framework.stage_backend.artifact_path", return_value=Path("/missing-artifact.json")
            ), patch("accagent.framework.stage_backend.read_json", return_value={"validation_policy": policy}):
                plan = build_plan(state, tools, [], {},
                                  upstream_hierarchy_gate={"status": "pass", "backend_compile_ready": True},
                                  validated_selection={"status": "pass"})
            self.assertEqual(plan["final_design_pass"], final_pass)
            self.assertEqual(plan["design_closure_metrics"]["failed_invariants"], 1)
            if bitstream_status == "fail":
                self.assertIn("failed real tool: real_tool.app_shell_runtime_bitstream", plan["final_design_pass_blockers"])

    def test_source_repair_goes_directly_to_recompile_without_team_audits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_state = root / "verification" / "sacg_state.json"
            source_state.parent.mkdir()
            source_state.write_text(json.dumps({}), encoding="utf-8")
            with patch(
                "accagent.framework.stage_backend.resolve_board_profile", return_value={}
            ), patch(
                "accagent.framework.stage_backend.write_board_shell_contract"
            ), patch(
                "accagent.framework.stage_backend.write_initial_app_shell_integration_contract"
            ), patch(
                "accagent.framework.stage_backend.check_upstream_hierarchical_verification_closure",
                return_value={"status": "pass"},
            ), patch(
                "accagent.framework.stage_backend.run_backend_real_tools",
                return_value=([{"source_change_requires_stage6_refresh": True}], []),
            ), patch(
                "accagent.framework.stage_team.run_design_team", side_effect=AssertionError("unnecessary team audit")
            ):
                report_path, report = plan_backend_board(Namespace(sacg_state=source_state))
            state = json.loads((root / "backend_board" / "sacg_state.json").read_text())

        self.assertEqual(report["status"], "incomplete")
        self.assertFalse(report["final_design_pass"])
        self.assertEqual(report["bounded_recovery_actions"]["next_stage"], "stage6.verification")
        self.assertEqual(state["memory"]["backtrack_requests"][-1]["target_stage"], "stage6.verification")

    def test_missing_compile_evidence_returns_to_stage6_without_backend_audits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_state = root / "verification" / "sacg_state.json"
            source_state.parent.mkdir()
            source_state.write_text("{}\n", encoding="utf-8")
            with patch(
                "accagent.framework.stage_backend.check_upstream_hierarchical_verification_closure",
                return_value={"status": "fail", "closure_mode": "compile_only_to_backend",
                              "blockers": ["current board compile failed"]},
            ), patch(
                "accagent.framework.stage_backend.resolve_board_profile",
                side_effect=AssertionError("no backend preparation before its prerequisite"),
            ), patch(
                "accagent.framework.stage_team.run_design_team",
                side_effect=AssertionError("no LLM audit for the required compile refresh"),
            ):
                _, report = plan_backend_board(Namespace(sacg_state=source_state))

        self.assertEqual(report["status"], "incomplete")
        self.assertTrue(report["stage6_refresh_required"])
        self.assertEqual(report["bounded_recovery_actions"]["next_stage"], "stage6.verification")
        self.assertIn("current board compile failed", report["summary"])

    def test_backend_adapter_repair_uses_current_source_and_exact_write_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "generated" / "board_integration" / "SlotAdapter.sv"
            source.parent.mkdir(parents=True)
            source.write_text("module SlotAdapter(input clock); endmodule\n", encoding="utf-8")
            generated_top = root / "generated" / "chisel" / "vivado" / "GeneratedAxiDdrTop.sv"
            generated_top.parent.mkdir(parents=True)
            generated_top.write_text(
                "module GeneratedTop(input io_norm1Weight_valid, input [127:0] io_norm1Weight_bits); endmodule\n",
                encoding="utf-8",
            )
            generated_top_sha256 = hashlib.sha256(generated_top.read_bytes()).hexdigest()
            sample_dir = root / "verification" / "board_interface" / "sample_project_sources"
            sample_dir.mkdir(parents=True)
            slot_sample = sample_dir / "slot.v"
            slot_sample.write_text("module SlotAdapter; LegacyCore core(); endmodule\n", encoding="utf-8")
            loader_sample = sample_dir / "legacy_core.v"
            loader_sample_content = "module LegacyCore; wire load_valid; endmodule\n"
            loader_sample.write_text(loader_sample_content, encoding="utf-8")
            identity = {
                "status": "pass",
                "simulation_hashes_match_source": True,
                "materialized_sources": [
                    {
                        "source_id": "sample-source:slot",
                        "closure_role": "compute_slot_implementation",
                        "declared_modules": ["SlotAdapter"],
                        "local_path": str(slot_sample),
                        "local_sha256": hashlib.sha256(slot_sample.read_bytes()).hexdigest(),
                        "hashes_match": True,
                    },
                    {
                        "source_id": "sample-source:loader",
                        "declared_modules": ["LegacyCore"],
                        "local_path": str(loader_sample),
                        "local_sha256": hashlib.sha256(loader_sample.read_bytes()).hexdigest(),
                        "hashes_match": True,
                    },
                ],
                "control_abi": {"evidence_refs": ["sample-source:loader"]},
            }
            identity_path = root / "verification" / "board_interface" / "board_source_identity.json"
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            contract = root / "generated" / "backend" / "constraints" / "app_shell_integration_contract.json"
            contract.parent.mkdir(parents=True)
            contract.write_text(json.dumps({
                "integration_target": {
                    "replacement_module_identity": "SlotAdapter",
                    "exact_source_closure": {
                        "source_module_evidence": [{"source_id": "sample-source:slot"}],
                    },
                },
                "compute_slot_abi": {"required_ports": []},
                "loader_route_contract": {
                    "weight": {
                        "path": "weights.u32.memh",
                        "sha256": "a" * 64,
                        "word_bits": 32,
                        "word_count": 4,
                        "stage_segments": [{
                            "stage_id": "stage_00_norm",
                            "op": "norm",
                            "global_stream_range": {"word_offset": 0, "word_count": 4},
                            "targets": [{
                                "target_id": "norm.weight",
                                "dut_port_role": "weight",
                                "global_stream_range": {"word_offset": 0, "word_count": 4},
                                "local_stream_range": {"word_offset": 0, "word_count": 4},
                                "port": {"data_width_bits": 128, "words_per_write": 4},
                                "source_tensor_hashes": ["not-needed-in-repair-context"],
                            }],
                        }],
                    },
                },
                "dut_loader_route_contract": {},
            }), encoding="utf-8")
            with patch(
                "accagent.framework.stage_backend.run_stage_agent",
                return_value={"output": {"status": "ready_to_apply", "file_edits": []}},
            ) as agent, patch(
                "accagent.framework.stage_repair_execute.apply_agent_file_edits",
                return_value={"status": "pass"},
            ) as apply_edits:
                report = repair_generated_compute_slot_adapter(root, root / "backend_board", {
                    "returncode": 1, "stderr_tail": "ValueError: ABI direction mismatch\n",
                })

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["source_changed"])
        inputs = agent.call_args.kwargs["inputs"]
        self.assertEqual(inputs["source_snapshot"]["content"], "module SlotAdapter(input clock); endmodule\n")
        self.assertEqual(inputs["generated_top_interface"]["module"], "GeneratedTop")
        self.assertIn("io_norm1Weight_bits", inputs["generated_top_interface"]["module_header"])
        self.assertEqual(
            inputs["generated_top_interface"]["sha256"],
            generated_top_sha256,
        )
        target = inputs["weight_stream_contract"]["stage_segments"][0]["targets"][0]
        self.assertEqual(target["target_id"], "norm.weight")
        self.assertEqual(target["global_stream_range"]["word_count"], 4)
        self.assertNotIn("source_tensor_hashes", target)
        self.assertEqual(inputs["existing_dut_loader_routes"], {})
        source_context = inputs["exact_board_loader_source_context"]
        self.assertEqual(source_context["status"], "pass")
        self.assertEqual(
            {item["source_id"] for item in source_context["sources"]},
            {"sample-source:slot", "sample-source:loader"},
        )
        self.assertEqual(
            next(item for item in source_context["sources"] if item["source_id"] == "sample-source:loader")["content"],
            loader_sample_content,
        )
        prompt_rules = agent.call_args.kwargs["prompt_rules"]
        self.assertTrue(any(
            "exact_board_loader_source_context when its status is pass" in rule
            for rule in prompt_rules
        ))
        self.assertTrue(any(
            "rather than saying no source context was supplied" in rule
            for rule in prompt_rules
        ))
        self.assertEqual(apply_edits.call_args.kwargs["allowed_exact_files"], {source.resolve()})
        self.assertTrue(apply_edits.call_args.kwargs["require_exact_source_hash"])

    def test_backend_adapter_repair_omits_sample_source_with_stale_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample_dir = root / "verification" / "board_interface" / "sample_project_sources"
            sample_dir.mkdir(parents=True)
            source = sample_dir / "loader.v"
            source.write_text("module Loader; endmodule\n", encoding="utf-8")
            identity = {
                "status": "pass",
                "simulation_hashes_match_source": True,
                "materialized_sources": [{
                    "source_id": "sample-source:loader",
                    "local_path": str(source),
                    "local_sha256": "0" * 64,
                    "hashes_match": True,
                }],
                "control_abi": {"evidence_refs": ["sample-source:loader"]},
            }
            identity_path = root / "verification" / "board_interface" / "board_source_identity.json"
            identity_path.write_text(json.dumps(identity), encoding="utf-8")

            context = adapter_repair_board_source_context(root, {})

        self.assertEqual(context["status"], "unavailable")
        self.assertEqual(context["sources"], [])
        self.assertEqual(context["omitted_sources"][0]["reason"], "materialized source hash does not match its identity record")

    def test_backend_adapter_repair_does_not_call_llm_without_generated_top_interface(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "generated" / "board_integration" / "SlotAdapter.sv"
            source.parent.mkdir(parents=True)
            source.write_text("module SlotAdapter(input clock); endmodule\n", encoding="utf-8")
            contract = root / "generated" / "backend" / "constraints" / "app_shell_integration_contract.json"
            contract.parent.mkdir(parents=True)
            contract.write_text(json.dumps({
                "integration_target": {"replacement_module_identity": "SlotAdapter"},
            }), encoding="utf-8")
            with patch("accagent.framework.stage_backend.run_stage_agent") as agent:
                report = repair_generated_compute_slot_adapter(root, root / "backend_board", {"returncode": 1})

        self.assertEqual(report["status"], "blocked")
        self.assertIn("generated accelerator top is unavailable", report["blockers"][0])
        agent.assert_not_called()

    def test_applied_adapter_repair_requires_stage6_refresh_and_does_not_run_vivado(self) -> None:
        tools = [
            {"name": "adapter", "required": True, "adapter_role": "compute_slot_adapter_generate"},
            {"name": "vivado", "required": True},
        ]
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.stage_backend.backend_tools_for_scope", return_value=(tools, [])
        ), patch(
            "accagent.framework.stage_backend.run_tools",
            return_value=[{"name": "adapter", "status": "fail", "returncode": 1}],
        ) as runner, patch(
            "accagent.framework.stage_backend.repair_generated_compute_slot_adapter",
            return_value={"status": "pass", "source_changed": True},
        ):
            root = Path(temp_dir)
            results, blockers = run_backend_real_tools({}, root, root / "backend", None, None)

        runner.assert_called_once()
        self.assertTrue(results[0]["source_change_requires_stage6_refresh"])
        self.assertIn("refresh Stage-6", blockers[0])

    def test_backend_stops_before_vivado_when_adapter_generation_fails(self) -> None:
        tools = [
            {"name": "wrapper", "required": True},
            {"name": "adapter", "required": True},
            {"name": "vivado", "required": True},
        ]
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.stage_backend.backend_tools_for_scope", return_value=(tools, [])
        ), patch(
            "accagent.framework.stage_backend.run_tools",
            side_effect=[
                [{"name": "wrapper", "status": "pass", "returncode": 0}],
                [{"name": "adapter", "status": "fail", "returncode": 1}],
            ],
        ) as runner:
            root = Path(temp_dir)
            results, blockers = run_backend_real_tools({}, root, root / "backend", None, None)

        self.assertEqual(runner.call_count, 2)
        self.assertEqual([result["checker"] for result in results], ["real_tool.wrapper", "real_tool.adapter"])
        self.assertEqual(blockers, [])

    def test_local_adapter_error_is_retained_in_backend_agent_digest(self) -> None:
        results = normalize_tool_results([{
            "name": "adapter", "status": "fail", "returncode": 1,
            "stderr_tail": "ValueError: compute-slot ABI direction mismatch for control: source=output required=input\n",
        }])
        diagnostics = results[0]["tool_report_digest"]["failure_diagnostics"]
        self.assertIn("direction mismatch for control", diagnostics[0])

    @staticmethod
    def state_for(parameters_path: Path) -> dict[str, object]:
        return {
            "artifacts": [
                {
                    "id": "artifact.stage4.parameter_binding",
                    "path": str(parameters_path),
                }
            ]
        }

    @staticmethod
    def binding(path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "selected_architecture": {
                        "parameters": {
                            "lanes": 16,
                            "fifo_depth": 32,
                            "activation_banks": 2,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

    @staticmethod
    def exact_qor(run_dir: Path) -> None:
        report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
        report.parent.mkdir(parents=True)
        report.write_text(json.dumps({"mode": "bitstream", "status": "pass"}), encoding="utf-8")
        bitstream = run_dir / "app_shell_runtime_bitstream"
        bitstream.mkdir()
        utilization = bitstream / "app_shell_impl_utilization.rpt"
        timing = bitstream / "app_shell_impl_timing.rpt"
        power = bitstream / "app_shell_impl_power.rpt"
        utilization.write_text("present\n", encoding="utf-8")
        timing.write_text("present\n", encoding="utf-8")
        power.write_text("present\n", encoding="utf-8")
        counter = run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"
        counter.parent.mkdir(parents=True)
        counter.write_text("present\n", encoding="utf-8")
        metrics_path = run_dir / "backend_board" / "qor" / "qor_metrics.json"
        metrics_path.parent.mkdir(parents=True)
        evidence_paths = [
            str(path.resolve())
            for path in [report, utilization, timing, power, counter, metrics_path]
        ]
        metrics_path.write_text(
            json.dumps(
                {
                    "measurement_scope": EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
                    "evidence_paths": evidence_paths,
                    "resources": {"lut": 10, "ff": 20, "bram36": 1, "bram18": 0, "uram": 2, "dsp": 3},
                    "power_w": 2.0,
                    "clock_frequency_mhz": 200.0,
                    "performance_tokens_per_second": 1_000.0,
                    "performance_model": "synthesizable_dut_counter",
                }
            ),
            encoding="utf-8",
        )

    def test_default_backend_scope_uses_only_exact_app_shell_measurement_chain(self) -> None:
        roles = roles_for_scope("all")
        self.assertIn("app_shell_runtime_bitstream", roles)
        self.assertIn("stage7_metrics", roles)
        self.assertNotIn("vivado_synthesis", roles)
        self.assertNotIn("vivado_implementation", roles)
        self.assertNotIn("vivado_power", roles)
        self.assertNotIn("board_runtime", roles)

    def test_failed_backend_tool_digest_preserves_command_error_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "vivado_report.json"
            diagnostic = "ERROR: [DRC MDRV-1] Multiple Driver Nets on cnn_core_0/<const0>."
            report_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "summary": "implementation failed",
                        "commands": [
                            {"returncode": 0, "stdout_tail": "ERROR: unrelated successful preflight"},
                            {
                                "returncode": 1,
                                "stdout_tail": f'# error "unsupported module name"\nlink_design completed\n{diagnostic}\nopt_design failed',
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            digest = backend_tool_report_digest(report_path)
            recovery_report = compact_report(report_path)

            self.assertIn(diagnostic, digest["failure_diagnostics"])
            self.assertNotIn("unrelated successful preflight", digest["failure_diagnostics"])
            self.assertNotIn('error "unsupported module name"', " ".join(digest["failure_diagnostics"]))
            self.assertIn(diagnostic, recovery_report["failure_diagnostics"])

    def test_backend_never_falls_back_to_a_legacy_power_script_or_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            self.assertIsNone(builtin_backend_tool("vivado_power", run_dir, []))

        gate = check_upstream_hierarchical_verification_closure({"artifacts": []})
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["closure_mode"], "unresolved_current_run")

    def test_compile_only_stage6_closure_allows_backend_without_board_runtime_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            verification_path = run_dir / "verification" / "verification_result.json"
            certificate_path = run_dir / "verification" / "certificates" / "board_axi_ddr_promotion_certificate.json"
            verification_path.parent.mkdir(parents=True)
            certificate_path.parent.mkdir(parents=True)
            verification_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "validation_policy": COMPILE_ONLY_POLICY,
                        "hierarchical_maturity": {
                            "status": "pass",
                            "backend_ready": True,
                            "levels": [
                                {"id": level, "status": "pass"}
                                for level in (
                                    "operator_leaf_functional",
                                    "single_layer_functional",
                                    "multilayer_pipeline_functional",
                                    "axi_ddr_functional",
                                )
                            ],
                        },
                        "board_bringup_readiness": {
                            "status": "not_run",
                            "board_bringup_ready": False,
                            "backend_compile_ready": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            certificate_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "level_id": "axi_ddr_functional",
                        "validation_policy": COMPILE_ONLY_POLICY,
                        "functional_semantics_claimed": False,
                        "required_gates": [{"name": "board_vcs_compile", "status": "pass"}],
                        "source_result": str(verification_path),
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage6.verification_result",
                        "path": str(verification_path),
                        "producer_transition": "verification_transition",
                    },
                    {
                        "id": "artifact.stage6.board_axi_ddr_promotion_certificate",
                        "path": str(certificate_path),
                        "producer_transition": "certificate_transition",
                    },
                ],
                "transitions": [
                    {"id": "verification_transition", "status": "promoted"},
                    {"id": "certificate_transition", "status": "promoted"},
                ],
            }

            with patch(
                "accagent.framework.stage_verification.build_board_bringup_readiness",
                side_effect=AssertionError("compile-only backend handoff must not require runtime simulation"),
            ):
                gate = check_upstream_hierarchical_verification_closure(state)

        self.assertEqual(gate["status"], "pass")
        self.assertTrue(gate["backend_compile_ready"])
        self.assertFalse(gate["board_bringup_ready"])
        self.assertEqual(gate["closure_mode"], "compile_only_to_backend")

    def test_meeting_targets_does_not_require_exhaustive_measurement(self) -> None:
        metrics = {
            "measurement_scope": SYNTHESIS_KERNEL_SCOPE,
            "resources": {"lut": 10, "ff": 20, "bram36": 1, "bram18": 0, "uram": 1, "dsp": 1},
            "power_w": None,
            "clock_frequency_mhz": 100.0,
            "performance_tokens_per_second": 1_000.0,
            "performance_model": "single_block_reuse_operator_token_pipeline_v1",
        }
        with patch("accagent.framework.stage_backend.constraint_facts", return_value={
            "qor_targets": {"performance_tokens_per_second": 100.0},
            "board": {"resource_budget": {"uram": 10}},
        }):
            result = classify_qor_optimization(
                {}, metrics, campaign={"unmeasured_candidate_ids": ["arch_next"]},
                measurement={"measurement_status": "measured"},
            )

        self.assertEqual(result["decision"], "pass")
        self.assertIn("performance_tokens_per_second", result["targets_checked"])

    def test_unmeasured_candidates_do_not_hide_measured_resource_misses_from_llm(self) -> None:
        metrics = {"resources": {"uram": 999}, "power_w": 1.0,
                   "clock_frequency_mhz": 100.0, "performance_tokens_per_second": 10.0}
        with patch("accagent.framework.stage_backend.constraint_facts", return_value={
            "board": {"resource_budget": {"uram": 960}},
        }):
            result = classify_qor_optimization({}, metrics, campaign={"unmeasured_candidate_ids": ["arch_next"]})
        self.assertEqual(result["decision"], "llm_required")
        self.assertEqual(result["misses"][0]["metric"], "resources.uram")

    def test_synthesis_clock_request_is_not_an_implicit_acceptance_target(self) -> None:
        metrics = {"resources": {"uram": 1}, "power_w": 1.0,
                   "clock_frequency_mhz": 150.0, "performance_tokens_per_second": 170.0}
        with patch("accagent.framework.stage_backend.constraint_facts", return_value={
            "qor_targets": {"performance_tokens_per_second": 170.0},
            "board": {"resource_budget": {"uram": 960}},
        }), patch("accagent.framework.stage_backend.artifact_path", return_value=Path("binding.json")), patch(
            "accagent.framework.stage_backend.read_json", return_value={"global_params": {"clock_target_mhz": 250}},
        ):
            result = classify_qor_optimization({}, metrics)
        self.assertEqual(result["decision"], "pass")
        self.assertNotIn("clock_frequency_mhz", result["targets_checked"])

    def test_strict_throughput_target_rejects_equal_measured_value(self) -> None:
        metrics = {
            "resources": {"lut": 10, "ff": 20, "bram36": 1, "bram18": 0, "uram": 1, "dsp": 1},
            "power_w": 1.0,
            "clock_frequency_mhz": 250.0,
            "performance_tokens_per_second": 170.0,
        }

        def facts(_state: dict[str, object], key: str) -> dict[str, object]:
            if key == "constraint.arch.design_space":
                return {
                    "qor_targets": {
                        "clock_frequency_mhz": 250.0,
                        "performance_tokens_per_second": 170.0,
                        "performance_comparison": ">",
                    }
                }
            return {"board": {"resource_budget": {"lut": 100, "ff": 100, "bram": 10, "uram": 10, "dsp": 10}}}

        with patch("accagent.framework.stage_backend.constraint_facts", side_effect=facts):
            result = classify_qor_optimization({}, metrics)

        self.assertEqual(result["decision"], "llm_required")
        self.assertEqual(result["misses"][0]["metric"], "performance_tokens_per_second")
        self.assertEqual(result["misses"][0]["comparison"], ">")

    def test_legacy_synthesis_throughput_cannot_route_dse(self) -> None:
        result = classify_qor_optimization({}, {
            "measurement_scope": SYNTHESIS_KERNEL_SCOPE,
            "resources": {"lut": 10, "ff": 20, "dsp": 3},
            "clock_frequency_mhz": 230.0,
            "performance_tokens_per_second": 0.6464,
        })
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["decision"], "continue_backend")
        self.assertIn("stale QoR", result["reason"])

    def test_separate_bram36_and_bram18_budgets_are_checked_without_double_counting(self) -> None:
        metrics = {
            "resources": {"lut": 10, "ff": 20, "bram36": 1, "bram18": 5, "uram": 1, "dsp": 1},
            "power_w": 1.0,
            "clock_frequency_mhz": 250.0,
            "performance_tokens_per_second": 200.0,
        }

        def facts(_state: dict[str, object], key: str) -> dict[str, object]:
            if key == "constraint.arch.design_space":
                return {"qor_targets": {}}
            return {"board": {"resource_budget": {"lut": 100, "ff": 100, "bram36": 2, "bram18": 4, "uram": 10, "dsp": 10}}}

        with patch("accagent.framework.stage_backend.constraint_facts", side_effect=facts):
            result = classify_qor_optimization({}, metrics)

        self.assertEqual(result["decision"], "llm_required")
        self.assertEqual(result["misses"][0]["metric"], "resources.bram18")

    def test_exact_dse_backtrack_is_identified_across_public_stage_aliases(self) -> None:
        request = {
            "target_stage": "stage4.parameter_binding",
            "verification_scope": "formal_dse_campaign",
        }
        self.assertTrue(is_formal_dse_backtrack(request, "parameter_binding"))

    def test_only_complete_exact_app_shell_qor_enters_the_measurement_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            binding = run_dir / "parameter_binding" / "parameter_binding.json"
            binding.parent.mkdir()
            self.binding(binding)
            self.exact_qor(run_dir)

            result = record_exact_dse_measurement(self.state_for(binding), run_dir)
            latest = load_latest(run_dir / "parameter_binding" / "dse_measurements.jsonl")

        self.assertEqual(result["status"], "recorded")
        self.assertEqual(result["measurement_status"], "measured")
        self.assertEqual(len(latest), 1)
        self.assertEqual(next(iter(latest.values()))["measurement_scope"], EXACT_TARGET_BOARD_APP_SHELL_SCOPE)

    def test_synthesis_qor_with_source_cycles_enters_measurement_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            binding = run_dir / "parameter_binding" / "parameter_binding.json"
            binding.parent.mkdir()
            self.binding(binding)
            diagnostics = run_dir / "backend_board" / "case_diagnostics"
            diagnostics.mkdir(parents=True)
            report = diagnostics / "app_shell_runtime_vivado.json"
            report.write_text(json.dumps({"mode": "synth", "status": "pass", "measurement_scope": SYNTHESIS_KERNEL_SCOPE}), encoding="utf-8")
            reports_dir = run_dir / "app_shell_runtime_bitstream"
            reports_dir.mkdir()
            utilization = reports_dir / "app_shell_synth_utilization.rpt"
            timing = reports_dir / "app_shell_synth_timing.rpt"
            power = reports_dir / "app_shell_synth_power.rpt"
            counter = run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"
            metrics_path = run_dir / "backend_board" / "qor" / "qor_metrics.json"
            for path in (utilization, timing, power, counter):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("present\n", encoding="utf-8")
            metrics_path.parent.mkdir(parents=True)
            evidence_paths = [
                str(path.resolve())
                for path in [report, utilization, timing, power, counter, metrics_path]
            ]
            metrics_path.write_text(
                json.dumps(
                    {
                        "measurement_scope": SYNTHESIS_KERNEL_SCOPE,
                        "resource_top": "CustomGeneratedKernel",
                        "resource_boundary": "generated_top_with_external_ports_excluding_board_shell",
                        "evidence_paths": evidence_paths,
                        "resources": {"lut": 10, "ff": 20, "bram36": 1, "bram18": 0, "uram": 2, "dsp": 3},
                        "power_w": None,
                        "clock_frequency_mhz": 200.0,
                        "performance_tokens_per_second": 1_000.0,
                        "performance_model": "single_block_reuse_operator_token_pipeline_v1",
                    }
                ),
                encoding="utf-8",
            )

            result = record_exact_dse_measurement(self.state_for(binding), run_dir)
            latest = load_latest(run_dir / "parameter_binding" / "dse_measurements.jsonl")

        self.assertEqual(result["status"], "recorded")
        self.assertEqual(next(iter(latest.values()))["measurement_scope"], SYNTHESIS_KERNEL_SCOPE)
        self.assertEqual(next(iter(latest.values()))["metrics"]["resource_top"], "CustomGeneratedKernel")

    def test_explicit_app_shell_implementation_failure_records_only_infeasible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            binding = run_dir / "parameter_binding" / "parameter_binding.json"
            binding.parent.mkdir()
            self.binding(binding)
            report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
            report.parent.mkdir(parents=True)
            report.write_text(
                json.dumps(
                    {
                        "mode": "bitstream",
                        "status": "fail",
                        "summary": "place failed",
                        "inspection": {"top_impl_status": "place_design failed"},
                    }
                ),
                encoding="utf-8",
            )

            result = record_exact_dse_measurement(self.state_for(binding), run_dir)
            latest = load_latest(run_dir / "parameter_binding" / "dse_measurements.jsonl")

        self.assertEqual(result["measurement_status"], "infeasible")
        row = next(iter(latest.values()))
        self.assertEqual(row["measurement_status"], "infeasible")
        self.assertIsNone(row["metrics"])


if __name__ == "__main__":
    unittest.main()
