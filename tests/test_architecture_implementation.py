import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework import architecture_implementation as implementation


class StopLoop(Exception):
    pass


class ArchitectureImplementationTests(unittest.TestCase):
    def test_python_failure_prevents_focused_tests(self):
        with patch.object(implementation, "execute", return_value={"returncode": 1}) as runner:
            checks = implementation.validate_python_sources(
                ["accagent/framework/weight_layout.py"],
                {"focused_test_modules": ["tests.test_weight_layout"]}, self.out)
        self.assertEqual(len(checks), 1)
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(runner.call_args.args[0][1:3], ["-m", "py_compile"])

    def test_focused_tests_return_actual_failure_to_repair_loop(self):
        with patch.object(implementation, "execute", side_effect=[
                {"returncode": 0}, {"returncode": 1}]) as runner:
            checks = implementation.validate_python_sources(
                ["accagent/framework/weight_layout.py"],
                {"focused_test_modules": ["tests.test_weight_layout"]}, self.out)
        self.assertEqual([check["returncode"] for check in checks], [0, 1])
        self.assertEqual(runner.call_args.args[0], [
            "python3", "-m", "unittest", "tests.test_weight_layout", "-q"])

    def test_ready_without_edits_runs_tools_instead_of_requiring_dummy_patch(self):
        output = {"status": "ready_to_apply", "file_edits": [],
                  "context_requests": [], "implementation_complete": False,
                  "pending_work": ["Validate current sources"]}

        def execute(*args, **kwargs):
            case = self.out / "iteration_0001/rtl/grouped"
            case.mkdir(parents=True, exist_ok=True)
            (case / "params.json").write_text("{}")
            (case / "simulation.log").write_text("PASS VCS compile/elaboration/link\n")
            return {"returncode": 0}

        with patch.object(implementation, "initial_sources", return_value=[]), \
                patch.object(implementation, "execute", side_effect=execute) as runner, \
                patch.object(implementation, "run_stage_agent",
                             side_effect=[{"output": output}, StopLoop()]):
            with self.assertRaises(StopLoop):
                implementation.implement(self.args)
        self.assertGreater(runner.call_count, 0)
        feedback = json.loads((self.out / "iteration_0001/validation.json").read_text())
        self.assertIn("checks", feedback)
        self.assertEqual(feedback["changed_sources"], [])

    def test_refill_width_coverage_reads_elaborated_ports(self):
        with tempfile.TemporaryDirectory() as directory:
            rtl = Path(directory)
            scalar = rtl / "scalar"
            scalar.mkdir()
            (scalar / "Linear.sv").write_text(
                "module Linear(input [31:0] io_tile_response_bits_data); endmodule")
            requested = {"io_tile_response_bits_data": [32, 512]}
            result = implementation.compiled_port_width_coverage(rtl, requested)
            self.assertEqual(result["returncode"], 1)
            self.assertEqual(result["missing_compiled_port_widths"],
                             {"io_tile_response_bits_data": [512]})
            wide = rtl / "wide"
            wide.mkdir()
            (wide / "Linear.sv").write_text(
                "module Linear(input [511:0] io_tile_response_bits_data); endmodule")
            self.assertEqual(implementation.compiled_port_width_coverage(rtl, requested)["returncode"], 0)

    def test_integer_case_cannot_borrow_legacy_port_widths(self):
        with tempfile.TemporaryDirectory() as directory:
            rtl = Path(directory)
            for case, width in [("legacy", 128), ("w4a8", 32)]:
                root = rtl / case
                root.mkdir()
                (root / "Linear.sv").write_text(
                    f"module Linear(input [{width - 1}:0] io_in_bits_data); endmodule")
            checks = implementation.compiled_case_coverage(
                rtl, {"w4a8": {"io_in_bits_data": [128]}}, ["w4a8"])
            self.assertEqual(checks[0]["returncode"], 1)
            self.assertEqual(checks[1]["returncode"], 0)

    def test_integer_case_rejects_fp_instances_and_missing_case(self):
        with tempfile.TemporaryDirectory() as directory:
            rtl = Path(directory)
            root = rtl / "w4a8"
            root.mkdir()
            (root / "Linear.sv").write_text(
                "module Linear(); fp_mul_sp_8_5 floating_mult(); endmodule")
            with patch("accagent.framework.fpga_ip_contract.discover_fp_modules",
                       return_value=["fp_mul_sp_8_5"]):
                checks = implementation.compiled_case_coverage(rtl, {}, ["w4a8"])
            self.assertEqual(checks[0]["returncode"], 1)
            self.assertEqual(implementation.compiled_case_coverage(
                rtl, {}, ["missing"])[0]["returncode"], 1)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)
        request = self.out / "request.json"
        request.write_text('{"required_regression_cases": ["grouped"]}')
        (self.out / "regression_oracle_contract.json").write_text('{"immutable_fragments": []}')
        self.args = argparse.Namespace(
            out=self.out, request=request, remote_host="test", remote_dir="/test",
            ip_context="/test/ip", simlib_setup="/test/setup", ip_models="/test/models",
            vcs_home="/test/vcs", validation_feedback=None,
            replay_candidate=None,
        )

    def test_remote_checkout_paths_bind_to_the_local_edit_scope(self):
        path = implementation.repository_edit_path(
            "/remote/checkout/accagent/framework/templates/operator_chisel/NewCache.scala"
        )
        self.assertEqual(path, implementation.ROOT / "accagent/framework/templates/operator_chisel/NewCache.scala")

    def test_unrelated_external_paths_remain_rejected(self):
        with self.assertRaises(ValueError):
            implementation.repository_edit_path("/remote/checkout/secrets.json")

    def test_shared_leaf_handoff_skips_duplicate_runner(self):
        run_dir = self.out / "run"
        request_dir = run_dir / "input"
        request_dir.mkdir(parents=True)
        request = {"out": str(self.out / "implementation")}
        (request_dir / "architecture_implementation_request.json").write_text(json.dumps(request))
        request_out = Path(request["out"])
        request_out.mkdir()
        (request_out / "implementation_status.json").write_text(
            json.dumps({"status": "shared_leaf_handoff"}))
        with patch.object(implementation.subprocess, "run") as runner:
            implementation.ensure_requested_architecture(run_dir)
        runner.assert_not_called()

    def test_handoff_rechecks_new_integer_requirements_after_reload(self):
        run_dir = self.out / "run"
        input_dir = run_dir / "input"
        input_dir.mkdir(parents=True)
        request_out = self.out / "implementation"
        attempt = request_out / "iteration_0001"
        (attempt / "llm").mkdir(parents=True)
        specification = self.out / "request.json"
        specification.write_text(json.dumps({"require_shared_implementation_complete": True,
                                             "required_integer_cases": ["w4a8"]}))
        request = {key: "/test" for key in [
            "remote-host", "remote-dir", "ip-context", "simlib-setup", "ip-models"]}
        request.update(out=str(request_out), request=str(specification))
        (input_dir / "architecture_implementation_request.json").write_text(json.dumps(request))
        status_path = request_out / "implementation_status.json"
        status = {"status": "shared_leaf_handoff", "iteration": 1,
                  "validation": str(attempt / "validation.json")}
        status_path.write_text(json.dumps(status))
        result = attempt / "llm/shared_architecture_implementation_agent_result.json"
        result.write_text(json.dumps({"output": {"implementation_complete": True, "pending_work": []}}))
        with patch.object(implementation.subprocess, "run") as runner:
            implementation.ensure_requested_architecture(run_dir)
        runner.assert_called_once()  # No W4A8 RTL: old handoff must be repaired.
        (attempt / "rtl/w4a8").mkdir(parents=True)
        status_path.write_text(json.dumps(status))
        with patch.object(implementation.subprocess, "run") as runner:
            implementation.ensure_requested_architecture(run_dir)
        runner.assert_not_called()  # Valid current evidence must not rerun tools.

    def test_no_edit_handoff_reuses_previous_case_evidence(self):
        run_dir = self.out / "run"
        input_dir = run_dir / "input"
        input_dir.mkdir(parents=True)
        request_out = self.out / "implementation"
        previous = request_out / "iteration_0001/rtl/w4a8"
        previous.mkdir(parents=True)
        attempt = request_out / "iteration_0002"
        (attempt / "llm").mkdir(parents=True)
        specification = self.out / "request.json"
        specification.write_text(json.dumps({"required_integer_cases": ["w4a8"],
                                             "require_shared_implementation_complete": True}))
        (input_dir / "architecture_implementation_request.json").write_text(json.dumps({
            "out": str(request_out), "request": str(specification)}))
        validation = attempt / "validation.json"
        validation.write_text(json.dumps({"handoff": "completed_without_new_edits"}))
        (request_out / "implementation_status.json").write_text(json.dumps({
            "status": "shared_leaf_handoff", "validation": str(validation)}))
        (attempt / "llm/shared_architecture_implementation_agent_result.json").write_text(
            json.dumps({"output": {"implementation_complete": True, "pending_work": []}}))
        with patch.object(implementation.subprocess, "run") as runner:
            implementation.ensure_requested_architecture(run_dir)
        runner.assert_not_called()

    def test_unique_indentation_difference_keeps_patch_content(self):
        before = '            "Common.scala",\n            "PhysicalResources.scala",\n'
        old = '        "Common.scala",\n        "PhysicalResources.scala",\n'
        new = old + '        "NewCache.scala",\n'
        adjusted_old, adjusted_new = implementation.align_edit_indentation(before, old, new)
        self.assertEqual(adjusted_old, before)
        self.assertEqual(adjusted_new, before + '            "NewCache.scala",\n')

    def test_complete_file_edit_accepts_exact_current_snapshot(self):
        relative = "accagent/framework/stage_artifacts.py"
        target = self.out / relative
        target.parent.mkdir(parents=True)
        target.write_text("old_source = True\n")
        with patch.object(implementation, "ROOT", self.out):
            implementation.apply_edits(
                [{"path": relative, "old_text": "", "new_text": "new_source = True\n"}],
                self.out / "backup", [], {relative: "old_source = True\n"},
            )
        self.assertEqual(target.read_text(), "new_source = True\n")
        self.assertEqual((self.out / "backup" / relative).read_text(), "old_source = True\n")

    def test_complete_file_edit_rejects_changes_since_the_request(self):
        relative = "accagent/framework/stage_artifacts.py"
        target = self.out / relative
        target.parent.mkdir(parents=True)
        target.write_text("concurrent_change = True\n")
        with patch.object(implementation, "ROOT", self.out):
            with self.assertRaises(ValueError):
                implementation.apply_edits(
                    [{"path": relative, "old_text": "", "new_text": "new_source = True\n"}],
                    self.out / "backup", [], {relative: "old_source = True\n"},
                )
        self.assertEqual(target.read_text(), "concurrent_change = True\n")

    def test_later_exact_edit_disambiguates_repeated_anchor(self):
        relative = "accagent/framework/stage_artifacts.py"
        target = self.out / relative
        target.parent.mkdir(parents=True)
        target.write_text("same\nfirst\nsame\nsecond\n")
        edits = [{"path": relative, "old_text": "same\n", "new_text": "changed\n"},
                 {"path": relative, "old_text": "same\nsecond\n", "new_text": "changed\nsecond\n"}]
        with patch.object(implementation, "ROOT", self.out):
            implementation.apply_edits(edits, self.out / "backup", [])
        self.assertEqual(target.read_text(), "changed\nfirst\nchanged\nsecond\n")

    def test_ambiguous_final_patch_does_not_choose_an_occurrence(self):
        relative = "accagent/framework/stage_artifacts.py"
        target = self.out / relative
        target.parent.mkdir(parents=True)
        before = "same\nfirst\nsame\nsecond\n"
        target.write_text(before)
        with patch.object(implementation, "ROOT", self.out):
            with self.assertRaisesRegex(ValueError, "multiple distinct exact results"):
                implementation.apply_edits(
                    [{"path": relative, "old_text": "same\n", "new_text": "changed\n"}],
                    self.out / "backup", [],
                )
        self.assertEqual(target.read_text(), before)

    def test_successful_runner_checks_cannot_promote_unchanged_architecture(self):
        output = {"file_edits": [{"path": "tests/fixtures/linear_pipeline/run_vcs.sh"}], "context_requests": [],
                  "implementation_complete": True, "pending_work": []}

        def execute(*args, **kwargs):
            case = self.out / "iteration_0001/rtl/grouped"
            case.mkdir(parents=True, exist_ok=True)
            (case / "params.json").write_text("{}")
            (case / "simulation.log").write_text("PASS VCS compile/elaboration/link\n")
            return {"returncode": 0}

        with patch.object(implementation, "initial_sources", return_value=[]), \
                patch.object(implementation, "apply_edits", return_value=["runner.sh"]), \
                patch.object(implementation, "execute", side_effect=execute), \
                patch.object(implementation, "run_stage_agent",
                             side_effect=[{"output": output}, StopLoop()]):
            with self.assertRaises(StopLoop):
                implementation.implement(self.args)
        status = json.loads((self.out / "implementation_status.json").read_text())
        feedback = json.loads((self.out / "iteration_0001/validation.json").read_text())
        self.assertEqual(status["status"], "implementing")
        self.assertEqual(feedback["status"], "fail")
        self.assertIn("architecture is incomplete", feedback["checks"][-1]["error"])

    def test_restart_restores_requested_context_from_current_sources(self):
        source = "accagent/framework/fpga_ip_vcs_plan.py"
        previous = self.out / "iteration_0001"
        previous.mkdir()
        (previous / "validation.json").write_text(json.dumps({
            "context_request_results": [{"status": "source_supplied", "requested": source}],
        }))
        (self.out / "implementation_status.json").write_text('{"iteration": 1, "status": "implementing"}')
        with patch.object(implementation, "initial_sources", return_value=[]), \
                patch.object(implementation, "run_stage_agent", side_effect=StopLoop) as worker:
            with self.assertRaises(StopLoop):
                implementation.implement(self.args)
        snapshots = worker.call_args.kwargs["inputs"]["source_snapshots"]
        self.assertEqual(snapshots[source], (implementation.ROOT / source).read_text())

    def test_prose_context_request_supplies_all_named_sources(self):
        names = ["scripts/synthesis/compute_slot_adapter_generator.py",
                 "scripts/synthesis/board_shell_wrapper_generator.py"]
        response = {"output": {"file_edits": [], "context_requests": [
            "Please supply " + " and ".join(names) + ". Both are needed."]}}
        with patch.object(implementation, "initial_sources", return_value=[]), \
                patch.object(implementation, "run_stage_agent",
                             side_effect=[response, StopLoop()]) as worker:
            with self.assertRaises(StopLoop):
                implementation.implement(self.args)
        snapshots = worker.call_args.kwargs["inputs"]["source_snapshots"]
        for name in names:
            self.assertEqual(snapshots[name], (implementation.ROOT / name).read_text())

    def test_external_tool_evidence_refreshes_during_retry_loop(self):
        evidence = self.out / "external.json"
        evidence.write_text('{"status": "environment_pending"}')
        self.args.validation_feedback = evidence
        seen = []

        def worker(**kwargs):
            seen.append(kwargs["inputs"]["external_validation_feedback"]["status"])
            if len(seen) == 2:
                raise StopLoop
            evidence.write_text('{"status": "environment_baseline_pass"}')
            return {"output": {"file_edits": [], "context_requests": []}}

        with patch.object(implementation, "initial_sources", return_value=[]), \
                patch.object(implementation, "run_stage_agent", side_effect=worker):
            with self.assertRaises(StopLoop):
                implementation.implement(self.args)
        self.assertEqual(seen, ["environment_pending", "environment_baseline_pass"])

    def test_architecture_request_refreshes_during_retry_loop(self):
        seen = []

        def worker(**kwargs):
            request = kwargs["inputs"]["user_architecture_request"]
            seen.append(request.get("user_authorization"))
            if len(seen) == 1:
                updated = json.loads(self.args.request.read_text())
                updated["user_authorization"] = "200 token/s target"
                self.args.request.write_text(json.dumps(updated))
                return {"output": {"file_edits": [], "context_requests": [],
                                   "implementation_complete": False, "pending_work": ["todo"]}}
            raise StopLoop

        with patch.object(implementation, "initial_sources", return_value=[]), \
                patch.object(implementation, "run_stage_agent", side_effect=worker):
            with self.assertRaises(StopLoop):
                implementation.implement(self.args)
        self.assertEqual(seen, [None, "200 token/s target"])

    def test_one_rejected_file_does_not_discard_other_incremental_edits(self):
        edits = [{"path": "accagent/framework/templates/operator_chisel/Linear.scala"},
                 {"path": "accagent/framework/stage_artifacts.py"}]
        with patch.object(implementation, "apply_edits", side_effect=[
            ["accagent/framework/templates/operator_chisel/Linear.scala"],
            ValueError("old_text must match exactly once"),
        ]):
            changed, rejected = implementation.apply_incremental_edits(edits, self.out, [])
        self.assertEqual(changed, ["accagent/framework/templates/operator_chisel/Linear.scala"])
        self.assertEqual(rejected[0]["path"], "accagent/framework/stage_artifacts.py")

    def test_missing_anchor_preserves_other_exact_edits_in_same_file(self):
        relative = "accagent/framework/stage_artifacts.py"
        target = self.out / relative
        target.parent.mkdir(parents=True)
        target.write_text("first = 1\nsecond = 2\n")
        edits = [
            {"path": relative, "old_text": "first = 1", "new_text": "first = 3"},
            {"path": relative, "old_text": "stale = 4", "new_text": "stale = 5"},
            {"path": relative, "old_text": "second = 2", "new_text": "second = 6"},
        ]
        with patch.object(implementation, "ROOT", self.out):
            changed, rejected = implementation.apply_incremental_edits(edits, self.out / "backup", [])
        self.assertEqual(changed, [relative])
        self.assertEqual(target.read_text(), "first = 3\nsecond = 6\n")
        self.assertEqual((self.out / "backup" / relative).read_text(), "first = 1\nsecond = 2\n")
        self.assertEqual(len(rejected), 1)
        self.assertIn("edit 2", rejected[0]["error"])

    def test_ambiguous_edit_does_not_discard_independent_exact_edit(self):
        relative = "accagent/framework/stage_artifacts.py"
        target = self.out / relative
        target.parent.mkdir(parents=True)
        target.write_text("same\nfirst\nsame\nsecond\nunique = 1\n")
        edits = [
            {"path": relative, "old_text": "same\n", "new_text": "changed\n"},
            {"path": relative, "old_text": "unique = 1", "new_text": "unique = 2"},
        ]
        with patch.object(implementation, "ROOT", self.out):
            changed, rejected = implementation.apply_incremental_edits(edits, self.out / "backup", [])
        self.assertEqual(changed, [relative])
        self.assertEqual(target.read_text(), "same\nfirst\nsame\nsecond\nunique = 2\n")
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["edit_index"], 1)

    def test_restart_recovers_last_completed_feedback_before_external_baseline(self):
        previous = self.out / "iteration_0001"
        previous.mkdir()
        evidence = {"status": "fail", "error": "current source compiler failure"}
        (previous / "validation.json").write_text(json.dumps(evidence))
        (self.out / "implementation_status.json").write_text('{"iteration": 2, "status": "implementing"}')
        external = self.out / "external.json"
        external.write_text('{"status": "historical_baseline_pass"}')
        self.args.validation_feedback = external
        with patch.object(implementation, "initial_sources", return_value=[]), \
                patch.object(implementation, "run_stage_agent", side_effect=StopLoop) as worker:
            with self.assertRaises(StopLoop):
                implementation.implement(self.args)
        self.assertEqual(worker.call_args.kwargs["inputs"]["previous_real_tool_feedback"], evidence)

    def test_rejected_edit_retains_compiler_evidence_plan_and_current_source(self):
        source = "accagent/framework/templates/operator_chisel/Linear.scala"
        previous = self.out / "iteration_0001"
        previous.mkdir()
        evidence = {"status": "fail", "checks": [{"returncode": 1, "error": "compiler failure"}]}
        (previous / "validation.json").write_text(json.dumps(evidence))
        (self.out / "implementation_status.json").write_text('{"iteration": 1, "status": "implementing"}')
        output = {"file_edits": [{"path": source}], "context_requests": [],
                  "summary": "Connect DDR", "pending_work": ["parent routing"]}
        with patch.object(implementation, "initial_sources", return_value=[implementation.ROOT / source]), \
                patch.object(implementation, "apply_incremental_edits", return_value=([], [{"path": source, "error": "anchor mismatch"}])), \
                patch.object(implementation, "run_stage_agent", side_effect=[{"output": output}, StopLoop()]) as worker:
            with self.assertRaises(StopLoop):
                implementation.implement(self.args)
        feedback = worker.call_args.kwargs["inputs"]["previous_real_tool_feedback"]
        self.assertEqual(feedback["last_real_tool_feedback"], evidence)
        self.assertEqual(feedback["implementation_plan"]["pending_work"], ["parent routing"])
        self.assertEqual(feedback["rejected_file_sources"][source], (implementation.ROOT / source).read_text())
        self.assertEqual(worker.call_args.kwargs["inputs"]["current_repair_sources"][source],
                         (implementation.ROOT / source).read_text())
