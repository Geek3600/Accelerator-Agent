import unittest

from accagent.framework.dse_timing_calibration import calibrated_cycle_terms


class TimingCycleCalibrationTest(unittest.TestCase):
    def test_compiled_schedule_analysis_cannot_claim_a_synthesized_source(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from tests.test_source_cycle_analysis import SourceCycleAnalysisTest
        from accagent.framework.source_cycle_analysis import source_context, ensure_source_cycle_analysis

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = SourceCycleAnalysisTest().make_sources(root)
            context = source_context(root)
            context.update(synthesis_source_archive_sha256=None,
                           compiled_source_snapshot_sha256="compiled-source",
                           compile_evidence={"status":"ready"})
            with patch("accagent.framework.stage_llm.run_stage_agent",return_value=output), \
                 patch("accagent.framework.dse_timing_calibration.compiled_source_context",return_value=context):
                path = ensure_source_cycle_analysis(root,context_override=context)
            result = json.loads(path.read_text())
            self.assertEqual(path.name,"compiled_source_cycle_analysis.json")
            self.assertIsNone(result["synthesis_source_archive_sha256"])
            self.assertEqual(result["latency_cycles"],36)
            self.assertFalse((path.parent/"source_cycle_analysis.json").exists())

    def test_schedule_context_failure_retries_without_editing_hardware(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from accagent.framework import stage_backend as backend

        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/"backend_board";out.mkdir()
            (out/"optimization_request.json").write_text(json.dumps({
                "scope":"existing_design_timing","calibrate_timing_cycles":True}))
            with patch("accagent.framework.dse_timing_calibration.compiled_source_context",side_effect=ValueError("missing context")), \
                 patch("accagent.framework.codegen_source_repair.repair_timing_sources",side_effect=AssertionError("no hardware edits")), \
                 patch.object(backend,"timing_repair_followup",return_value=(out,{})) as followup:
                backend.compiled_cycle_followup(root/"state.json",root,out)
            plan=followup.call_args.args[2]
            self.assertEqual(plan["timing_source_repair"]["status"],"cycle_analysis_pending")

    def test_compile_failure_does_not_enter_schedule_analysis_loop(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from accagent.framework.stage_backend import compiled_cycle_followup

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "backend_board"
            out.mkdir()
            (out / "optimization_request.json").write_text(json.dumps({
                "scope": "existing_design_timing", "calibrate_timing_cycles": True}))
            application = out / "timing_optimization/candidate/application.json"
            application.parent.mkdir(parents=True)
            application.write_text(json.dumps({"status": "compile_failed"}))
            with patch("accagent.framework.dse_timing_calibration.compiled_source_context",
                       side_effect=AssertionError("compiler feedback must be repaired first")):
                self.assertIsNone(compiled_cycle_followup(root/"state.json",root,out))

    def test_source_projection_uses_complete_chisel_for_large_flattened_hierarchy(self):
        from accagent.framework.source_cycle_analysis import _cycle_analysis_prompt_sources, MAX_EMITTED_RTL_SOURCE_BYTES

        scala = "class GeneratedAcceleratorTop { val core = Module(new Block(p)); io.out <> core.io.out }"
        sources = {
            "generated/GeneratedAcceleratorTop.scala": scala,
            "generated/GeneratedAcceleratorTop.sv": "module GeneratedAcceleratorTop;\n" + "x" * MAX_EMITTED_RTL_SOURCE_BYTES,
        }
        provided, omitted = _cycle_analysis_prompt_sources(sources)
        self.assertEqual(provided, {"generated/GeneratedAcceleratorTop.scala": scala})
        self.assertEqual(omitted[0]["reason"], "expanded_hierarchy_use_complete_chisel")

    def test_cycle_analysis_retry_retains_workload_and_complete_source(self):
        from accagent.framework.stage_llm import compact_retry_prompt

        source = "class TimedOperator { val states = 17 }\n" * 200
        prompt = compact_retry_prompt(
            "source_cycle_analysis_agent", "backend_board", "derive cycle schedule",
            {"sources": {"Operator.scala": source}, "workload": {"processed_tokens": 16},
             "synthesis_source_archive_sha256": "a" * 64},
            {"properties": {"pipeline_schedule": {"type": "object"}}}, [],
        )
        self.assertIn("TimedOperator", prompt)
        self.assertIn("processed_tokens", prompt)
        self.assertNotIn('"_more_keys"', prompt)

    def analyze(self, interval=10, tail=20):
        schedule = {
            "mode": "single_block_reuse", "operator_token_overlap": True,
            "start_to_first_input_cycles": 0, "steady_state_ii_cycles": interval,
            "last_token_start_to_completion_cycles": tail,
        }
        return {"model_layers": 3, "processed_tokens": 4, "pipeline_schedule": schedule,
                "latency_cycles": 3 * (3 * interval + tail)}

    def test_preserves_ddr_and_recomputes_exposed_prefetch(self):
        proxy = {"cycles": 999, "compute_cycles_per_layer": 25,
                 "initial_refill_cycles": 60, "cache_refill_service_cycles_per_layer": 60}
        result = calibrated_cycle_terms(proxy, self.analyze())
        self.assertEqual(result["compute_cycles_per_layer"], 50)
        self.assertEqual(result["overlapped_refill_stall_cycles_per_layer"], 10)
        self.assertEqual(result["latency_cycles"], 60 + 3 * 50 + 2 * 10)
        slower = calibrated_cycle_terms(proxy, self.analyze(interval=20))
        self.assertEqual(slower["overlapped_refill_stall_cycles_per_layer"], 0)
        self.assertEqual(slower["latency_cycles"], 60 + 3 * 80)

    def test_pipeline_fill_is_charged_once_per_layer(self):
        proxy = {"cycles": 999, "compute_cycles_per_layer": 25,
                 "initial_refill_cycles": 1, "cache_refill_service_cycles_per_layer": 1}
        before = calibrated_cycle_terms(proxy, self.analyze())
        after = calibrated_cycle_terms(proxy, self.analyze(tail=24))
        self.assertEqual(after["latency_cycles"] - before["latency_cycles"], 3 * 4)

    def test_rejects_inconsistent_schedule_and_invalid_refill(self):
        proxy = {"cycles": 999, "compute_cycles_per_layer": 25,
                 "initial_refill_cycles": 60, "cache_refill_service_cycles_per_layer": 60}
        with self.assertRaisesRegex(ValueError, "disagree"):
            calibrated_cycle_terms(proxy, {**self.analyze(), "latency_cycles": 1})
        with self.assertRaisesRegex(ValueError, "finite"):
            calibrated_cycle_terms({**proxy, "initial_refill_cycles": float("nan")}, self.analyze())
