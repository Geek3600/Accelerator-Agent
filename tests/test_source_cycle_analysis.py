from __future__ import annotations

import json
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.source_cycle_analysis import (
    MAX_EMITTED_RTL_SOURCE_BYTES,
    _chisel_class_index,
    _cycle_analysis_prompt_sources,
    analysis_path,
    ensure_source_cycle_analysis,
    pipeline_cycle_total,
    source_context,
)
from scripts.synthesis.app_shell_runtime_vivado import create_source_closure_archive
from scripts.synthesis import case_stage7_metrics as metrics


class SourceCycleAnalysisTest(unittest.TestCase):
    def test_chisel_class_index_keeps_module_instances_in_declaring_scope(self) -> None:
        source = """class FloatingAttention extends Module {
  val softmax = Module(new Softmax(p.softmax))
}
class IntegerAttention extends Module {
  val divider = Module(new IntegerDivider(p.width))
}
class Attention extends Module {
  if (p.integerMode) {
    val core = Module(new IntegerAttention(p))
  } else {
    val core = Module(new FloatingAttention(p))
  }
}
"""
        scopes = {entry["class"]: entry for entry in _chisel_class_index({"Attention.scala": source})}

        self.assertEqual(
            [item["module"] for item in scopes["FloatingAttention"]["module_instantiations"]],
            ["Softmax"],
        )
        self.assertEqual(
            [item["module"] for item in scopes["IntegerAttention"]["module_instantiations"]],
            ["IntegerDivider"],
        )
        self.assertEqual(
            [item["module"] for item in scopes["Attention"]["module_instantiations"]],
            ["IntegerAttention", "FloatingAttention"],
        )

    def test_prompt_keeps_design_sources_and_indexes_expanded_rtl(self) -> None:
        sources = {
            "generated/chisel/src/main/scala/templates/Linear.scala": "class Linear {}\n",
            "generated/chisel/src/main/scala/generated/GeneratedDesignParams.scala": "object GeneratedDesignParams {}\n",
            "generated/chisel/runtime/runtime_config.json": "{}\n",
            "generated/chisel/vivado/GeneratedAcceleratorTop.sv": "module GeneratedAcceleratorTop; endmodule\n",
            "generated/chisel/vivado/PhysicalFp32MulPipeline.sv": "module PhysicalFp32MulPipeline; endmodule\n",
            "generated/chisel/vivado/PhysicalSimpleDualPortMemory.sv": "module PhysicalSimpleDualPortMemory; endmodule\n",
            "generated/chisel/vivado/Linear.sv": "module Linear;\n" + ("x" * MAX_EMITTED_RTL_SOURCE_BYTES),
            "generated/chisel/src/main/resources/table.memh": "0000\n",
        }

        prompt_sources, omitted = _cycle_analysis_prompt_sources(sources)

        self.assertIn("generated/chisel/src/main/scala/templates/Linear.scala", prompt_sources)
        self.assertIn("generated/chisel/src/main/scala/generated/GeneratedDesignParams.scala", prompt_sources)
        self.assertIn("generated/chisel/runtime/runtime_config.json", prompt_sources)
        self.assertIn("generated/chisel/vivado/GeneratedAcceleratorTop.sv", prompt_sources)
        self.assertIn("generated/chisel/vivado/PhysicalFp32MulPipeline.sv", prompt_sources)
        self.assertEqual(
            {item["path"] for item in omitted},
            {
                "generated/chisel/vivado/Linear.sv",
                "generated/chisel/vivado/PhysicalSimpleDualPortMemory.sv",
            },
        )

    def test_single_reused_block_overlaps_tokens_but_serializes_model_layers(self) -> None:
        schedule = {
            "mode": "single_block_reuse", "operator_token_overlap": True,
            "start_to_first_input_cycles": 2, "steady_state_ii_cycles": 4,
            "last_token_start_to_completion_cycles": 6, "exposed_layer_handoff_cycles": 3,
        }
        self.assertEqual(pipeline_cycle_total(schedule, 5, 12), 12 * (2 + 4 * 4 + 6))
        with self.assertRaisesRegex(ValueError, "single reused transformer block"):
            pipeline_cycle_total({**schedule, "mode": "overlapped_token_pipeline"}, 5, 12)

    def test_nonuniform_ingress_gaps_are_not_replaced_by_steady_state_ii(self) -> None:
        schedule = {
            "mode": "single_block_reuse", "operator_token_overlap": True,
            "start_to_first_input_cycles": 0, "steady_state_ii_cycles": 10,
            "last_token_start_to_completion_cycles": 20, "exposed_layer_handoff_cycles": 0,
            "token_start_intervals": [{"cycles": 2, "repetitions": 1}, {"cycles": 10, "repetitions": 3}],
        }
        self.assertEqual(pipeline_cycle_total(schedule, 5, 12), 12 * (2 + 30 + 20))
        with self.assertRaisesRegex(ValueError, "exactly"):
            pipeline_cycle_total(schedule, 6, 12)

    def make_sources(self, run_dir: Path) -> dict:
        source = run_dir / "generated/chisel/src/main/scala/Design.scala"
        source.parent.mkdir(parents=True)
        source.write_text("object Design { val tokens = 2; val layers = 3 }\n", encoding="utf-8")
        top = run_dir / "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala"
        top.parent.mkdir(parents=True)
        top.write_text(
            "class GeneratedAcceleratorTop { val core = Module(new ExampleBlock(p)) }\n",
            encoding="utf-8",
        )
        (top.parent / "GeneratedDesignParams.scala").write_text(
            'object GeneratedDesignParams {\nval modelType: String = "example_decoder"\n'
            'val computeArrayRows: Int = 1\nval computeArrayCols: Int = 1\n}\n',
            encoding="utf-8",
        )
        block = run_dir / "generated/chisel/src/main/scala/spatialaccagent/templates/ExampleBlock.scala"
        block.parent.mkdir(parents=True)
        block.write_text(
            """class ExampleBlock extends Module {
  val io = IO(new Bundle { val in = Flipped(Decoupled(UInt(8.W))); val out = Decoupled(UInt(8.W)) })
  first.io.out <> second.io.in
}
""",
            encoding="utf-8",
        )
        runtime = run_dir / "generated/chisel/runtime/runtime_config.json"
        runtime.parent.mkdir(parents=True)
        runtime.write_text(
            json.dumps({
                "board": {"fpga_part": "test_part"},
                "params": {
                    "lanes": 1,
                    "elem_bits": 16,
                    "cache_refill_data_width_bits": 512,
                    "cross_token_reuse_tokens": 2,
                },
                "memory_layout": {
                    "num_layers": 3, "tensor_shape": {"seq_len": 2, "hidden_size": 2},
                    "axi_data_width_bits": 512,
                    "weight_storage_terms": [{"stage": "linear", "physical_role": "weight", "elements": 4, "element_bits": 16, "factors": ["hidden_size", "hidden_size"]}],
                    "transfer_rules": ["alternate weight buffers and prefetch next-layer weights during compute"],
                },
                "run_sequence": ["prefetch next layer weights while current layer computes"],
            }),
            encoding="utf-8",
        )
        rtl = run_dir / "generated/chisel/vivado/GeneratedAxiDdrTop.sv"
        rtl.parent.mkdir(parents=True)
        rtl.write_text("module GeneratedAxiDdrTop(input clock); endmodule\n", encoding="utf-8")
        modules = run_dir / "generated/chisel/simulation/fpga_ip_modules.txt"
        modules.parent.mkdir(parents=True)
        modules.write_text("fp_add_sp_12\n", encoding="utf-8")
        ip_tcl = run_dir / "generated/chisel/scripts/gen_xilinx_fp_ips_23.tcl"
        ip_tcl.parent.mkdir(parents=True)
        ip_tcl.write_text("puts fp_ip\n", encoding="utf-8")
        archive = run_dir / "generated/backend/scripts/app_shell_generated_vivado_closure.tar.gz"
        create_source_closure_archive(archive, rtl.parent, modules, ip_tcl)
        report = run_dir / "backend_board/case_diagnostics/app_shell_runtime_vivado.json"
        report.parent.mkdir(parents=True)
        report.write_text(json.dumps({
            "status": "pass",
            "mode": "synth",
            "measurement_scope": "generated_kernel_synthesis",
            "closure_archive": str(archive),
            "synthesis_source_archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "commands": [{"argv": ["scp", str(archive), "remote:/run/"]}],
        }), encoding="utf-8")
        return {"output": {
            "status": "ready", "latency_cycles": 999, "processed_tokens": 2,
            "pipeline_schedule": {
                "mode": "single_block_reuse", "operator_token_overlap": True,
                "start_to_first_input_cycles": 0, "steady_state_ii_cycles": 5,
                "last_token_start_to_completion_cycles": 7, "exposed_layer_handoff_cycles": 3,
            },
            "model_layers": 3, "derivation": "One streamed pass takes 12 cycles; three reused layer passes have two exposed handoffs.",
            "assumptions": ["Weights are prefetched without exposed delay beyond the stated handoff."],
            "source_refs": [str(top.relative_to(run_dir)), str(block.relative_to(run_dir))],
        }}

    def test_reuses_analysis_only_for_unchanged_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result) as agent:
                path = ensure_source_cycle_analysis(root)
                ensure_source_cycle_analysis(root)
                self.assertEqual(agent.call_count, 1)
                self.assertEqual(json.loads(path.read_text())["latency_cycles"], 36)
                self.assertEqual(json.loads(path.read_text())["pipeline_schedule"]["exposed_layer_handoff_cycles"], 0)
                self.assertAlmostEqual(metrics.parse_performance_tokens_per_second(path, 100.0, None), 2 * 100_000_000 / 36)
                self.assertIsNone(metrics.parse_performance_tokens_per_second(path, 100.0, 3))
                rtl = root / "generated/chisel/vivado/GeneratedAxiDdrTop.sv"
                rtl.write_text(rtl.read_text() + "\n", encoding="utf-8")
                self.assertAlmostEqual(metrics.parse_performance_tokens_per_second(path, 100.0, None), 2 * 100_000_000 / 36)
                modules = root / "generated/chisel/simulation/fpga_ip_modules.txt"
                ip_tcl = root / "generated/chisel/scripts/gen_xilinx_fp_ips_23.tcl"
                archive = root / "generated/backend/scripts/app_shell_generated_vivado_closure.tar.gz"
                create_source_closure_archive(archive, rtl.parent, modules, ip_tcl)
                synthesis_report = root / "backend_board/case_diagnostics/app_shell_runtime_vivado.json"
                synthesis = json.loads(synthesis_report.read_text())
                synthesis["synthesis_source_archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
                synthesis_report.write_text(json.dumps(synthesis), encoding="utf-8")
                self.assertIsNone(metrics.parse_performance_tokens_per_second(path, 100.0, None))
                ensure_source_cycle_analysis(root)
                self.assertEqual(agent.call_count, 2)

    def test_total_cycles_are_computed_instead_of_trusting_llm_arithmetic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            result["output"]["latency_cycles"] = 999
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result):
                path = ensure_source_cycle_analysis(root)
            self.assertEqual(json.loads(path.read_text())["latency_cycles"], 36)

    def test_cycle_reanalysis_receives_repair_disagreement_and_current_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            analysis_dir = root / "backend_board/qor/cycle_analysis/llm"
            analysis_dir.mkdir(parents=True)
            previous = {"status": "blocked", "derivation": "A producer waits for a chunk output."}
            (analysis_dir / "source_cycle_analysis_agent_result.json").write_text(json.dumps({"output": previous}))
            repair_dir = root / "backend_board/timing_optimization/current"
            repair_dir.mkdir(parents=True)
            feedback = {
                "status": "compiled_pending_vcs", "changed_sources": ["Attention.scala"],
                "implementation_summary": "Producer now feeds later rows independently of output retirement.",
            }
            (repair_dir / "application.json").write_text(json.dumps(feedback))
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result) as agent:
                ensure_source_cycle_analysis(root)
            inputs = agent.call_args.kwargs["inputs"]
            self.assertEqual(inputs["previous_attempt_for_correction_only"], previous)
            self.assertEqual(inputs["latest_repair_feedback_for_source_recheck"]["implementation_summary"],
                             feedback["implementation_summary"])
            self.assertIn("generated/chisel/src/main/scala/Design.scala", inputs["sources"])
            self.assertTrue(any("exact current branch and guard" in rule
                                for rule in agent.call_args.kwargs["prompt_rules"]))
            self.assertTrue(any("Use chisel_class_index" in rule
                                for rule in agent.call_args.kwargs["prompt_rules"]))

    def test_explicit_double_buffer_prefetch_uses_no_stall_handoff_assumption(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result) as agent:
                ensure_source_cycle_analysis(root)
            rules = agent.call_args.kwargs["prompt_rules"]
            self.assertTrue(any("assume inter-layer weight handoff is zero" in rule for rule in rules))
            self.assertTrue(any("not a measured whole-system result" in rule for rule in rules))
            self.assertTrue(agent.call_args.kwargs["inputs"]["schedule_policy"]["runtime_constants_preloaded"])
            self.assertIn(
                "one accepted top-level io.start per model-layer pass",
                agent.call_args.kwargs["inputs"]["schedule_policy"]["layer_start_contract"],
            )
            self.assertTrue(any("rather than requiring external controller RTL" in rule for rule in rules))
            self.assertTrue(any("nominal analytical precondition" in rule for rule in rules))
            self.assertTrue(any("driver of the block's final io_out port" in rule for rule in rules))
            evidence = agent.call_args.kwargs["inputs"]["synthesis_evidence"]
            self.assertTrue(evidence["framework_verified_source_binding"])
            self.assertEqual(evidence["status"], "pass")
            saved = json.loads(analysis_path(root).read_text())
            self.assertEqual(saved["pipeline_schedule"]["exposed_layer_handoff_cycles"], 0)

    def test_legacy_analysis_without_schedule_terms_is_regenerated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result) as agent:
                path = ensure_source_cycle_analysis(root)
                cached = json.loads(path.read_text())
                del cached["pipeline_schedule"]
                path.write_text(json.dumps(cached), encoding="utf-8")
                self.assertIsNone(metrics.parse_performance_tokens_per_second(path, 100.0, None))
                ensure_source_cycle_analysis(root)
            self.assertEqual(agent.call_count, 2)

    def test_blocked_analysis_does_not_invent_a_counter_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            result["output"]["status"] = "blocked"
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result):
                with self.assertRaisesRegex(ValueError, "incomplete"):
                    ensure_source_cycle_analysis(root)
            self.assertFalse(analysis_path(root).exists())
            self.assertFalse((root / "verification/board_simulation/reports/performance_counter_report.json").exists())

    def test_pipeline_evidence_uses_the_synthesis_context_not_citation_spelling(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            result["output"]["source_refs"] = ["generated/chisel/vivado/GeneratedAxiDdrTop.sv"]
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result):
                path = ensure_source_cycle_analysis(root)
            self.assertEqual(json.loads(path.read_text())["latency_cycles"], 36)

    def test_workload_counts_must_match_runtime_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            result["output"]["model_layers"] = 12
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result):
                with self.assertRaisesRegex(ValueError, "disagrees with the synthesized runtime workload"):
                    ensure_source_cycle_analysis(root)

    def test_rejects_sources_changed_during_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)

            def change_source(**kwargs):
                source = root / "generated/chisel/src/main/scala/Design.scala"
                source.write_text("object NewDesign {}\n", encoding="utf-8")
                modules = root / "generated/chisel/simulation/fpga_ip_modules.txt"
                ip_tcl = root / "generated/chisel/scripts/gen_xilinx_fp_ips_23.tcl"
                rtl = root / "generated/chisel/vivado"
                archive = root / "generated/backend/scripts/app_shell_generated_vivado_closure.tar.gz"
                create_source_closure_archive(archive, rtl, modules, ip_tcl)
                report = root / "backend_board/case_diagnostics/app_shell_runtime_vivado.json"
                synthesis = json.loads(report.read_text())
                synthesis["synthesis_source_archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
                report.write_text(json.dumps(synthesis), encoding="utf-8")
                return result

            with patch("accagent.framework.stage_llm.run_stage_agent", side_effect=change_source):
                with self.assertRaisesRegex(ValueError, "sources changed"):
                    ensure_source_cycle_analysis(root)
            self.assertFalse(analysis_path(root).exists())

    def test_cycle_context_uses_latest_synthesis_archive_not_live_rtl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_sources(root)
            live_rtl = root / "generated/chisel/vivado/GeneratedAxiDdrTop.sv"
            live_rtl.write_text("module ChangedTop(input clock); endmodule\n", encoding="utf-8")
            context = source_context(root)
            self.assertIn("module GeneratedAxiDdrTop", context["sources"]["generated/chisel/vivado/GeneratedAxiDdrTop.sv"])
            self.assertNotIn("module ChangedTop", context["sources"]["generated/chisel/vivado/GeneratedAxiDdrTop.sv"])
            self.assertEqual(context["schedule_policy"]["mode"], "nominal_no_stall")
            self.assertEqual(context["schedule_policy"]["physical_transformer_blocks"], 1)
            self.assertEqual(context["workload"]["processed_tokens"], 2)
            self.assertEqual(context["workload"]["model_layers"], 3)
            self.assertEqual(context["workload"]["axi_data_width_bits"], 512)

    def test_cycle_context_accepts_recovered_synthesis_with_verified_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_sources(root)
            report = root / "backend_board/case_diagnostics/app_shell_runtime_vivado.json"
            synthesis = json.loads(report.read_text(encoding="utf-8"))
            synthesis["collect_only"] = True
            report.write_text(json.dumps(synthesis), encoding="utf-8")

            context = source_context(root)

        self.assertEqual(context["synthesis_source_archive_sha256"], synthesis["synthesis_source_archive_sha256"])

    def test_matching_compiled_cycle_analysis_is_promoted_without_another_llm_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            synthesis_report = json.loads(
                (root / "backend_board/case_diagnostics/app_shell_runtime_vivado.json").read_text(encoding="utf-8")
            )
            compile_context = source_context(root)
            compile_context.update(
                synthesis_source_archive_sha256=None,
                compiled_source_snapshot_sha256="compile-snapshot",
                compile_evidence={"status": "ready", "validation_policy": "vcs_compile_only"},
            )
            with patch("accagent.framework.dse_timing_calibration.compiled_source_context", return_value=compile_context), patch(
                "accagent.framework.stage_llm.run_stage_agent", return_value=result
            ):
                compiled_path = ensure_source_cycle_analysis(root, context_override=compile_context)
            with patch("accagent.framework.dse_timing_calibration.compiled_source_context", return_value=compile_context), patch(
                "accagent.framework.stage_llm.run_stage_agent", side_effect=AssertionError("analysis should be reused")
            ):
                synthesis_path = ensure_source_cycle_analysis(root)
            compiled = json.loads(compiled_path.read_text(encoding="utf-8"))
            synthesis = json.loads(synthesis_path.read_text(encoding="utf-8"))

        self.assertEqual(synthesis["status"], "pass")
        self.assertEqual(synthesis["latency_cycles"], compiled["latency_cycles"])
        self.assertEqual(synthesis["synthesis_source_archive_sha256"], synthesis_report["synthesis_source_archive_sha256"])
        self.assertEqual(synthesis["analysis_reuse"]["kind"], "matching_compiled_source_analysis")

    def test_rejects_source_archive_newer_than_latest_synthesis_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_sources(root)
            archive = root / "generated/backend/scripts/app_shell_generated_vivado_closure.tar.gz"
            report = root / "backend_board/case_diagnostics/app_shell_runtime_vivado.json"
            newer = report.stat().st_mtime_ns + 1_000_000
            os.utime(archive, ns=(newer, newer))
            with self.assertRaisesRegex(ValueError, "newer synthesis source archive"):
                source_context(root)

    def test_metrics_automatically_collect_source_cycles_after_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.make_sources(root)
            app_shell = root / "backend_board/case_diagnostics/app_shell_runtime_vivado.json"
            reports = root / "app_shell_runtime_bitstream"
            reports.mkdir()
            (reports / "app_shell_synth_utilization.rpt").write_text(
                "| Instance | Total LUTs | FFs | RAMB36 | RAMB18 | URAM | DSP Blocks |\n"
                "| top | 100 | 200 | 3 | 4 | 5 | 6 |\n", encoding="utf-8",
            )
            (reports / "app_shell_synth_timing.rpt").write_text(
                "WNS(ns)\n----\n 0.000\n\nclk {0.000 5.000} 10.000 100.000\n", encoding="utf-8",
            )
            output = root / "backend_board/qor/qor_metrics.json"
            with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result) as agent, patch(
                "accagent.framework.dse_calibration.SAMPLE_DIR", root / "calibration"
            ):
                self.assertEqual(metrics.main(["--run-dir", str(root), "--out", str(output)]), 0)
            report = json.loads(output.read_text())
            self.assertEqual(report["metric_quality"], "post_synthesis_clock_and_analytical_source_cycles")
            self.assertEqual(report["performance_estimation"]["measurement_kind"], "analytical_estimate")
            self.assertIn(str(analysis_path(root)), report["evidence_paths"])
            self.assertIsNone(report["power_w"])
            agent.assert_called_once()

    def test_incomplete_cycle_analysis_preserves_available_synthesis_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_sources(root)
            app_shell = root / "backend_board/case_diagnostics/app_shell_runtime_vivado.json"
            app_shell.parent.mkdir(parents=True, exist_ok=True)
            app_shell.write_text('{"mode": "synth", "status": "pass"}\n', encoding="utf-8")
            reports = root / "app_shell_runtime_bitstream"
            reports.mkdir()
            (reports / "app_shell_synth_utilization.rpt").write_text(
                "| Instance | Total LUTs | FFs | RAMB36 | RAMB18 | URAM | DSP Blocks |\n"
                "| top | 100 | 200 | 3 | 4 | 5 | 6 |\n", encoding="utf-8",
            )
            (reports / "app_shell_synth_timing.rpt").write_text(
                "WNS(ns)\n----\n 0.000\n\nclk {0.000 5.000} 10.000 100.000\n", encoding="utf-8",
            )
            output = root / "backend_board/qor/qor_metrics.json"

            def pending_analysis(_run_dir: Path) -> None:
                partial = json.loads(output.read_text())
                self.assertEqual(partial["status"], "incomplete")
                self.assertEqual(partial["resources"]["lut"], 100)
                self.assertEqual(partial["clock_frequency_mhz"], 100)
                self.assertIsNone(partial["performance_tokens_per_second"])
                raise ValueError("missing kernel bounds")

            with patch("accagent.framework.source_cycle_analysis.ensure_source_cycle_analysis", side_effect=pending_analysis):
                self.assertEqual(metrics.main(["--run-dir", str(root), "--out", str(output)]), 1)
            report = json.loads(output.read_text())
        self.assertEqual(report["status"], "incomplete")
        self.assertEqual(report["resources"]["lut"], 100)
        self.assertEqual(report["clock_frequency_mhz"], 100)
        self.assertIsNone(report["performance_tokens_per_second"])
        self.assertEqual(report["performance_estimation_error"], "missing kernel bounds")
