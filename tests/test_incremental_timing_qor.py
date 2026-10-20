import hashlib
import json
import shutil
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from accagent.framework import codegen_source_repair as repair
from accagent.framework import stage_backend as backend
from accagent.framework.dse_ledger import candidate_fingerprint, DSE_ESTIMATED_CYCLE_MODEL
from scripts.synthesis import app_shell_runtime_vivado as synthesis
from scripts.synthesis import case_stage7_metrics as metrics
from tests import test_source_cycle_analysis as fixtures
from accagent.framework.prompt_source_encoding import encode_numbered_source, decode_numbered_source
from accagent.framework.stage_llm import compact_retry_prompt


class IncrementalTimingQorTest(unittest.TestCase):
    def test_run_local_timing_optimization_does_not_record_a_new_dse_candidate(self):
        import tempfile
        from argparse import Namespace
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            out = run / "backend_board"
            out.mkdir()
            (out / "optimization_request.json").write_text(json.dumps({
                "scope": "existing_design_timing", "clock_frequency_mhz": 150,
            }))
            args = Namespace(sacg_state=run / "verification/sacg_state.json")
            tools = [{"checker": "real_tool.app_shell_runtime_bitstream", "status": "pass"}]
            with patch.object(backend, "run_dir_from_state", return_value=run), \
                 patch.object(backend, "read_json", return_value={}), \
                 patch.object(backend, "check_upstream_hierarchical_verification_closure", return_value={"status":"pass"}), \
                 patch("accagent.framework.stage_backend.resolve_board_profile", return_value={"path":str(run/"board.json")}), \
                 patch.object(backend, "write_board_shell_contract"), \
                 patch.object(backend, "write_initial_app_shell_integration_contract"), \
                 patch.object(backend, "compiled_cycle_followup", return_value=None), \
                 patch.object(backend, "run_backend_real_tools", return_value=(tools, [])), \
                 patch.object(backend, "record_exact_dse_measurement", side_effect=AssertionError("timing optimization is not a DSE candidate")), \
                 patch.object(backend, "exact_dse_campaign", return_value={"status":"pending"}), \
                 patch.object(backend, "build_plan", return_value={"qor_optimization": {"decision":"pass"}, "qor": {}}) as build, \
                 patch.object(backend, "generate_backend_package", return_value={"root":str(run),"files":[]}), \
                 patch("accagent.framework.stage_backend.validated_stage6_selection", return_value={"status":"pass"}), \
                 patch.object(backend, "backend_llm_decision_packet", return_value={}), \
                 patch.object(backend, "write_json"), \
                 patch.object(backend, "scope_passed", return_value=True), \
                 patch.object(backend, "update_sacg", return_value="transition"), \
                 patch.object(backend, "backend_bounded_recovery", return_value={"status":"pass"}):
                backend.plan_backend_board(args)
            self.assertEqual(build.call_args.args[5]["status"], "not_recorded")

    def test_source_schedule_defect_repairs_existing_design_without_dse_backtrack(self):
        plan = {"qor": {"clock_frequency_mhz": 121,
                        "source_schedule_diagnosis": {"status": "blocked", "blocker_kind": "noncompleting_hardware_schedule", "derivation": "No outgoing state transition"}},
                "qor_optimization": {"decision": "continue_backend", "status": "unavailable"}}
        backend.apply_requested_qor_scope(plan, {"scope": "existing_design_timing", "clock_frequency_mhz": 150})
        self.assertEqual(plan["qor_optimization"]["decision"], "local_optimization")
        self.assertTrue(plan["qor_optimization"]["preserve_existing_hardware"])
        plan["qor"]["source_schedule_diagnosis"] = {"status": "llm_error", "derivation": "HTTP 503"}
        plan["qor_optimization"] = {"decision": "continue_backend"}
        backend.apply_requested_qor_scope(plan, {"scope": "existing_design_timing", "clock_frequency_mhz": 150})
        self.assertEqual(plan["qor_optimization"]["decision"], "continue_backend")

    def test_blocked_patch_retry_keeps_last_compiler_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            source = run / "generated/chisel/src/main/scala/spatialaccagent/templates/Operator.scala"
            source.parent.mkdir(parents=True)
            source.write_text("class Operator")
            out = run / "backend_board"
            digest = "a" * 64
            attempt = out / "timing_optimization" / digest[:20]
            attempt.mkdir(parents=True)
            (attempt / "application.json").write_text(json.dumps({"status": "blocked", "blockers": ["anchor mismatch"]}))
            rejected = {"path": str(source), "text_replacements": [
                {"old_text": "when (state === sProjectRead)", "new_text": "replacement"}
            ]}
            (attempt / "agent_patch_application.json").write_text(json.dumps({
                "agent_transaction_rejection": {
                    "blockers": ["anchor matched twice"], "rejected_file_edits": [rejected]
                }
            }))
            (attempt / "incremental_compile.log").write_text("compiler: missing state in Attention.scala")
            diagnosis_path = out / "qor/compiled_cycle_analysis/llm/source_cycle_analysis_agent_result.json"
            diagnosis_path.parent.mkdir(parents=True)
            diagnosis = {"status": "blocked", "blocker_kind": "noncompleting_hardware_schedule",
                         "derivation": "Nested projection never receives the repeated-layer start."}
            diagnosis_path.write_text(json.dumps({"output": diagnosis}))
            context = {"synthesis_source_archive_sha256": digest, "sources": {}, "workload": {}}
            with patch("accagent.framework.source_cycle_analysis.source_context", return_value=context), patch.object(
                repair, "run_stage_agent", return_value={"output": {"status": "blocked", "file_edits": []}}
            ) as agent:
                repair.repair_timing_sources(run, out, {"critical_timing_path": {"source": "a", "destination": "b"}})
            feedback = agent.call_args.kwargs["inputs"]["previous_repair_feedback"]
            self.assertIn("Attention.scala", feedback["compiler_diagnostics"])
            self.assertEqual(feedback["patch_rejection_feedback"]["rejected_file_edits"], [rejected])
            self.assertEqual(agent.call_args.kwargs["inputs"]["latest_schedule_feedback_for_source_recheck"]["diagnosis"],
                             diagnosis)

    def test_stale_synthesis_context_falls_back_to_current_vcs_verified_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            source = run / "generated/chisel/src/main/scala/spatialaccagent/templates/Attention.scala"
            source.parent.mkdir(parents=True)
            source.write_text("class Attention")
            out = run / "backend_board"
            context = {"synthesis_source_archive_sha256": None,
                       "compiled_source_snapshot_sha256": "current-vcs-snapshot",
                       "sources": {"GeneratedDesignParams.scala": "class Params"}, "workload": {}}
            with patch("accagent.framework.source_cycle_analysis.source_context",
                       side_effect=ValueError("a newer synthesis source archive is not covered by the latest synthesis report")), \
                 patch("accagent.framework.dse_timing_calibration.compiled_source_context", return_value=context), \
                 patch.object(repair, "run_stage_agent", return_value={"output": {"status": "blocked", "file_edits": []}}) as agent:
                result = repair.repair_timing_sources(
                    run, out, {"critical_timing_path": {"source": "src", "destination": "dst"}})
            self.assertEqual(result["status"], "blocked")
            self.assertIn("Attention.scala", next(iter(agent.call_args.kwargs["inputs"]["source_snapshots"])))
            self.assertEqual(agent.call_args.kwargs["inputs"]["synthesis_source_archive_sha256"], "current-vcs-snapshot")

    def test_compiled_timing_patch_can_continue_after_current_vcs_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            source = run / "generated/chisel/src/main/scala/spatialaccagent/templates/Attention.scala"
            source.parent.mkdir(parents=True)
            source.write_text("class Attention")
            out = run / "backend_board"
            digest = "b" * 64
            attempt = out / "timing_optimization" / digest[:20]
            attempt.mkdir(parents=True)
            (attempt / "application.json").write_text(json.dumps({
                "status": "compiled_pending_vcs", "changed_sources": [str(source)]
            }))
            context = {"synthesis_source_archive_sha256": digest, "sources": {}, "workload": {}}
            with patch("accagent.framework.source_cycle_analysis.source_context", return_value=context), \
                 patch("accagent.framework.stage_repair_execute.stage2_compile_only_authority",
                       return_value={"status": "ready"}), \
                 patch.object(repair, "run_stage_agent", return_value={"output": {"status": "blocked", "file_edits": []}}) as agent:
                result = repair.repair_timing_sources(
                    run, out, {"critical_timing_path": {"source": "src", "destination": "dst"},
                               "source_schedule_diagnosis": {"blocker_kind": "noncompleting_hardware_schedule"}})
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(agent.call_count, 1)

    def test_pending_timing_patch_recompiles_before_any_backend_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            state = run / "backend_board/sacg_state.json"
            state.parent.mkdir()
            state.write_text("{}")
            application = state.parent / "timing_optimization/current/application.json"
            application.parent.mkdir(parents=True)
            application.write_text(json.dumps({"status": "compiled_pending_vcs"}))
            with patch("accagent.framework.stage_repair_execute.stage2_compile_only_authority",
                       return_value={"status": "stale"}), patch.object(
                    backend, "check_upstream_hierarchical_verification_closure",
                    side_effect=AssertionError("no backend processing before current-source VCS")):
                _, report = backend.plan_backend_board(Namespace(sacg_state=state))
            self.assertTrue(report["stage6_refresh_required"])
            self.assertEqual(report["timing_source_repair"]["status"], "compiled_pending_vcs")

    def test_explicit_clock_goal_continues_after_throughput_target_passes(self):
        plan = {"qor": {"clock_frequency_mhz": 82.75},
                "qor_optimization": {"status": "pass", "decision": "pass",
                                     "targets": {"performance_tokens_per_second": 200}}}
        request = {"scope": "existing_design_timing", "clock_frequency_mhz": 100}
        backend.apply_requested_qor_scope(plan, request)
        self.assertEqual(plan["qor_optimization"]["decision"], "local_optimization")
        self.assertEqual(plan["qor_optimization"]["targets"]["clock_frequency_mhz"], 100)
        plan["qor"]["clock_frequency_mhz"] = 101
        plan["qor_optimization"]["decision"] = "llm_required"
        backend.apply_requested_qor_scope(plan, request)
        self.assertEqual(plan["qor_optimization"]["decision"], "pass")
        plan["qor_optimization"].update(decision="llm_required", misses=[{"metric": "resources.lut", "ratio": 1.1}])
        backend.apply_requested_qor_scope(plan, request)
        self.assertEqual(plan["qor_optimization"]["decision"], "local_optimization")
        self.assertEqual(plan["qor_optimization"]["misses"][0]["metric"], "resources.lut")

    def test_timing_patch_routes_before_promoting_stale_implementation_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "verification/sacg_state.json"
            state.parent.mkdir()
            state.write_text("{}")
            out = root / "backend_board"
            plan = {"timing_source_repair": {"status": "compiled_pending_vcs"},
                    "qor": {"clock_frequency_mhz": 47.17},
                    "qor_optimization": {"decision": "local_optimization"}}
            with patch.object(backend.SACGStore, "promote", side_effect=AssertionError("unvalidated implementation")):
                path, report = backend.timing_repair_followup(state, out, plan, [])
            self.assertTrue(report["stage6_refresh_required"])
            self.assertFalse(report["final_design_pass"])
            self.assertEqual(report["timing_source_repair"]["status"], "compiled_pending_vcs")
            self.assertEqual(json.loads(path.read_text()), report)
            plan["timing_source_repair"] = {"status": "compile_failed"}
            _, report = backend.timing_repair_followup(out / "sacg_state.json", out, plan, [])
            self.assertFalse(report["stage6_refresh_required"])
            self.assertEqual(report["bounded_recovery_actions"]["next_stage"], "stage7.backend_board")
            self.assertEqual(report["timing_source_repair"]["status"], "compile_failed")

    def test_best_qor_retains_better_source_and_ignores_unbound_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            backend = run / "backend_board"
            for name, frequency in [("better", 45.34), ("worse", 16.94)]:
                digest = hashlib.sha256(name.encode()).hexdigest()
                folder = backend / "measurements" / digest
                folder.mkdir(parents=True)
                archive = folder / "closure.tar.gz"
                archive.write_bytes(name.encode())
                (folder / "app_shell_runtime_vivado.json").write_text(json.dumps({
                    "status": "pass", "synthesis_source_archive_sha256": digest,
                    "closure_archive": str(archive)}))
                (folder / "qor_metrics.json").write_text(json.dumps({
                    "status": "pass", "measurement_scope": "kernel", "metric_quality": "estimated_cycles",
                    "clock_frequency_mhz": frequency, "performance_tokens_per_second": frequency * 10,
                    "performance_estimation": {"synthesis_source_archive_sha256": digest}}))
                metrics.preserve_best_qor(run)
                result = json.loads((backend / "best_qor.json").read_text())["groups"]["kernel:estimated_cycles"]
                self.assertEqual(result["best_clock"]["clock_frequency_mhz"], 45.34)
                self.assertAlmostEqual(result["best_throughput"]["performance_tokens_per_second"], 453.4)
            archive.write_bytes(b"replaced source")
            metric_path = folder / "qor_metrics.json"
            data = json.loads(metric_path.read_text())
            data["clock_frequency_mhz"] = 999.0
            metric_path.write_text(json.dumps(data))
            metrics.preserve_best_qor(run)
            result = json.loads((backend / "best_qor.json").read_text())["groups"]["kernel:estimated_cycles"]
            self.assertEqual(result["best_clock"]["clock_frequency_mhz"], 45.34)

    def test_completed_synthesis_snapshot_survives_new_source_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            archive = run / "closure.tar.gz"
            archive.write_bytes(b"original tool source closure")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            report = run / "report.json"
            report.write_text(json.dumps({"status": "pass", "closure_archive": str(archive),
                                          "synthesis_source_archive_sha256": digest}))
            folder = synthesis.preserve_successful_synthesis(run, report)
            archive.write_bytes(b"new design")
            synthesis.preserve_successful_synthesis(run, report)
            self.assertEqual((folder / archive.name).read_bytes(), b"original tool source closure")
            self.assertTrue(json.loads((folder / "snapshot.json").read_text())["original_archive_preserved"])

    def test_backend_priority_sources_and_module_headers_use_lossless_encoding(self):
        source = ''.join(f'wire [31:0] scale_{i} = cfg[{i}];\n' for i in range(36027))
        header = 'module Top (\n' + ''.join(f'input [31:0] scale_{i},\n' for i in range(36027)) + ');\n'
        inputs = {"source_snapshot": {"path": "/run/adapter.sv", "content": source},
                  "generated_top_interface": {"path": "/run/Top.sv", "module_header": header},
                  "weight_stream_contract": {}, "exact_board_loader_source_context": {}}
        prompt = compact_retry_prompt("backend_compute_slot_repair_agent", "backend_board", "repair",
                                      inputs, {"properties": {"file_edits": {"type": "array"}}})
        self.assertIn("lossless_numbered_source_lines_v1", prompt)
        self.assertIn("numeric_columns", prompt)
        self.assertLess(len(prompt), (len(source) + len(header)) // 10)

    def test_backend_uses_stage6_compiled_nested_adapter_before_old_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            source = run / "generated/board_integration/rtl/custom.sv"
            source.parent.mkdir(parents=True)
            source.write_text("module Slot (input clock); endmodule")
            old = source.parent.parent / "Slot.v"
            old.write_text("module Slot (input old_clock); endmodule")
            manifest = run / "verification/board_simulation/board_simulation_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"source_files": [{"role": "compute_slot_adapter",
                "path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]}))
            self.assertEqual(backend.compute_slot_adapter_source_path(run, "Slot"), source.resolve())

    def test_anchor_binding_only_accepts_unique_identical_code_despite_comment_changes(self):
        source = 'when (valid) {\n // actual source comment\n result := "http://keep"\n}\n'
        old = 'when(valid) {\n // paraphrased comment\n result := "http://keep"\n}'
        edit = {"path": "source", "old_text": old, "new_text": "replacement"}
        bound = repair.bind_source_anchors([edit], {"source": source})
        self.assertEqual(source.count(bound[0]["old_text"]), 1)
        changed_code = dict(edit, old_text=old.replace('"http://keep"', '"http://changed"'))
        self.assertEqual(repair.bind_source_anchors([changed_code], {"source": source})[0]["old_text"], changed_code["old_text"])
        self.assertEqual(repair.bind_source_anchors([edit], {"source": source * 2})[0]["old_text"], old)
        for original, candidate in [('val ab = 1', 'val a b = 1'), ('a >= b', 'a > = b')]:
            edit = {"path": "source", "old_text": candidate, "new_text": "replacement"}
            self.assertEqual(repair.bind_source_anchors([edit], {"source": original})[0]["old_text"], candidate)

    def test_numbered_source_encoding_preserves_every_connection_and_irregular_line(self):
        text = 'module Adapter;\r\n' + ''.join(
            f'wire [31:0] scale_{i} = memory[{i + 2560}][39:8];\r\n' for i in range(36027))
        text += 'wire [7:0] special_0001 = 8\'h01;\nendmodule'
        encoded = encode_numbered_source(text)
        self.assertIsInstance(encoded, dict)
        self.assertEqual(decode_numbered_source(encoded), text)
        self.assertLess(len(json.dumps(encoded)), len(text) // 10)

    def test_explicit_timing_goal_continues_after_throughput_pass_and_stops_at_clock_goal(self):
        targets = {"clock_frequency_mhz": 100, "performance_tokens_per_second": 200}
        facts = {"constraint.arch.design_space": {"qor_targets": targets},
                 "constraint.deployment.board": {"board": {"resource_budget": {"lut": 1000}}}}
        metrics = {"measurement_scope": "generated_kernel_synthesis",
                   "performance_model": DSE_ESTIMATED_CYCLE_MODEL,
                   "resources": {"lut": 500}, "clock_frequency_mhz": 50,
                   "performance_tokens_per_second": 503.69}
        with patch.object(backend, "constraint_facts", side_effect=lambda state, key: facts[key]), \
                patch.object(backend, "artifact_path", side_effect=KeyError):
            plan = {"qor_optimization": backend.classify_qor_optimization({}, metrics)}
            backend.apply_requested_qor_scope(plan, {"scope": "existing_design_timing"})
            self.assertEqual(plan["qor_optimization"]["decision"], "local_optimization")
            self.assertEqual(plan["qor_optimization"]["next_stage"], "stage6.verification")
            self.assertEqual(plan["qor_optimization"]["misses"][0]["metric"], "clock_frequency_mhz")
            metrics["clock_frequency_mhz"] = 100
            plan = {"qor_optimization": backend.classify_qor_optimization({}, metrics)}
            backend.apply_requested_qor_scope(plan, {"scope": "existing_design_timing"})
            self.assertEqual(plan["qor_optimization"]["decision"], "pass")
            packet = backend.backend_qor_decision_packet(plan)
            self.assertEqual(packet["targets"]["clock_frequency_mhz"], 100)

    def fixture(self, root):
        fixtures.SourceCycleAnalysisTest().make_sources(root)
        folder = root / "parameter_binding"
        folder.mkdir()
        params = {"lanes": 1, "compute_array_rows": 1, "compute_array_cols": 1}
        selected = {"parameters": params, "candidate_fingerprint": candidate_fingerprint(params),
                    "structural_cost_proxy": {"cycles": 36}}
        (folder / "selected_architecture.json").write_text(json.dumps(selected))
        (folder / "parameter_binding.json").write_text(json.dumps({"selected_architecture_parameters": params}))
        return params

    def test_dse_cycles_require_current_binding_and_synthesized_parameters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            params = self.fixture(root)
            with patch("accagent.framework.stage_llm.run_stage_agent", side_effect=AssertionError("no cycle LLM")):
                path = metrics.ensure_dse_cycle_estimate(root)
            report = json.loads(path.read_text())
            self.assertEqual(report["performance_model"], DSE_ESTIMATED_CYCLE_MODEL)
            self.assertTrue(report["cycles_are_estimated"])
            self.assertFalse(report["rtl_cycles_measured"])
            self.assertAlmostEqual(metrics.parse_performance_tokens_per_second(path, 100, None, root), 2 * 100e6 / 36)
            binding = root / "parameter_binding/parameter_binding.json"
            binding.write_text(json.dumps({"selected_architecture_parameters": dict(params, lanes=2)}))
            self.assertIsNone(metrics.parse_performance_tokens_per_second(path, 100, None, root))
            with self.assertRaisesRegex(ValueError, "current parameter binding"):
                metrics.ensure_dse_cycle_estimate(root)

    def test_optimized_schedule_calibrates_compute_and_preserves_ddr(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            selection = root / "parameter_binding/selected_architecture.json"
            selected = json.loads(selection.read_text())
            selected["structural_cost_proxy"].update(
                compute_cycles_per_layer=5, initial_refill_cycles=20,
                cache_refill_service_cycles_per_layer=20,
            )
            selection.write_text(json.dumps(selected))
            request = root / "backend_board/optimization_request.json"
            request.write_text(json.dumps({"calibrate_timing_cycles": True}))
            analysis = {
                "output": {"status": "ready", "processed_tokens": 2, "model_layers": 3,
                    "pipeline_schedule": {"mode": "single_block_reuse", "operator_token_overlap": True,
                        "start_to_first_input_cycles": 2, "steady_state_ii_cycles": 4,
                        "last_token_start_to_completion_cycles": 6},
                    "derivation": "Two connected source-grounded pipeline stages.",
                    "assumptions": ["No external stalls."],
                    "source_refs": [
                        "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala",
                        "generated/chisel/src/main/scala/spatialaccagent/templates/ExampleBlock.scala",
                    ]}}
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=analysis) as agent:
                path = metrics.ensure_dse_cycle_estimate(root)
                metrics.ensure_dse_cycle_estimate(root)
            self.assertEqual(agent.call_count, 1)
            calibrated = json.loads(path.read_text())
            # 12 compute cycles per layer, 8 exposed prefetch cycles at each handoff.
            self.assertEqual(calibrated["latency_cycles"], 20 + 3 * 12 + 2 * 8)
            self.assertAlmostEqual(metrics.parse_performance_tokens_per_second(path, 100, None, root),
                                   2 * 100e6 / 72)
            calibrated["latency_cycles"] = 36
            path.write_text(json.dumps(calibrated))
            self.assertIsNone(metrics.parse_performance_tokens_per_second(path, 100, None, root))

    def test_enabling_calibration_does_not_reuse_original_dse_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            path = metrics.ensure_dse_cycle_estimate(root)
            (root / "backend_board/optimization_request.json").write_text(
                json.dumps({"calibrate_timing_cycles": True}))
            self.assertIsNone(metrics.parse_performance_tokens_per_second(path, 100, None, root))

    def test_synthesis_reuse_requires_identical_synthesis_inputs_clock_and_part(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            report_path = root / "backend_board/case_diagnostics/app_shell_runtime_vivado.json"
            report = json.loads(report_path.read_text())
            report.update(fpga_part="part", clock_target_mhz=100.0, collect_only=False)
            report_path.write_text(json.dumps(report))
            folder = root / "app_shell_runtime_bitstream"
            folder.mkdir()
            for name in ["app_shell_synth_utilization.rpt", "app_shell_synth_timing.rpt"]:
                (folder / name).write_text("real tool fixture")
            args = Namespace(mode="synth", collect_only=False, out=report_path, run_dir=root,
                             fpga_part="part", clock_target_mhz=100.0,
                             generated_vivado_dir=root / "generated/chisel/vivado",
                             ip_module_manifest=root / "generated/chisel/simulation/fpga_ip_modules.txt",
                             ip_generation_tcl=root / "generated/chisel/scripts/gen_xilinx_fp_ips_23.tcl")
            self.assertTrue(synthesis.reusable_kernel_synthesis(args))
            args.clock_target_mhz = 120.0
            self.assertFalse(synthesis.reusable_kernel_synthesis(args))
            args.clock_target_mhz = 100.0
            source = root / "generated/chisel/src/main/scala/Design.scala"
            source.write_text(source.read_text() + "// actual hardware change\n")
            report = json.loads(report_path.read_text())
            archive = Path(report["closure_archive"])
            preserved = root / "backend_board/measurements" / report["synthesis_source_archive_sha256"] / archive.name
            preserved.parent.mkdir(parents=True)
            shutil.copy2(archive, preserved)
            synthesis.create_source_closure_archive(
                archive, args.generated_vivado_dir, args.ip_module_manifest, args.ip_generation_tcl
            )
            self.assertTrue(synthesis.reusable_kernel_synthesis(args))
            basis = synthesis.kernel_synthesis_reuse_basis(args)
            self.assertFalse(basis["complete_source_payload_matches"])
            self.assertTrue(basis["synthesized_source_payload_matches"])
            self.assertFalse(basis["generator_source_context_matches"])
            self.assertEqual(Path(basis["closure_archive"]), preserved)
            rtl = root / "generated/chisel/vivado/GeneratedAxiDdrTop.sv"
            rtl.write_text(rtl.read_text() + "// synthesized hardware change\n")
            self.assertFalse(synthesis.reusable_kernel_synthesis(args))

    def test_timing_repair_applies_agent_patch_to_existing_design_without_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared = root / "accagent/framework/templates/operator_chisel/Operator.scala"
            shared.parent.mkdir(parents=True)
            shared.write_text("class Operator { val pipeline = false }\n")
            run = root / "accagent/runs/example"
            current = run / "generated/chisel/src/main/scala/spatialaccagent/templates/Operator.scala"
            current.parent.mkdir(parents=True)
            current.write_text(shared.read_text())
            path = str(current.resolve())
            context = {"synthesis_source_archive_sha256": "source-identity", "sources": {}, "workload": {}}
            output = {"output": {"status": "ready_to_apply", "file_edits": [
                {"path": path, "old_text": "pipeline = false", "new_text": "pipeline = true"}]}}
            timing = {"source": "operator/start_reg/C", "destination": "operator/end_reg/D", "logic_levels": 100}
            with patch.object(repair, "ROOT", root), patch("accagent.framework.architecture_implementation.ROOT", root), \
                    patch("accagent.framework.source_cycle_analysis.source_context", return_value=context), \
                    patch.object(repair, "run_stage_agent", return_value=output) as agent, \
                    patch.object(repair.subprocess, "run", return_value=Namespace(returncode=0)) as compiler:
                result = repair.repair_timing_sources(run, run / "backend_board", {"critical_timing_path": timing})
                self.assertEqual(result["status"], "compiled_pending_vcs")
                self.assertIn("pipeline = false", shared.read_text())
                self.assertFalse(result["shared_templates_modified"])
                self.assertIn("pipeline = true", current.read_text())
                self.assertEqual(agent.call_args.kwargs["inputs"]["critical_timing_path"], timing)
                self.assertNotIn("stage_code_generation", " ".join(compiler.call_args.args[0]))
                repair.repair_timing_sources(run, run / "backend_board", {"critical_timing_path": timing})
                agent.assert_called_once()
                compiler.assert_called_once()

    def test_worst_path_extracts_real_endpoint_and_logic_depth(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "timing.rpt"
            path.write_text("Slack (VIOLATED) : -55.018ns\n Source: stage/a/C\n Destination: stage/b/D\n"
                            "Data Path Delay: 58.908ns\n Logic Levels: 228 (CARRY8=103)\n Location Delay\n")
            result = metrics.parse_timing_bottleneck(path)
            self.assertEqual(result["logic_levels"], 228)
            self.assertEqual(result["destination"], "stage/b/D")
            self.assertEqual(result["report_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
