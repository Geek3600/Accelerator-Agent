import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework import codegen_source_repair as repair


class CompileSourceRepairTests(unittest.TestCase):
    def test_timing_repair_handles_null_compile_and_rejection_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            source = run_dir / "generated/chisel/src/main/scala/spatialaccagent/templates/Attention.scala"
            source.parent.mkdir(parents=True)
            source.write_text("class IntegerAttention")
            out_dir = root / "out"
            fingerprint = "a" * 64
            timing_report = root / "timing.rpt"
            timing_report.write_text(
                "Max Delay Paths\nSlack (VIOLATED) : -12.0ns\n"
                "  CARRY8 (Prop_CARRY8_CI_CO[7])\n"
                "Slack (VIOLATED) : -10.0ns\n  unrelated_path\n"
            )
            attempt_dir = out_dir / "timing_optimization" / fingerprint[:20]
            attempt_dir.mkdir(parents=True)
            repair.write_json(attempt_dir / "application.json", {
                "status": "blocked", "incremental_compile": None,
                "blockers": ["compile blocked"],
            })
            repair.write_json(attempt_dir / "agent_patch_application.json", {
                "status": "pass", "agent_transaction_rejection": None,
            })
            context = {
                "compiled_source_snapshot_sha256": fingerprint,
                "sources": {str(source.resolve()): source.read_text()},
                "workload": {},
            }
            with patch.object(repair, "run_stage_agent", return_value={"output": {
                    "status": "blocked", "file_edits": [],
                    "blocked_reasons": ["no bounded repair proposed"],
            }}) as llm:
                result = repair.repair_timing_sources(
                    run_dir, out_dir,
                    {"critical_timing_path": {"source": "maximumScoreReg_reg[1]",
                                               "destination": "probabilities_01/DSP_A_B_DATA_INST/B[0]",
                                               "report_path": str(timing_report),
                                               "report_sha256": repair.hashlib.sha256(
                                                   timing_report.read_bytes()).hexdigest()}},
                    analysis_context=context,
                )

            self.assertEqual(result["status"], "blocked")
            feedback = llm.call_args.kwargs["inputs"]["previous_repair_feedback"]
            self.assertEqual(feedback["patch_rejection_feedback"], {
                "blockers": [], "rejected_file_edits": [],
            })
            path_detail = llm.call_args.kwargs["inputs"]["critical_timing_path_detail"]
            self.assertTrue(path_detail["hash_verified"])
            self.assertIn("CARRY8 (Prop_CARRY8_CI_CO[7])", path_detail["path_excerpt"])
            self.assertIn("recent_timing_implementations", llm.call_args.kwargs["inputs"])

    def test_timing_schedule_feedback_survives_new_source_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            previous = out_dir / "timing_optimization/old_source/application.json"
            previous.parent.mkdir(parents=True)
            repair.write_json(previous, {
                "status": "compiled_pending_vcs",
                "synthesis_source_archive_sha256": "old_source_hash",
                "implementation_summary": "Added 8 cycles; beat II increased from 3 to 11.",
                "compiler_diagnostics": "large unrelated log",
            })
            current = out_dir / "timing_optimization/new_source/application.json"
            current.parent.mkdir(parents=True)
            repair.write_json(current, {"status": "blocked", "blockers": ["retry"]})

            records = repair.recent_timing_implementation_context(out_dir)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["synthesis_source_archive_sha256"], "old_source_hash")
            self.assertIn("3 to 11", records[0]["implementation_summary"])
            self.assertNotIn("compiler_diagnostics", records[0])

    def test_timing_context_exposes_ambiguous_signal_owners(self):
        source = "class FloatNorm {\n val denominatorReg = Reg(UInt(32.W))\n}\nclass IntNorm {\n val denominatorReg = Reg(UInt(64.W))\n val outputReg = Reg(UInt(8.W))\n}"
        timing = {"source": "core/denominatorReg_reg[1]/C",
                  "destination": "core/outputReg_09/DSP_A_B_DATA_INST/A[0]"}
        result = repair.timing_signal_source_context(timing, {"Norm.scala": source})
        self.assertEqual([row["enclosing_class"] for row in result],
                         ["class FloatNorm {", "class IntNorm {", "class IntNorm {"])
        self.assertEqual([row["line"] for row in result], [2, 5, 6])

    def test_timing_context_includes_full_control_window_around_endpoint(self):
        source = "\n".join(f"line_{index}" for index in range(1, 121))
        source = source.replace("line_60", "val writeToken = RegInit(0.U(8.W))")
        timing = {"source": "core/writeToken_reg[2]/C",
                  "destination": "core/outputMem/DINADIN[0]"}

        result = repair.timing_signal_source_context(timing, {"Linear.scala": source})

        excerpt = result[0]["source_excerpt"]
        self.assertIn("line_28", excerpt)
        self.assertIn("line_108", excerpt)
        self.assertNotIn("line_27", excerpt)
        self.assertNotIn("line_109", excerpt)

    def test_critical_path_context_includes_hash_bound_cell_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "timing.rpt"
            report.write_text(
                "Max Delay Paths\n"
                "Slack (VIOLATED) : -12.0ns\n"
                "  Source: source_reg/C\n"
                "  CARRY8 (Prop_CARRY8_CI_CO[7])\n"
                "  net (fo=1) path_net\n"
                "Slack (VIOLATED) : -10.0ns\n"
                "  second_path_only\n"
            )
            digest = repair.hashlib.sha256(report.read_bytes()).hexdigest()

            result = repair.critical_timing_path_detail_context({
                "report_path": str(report), "report_sha256": digest,
            })

            self.assertEqual(result["status"], "pass")
            self.assertTrue(result["hash_verified"])
            self.assertIn("CARRY8 (Prop_CARRY8_CI_CO[7])", result["path_excerpt"])
            self.assertNotIn("second_path_only", result["path_excerpt"])

    def test_critical_path_context_rejects_changed_report_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "timing.rpt"
            report.write_text("Max Delay Paths\nSlack (VIOLATED) : -12.0ns\n  path detail\n")

            result = repair.critical_timing_path_detail_context({
                "report_path": str(report), "report_sha256": "0" * 64,
            })

            self.assertEqual(result["status"], "stale")
            self.assertEqual(result["expected_sha256"], "0" * 64)

    def test_no_localized_source_does_not_request_patch(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(repair, "run_stage_agent") as llm:
            self.assertFalse(repair.repair_compile_sources({"steps": []}, Path(tmp)))
            llm.assert_not_called()

    def test_rejects_patch_outside_localized_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "accagent/framework/templates/operator_chisel/Cache.scala"
            source.parent.mkdir(parents=True)
            source.write_text("original")
            gate = {"steps": [{"stdout_tail": "[warn] src/main/scala/templates/Cache.scala 4:1: warning"}]}
            result = {"output": {"status": "ready_to_apply", "file_edits": [
                {"path": "framework/checker.py", "old_text": "a", "new_text": "b"}
            ]}}
            with patch.object(repair, "ROOT", root), patch.object(repair, "run_stage_agent", return_value=result), patch.object(repair, "apply_edits") as apply:
                with self.assertRaisesRegex(ValueError, "outside compiler-localized"):
                    repair.repair_compile_sources(gate, root / "out")
                apply.assert_not_called()

    def test_runtime_stack_trace_requests_the_named_template_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "accagent/framework/templates/operator_chisel/Norm.scala"
            template.parent.mkdir(parents=True)
            template.write_text("class VectorNormParams")
            gate = {"steps": [{"stderr_tail": "at templates.VectorNormParams.<init>(Norm.scala:21)"}]}
            result = {"output": {"status": "needs_context", "file_edits": []}}
            with patch.object(repair, "ROOT", root), patch.object(repair, "run_stage_agent", return_value=result) as llm:
                self.assertFalse(repair.repair_compile_sources(gate, root / "out"))
                self.assertIn(str(template.relative_to(root)), llm.call_args.kwargs["inputs"]["source_snapshots"])

    def test_generated_failure_exposes_producer_and_referenced_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "accagent/framework/templates/operator_chisel/Block.scala"
            template.parent.mkdir(parents=True)
            template.write_text("class TargetBlock(p: Params)")
            producer = root / "accagent/framework/stage_artifacts.py"
            producer.write_text("producer")
            cwd = root / "generated/chisel"
            generated = cwd / "src/main/scala/spatialaccagent/generated/GeneratedTop.scala"
            generated.parent.mkdir(parents=True)
            generated.write_text("val core = Module(new TargetBlock(p))")
            gate = {"cwd": str(cwd), "steps": [{"stdout_tail": f"[error] {generated}:10: bad port"}]}
            result = {"output": {"status": "needs_context", "file_edits": []}}
            with patch.object(repair, "ROOT", root), patch.object(repair, "run_stage_agent", return_value=result) as llm:
                self.assertFalse(repair.repair_compile_sources(gate, root / "out"))
                inputs = llm.call_args.kwargs["inputs"]
                self.assertEqual(set(inputs["source_snapshots"]), {str(producer.relative_to(root)), str(template.relative_to(root))})
                self.assertEqual(inputs["generated_diagnostic_sources_read_only"], {generated.name: generated.read_text()})

    def test_concurrent_source_change_requires_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "accagent/framework/templates/operator_chisel/Cache.scala"
            source.parent.mkdir(parents=True)
            source.write_text("original")
            gate = {"steps": [{"stdout_tail": "[warn] src/main/scala/templates/Cache.scala 4:1: warning"}]}

            def respond(**kwargs):
                source.write_text("newer source")
                return {"output": {"status": "ready_to_apply", "file_edits": [
                    {"path": "accagent/framework/templates/operator_chisel/Cache.scala", "old_text": "original", "new_text": "patched"}
                ]}}

            with patch.object(repair, "ROOT", root), patch.object(repair, "run_stage_agent", side_effect=respond), patch.object(repair, "apply_edits") as apply:
                self.assertTrue(repair.repair_compile_sources(gate, root / "out"))
                apply.assert_not_called()
                self.assertEqual(source.read_text(), "newer source")
