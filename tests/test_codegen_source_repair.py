import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework import codegen_source_repair as repair


class CompileSourceRepairTests(unittest.TestCase):
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
