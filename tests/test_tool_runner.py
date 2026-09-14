import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.tool_runner import (
    attach_produced_json_reports,
    report_key,
    report_signature,
    resolve_python_execution,
    run_tool,
)


class ToolRunnerFreshnessTest(TestCase):
    def test_python_dependency_resolver_selects_an_installed_compatible_environment(self) -> None:
        tool = {"python_modules": ["torch", "transformers"]}
        candidates = [Path("/opt/base/bin/python"), Path("/opt/model/bin/python")]
        with patch(
            "accagent.framework.tool_runner.python_interpreter_candidates",
            return_value=candidates,
        ), patch(
            "accagent.framework.tool_runner.python_modules_available",
            side_effect=[
                (False, {"returncode": 1, "stderr_tail": "missing transformers"}),
                (True, {"returncode": 0, "stderr_tail": ""}),
            ],
        ):
            argv, evidence, execution_env = resolve_python_execution(tool, ["python3", "tool.py"], {})

        self.assertEqual(argv, [str(candidates[1]), "tool.py"])
        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["selected_executable"], str(candidates[1]))
        self.assertEqual([row["status"] for row in evidence["probes"]], ["fail", "pass"])
        self.assertEqual(execution_env["PYTHONNOUSERSITE"], "1")
        self.assertEqual(execution_env["PATH"].split(":"), ["/opt/model/bin"])

    def test_python_dependency_resolver_fails_closed_without_compatible_environment(self) -> None:
        tool = {"python_modules": ["transformers"]}
        candidate = Path("/opt/base/bin/python")
        with patch(
            "accagent.framework.tool_runner.python_interpreter_candidates",
            return_value=[candidate],
        ), patch(
            "accagent.framework.tool_runner.python_modules_available",
            return_value=(False, {"returncode": 1, "stderr_tail": "missing transformers"}),
        ):
            argv, evidence, execution_env = resolve_python_execution(tool, ["python3", "tool.py"], {})

        self.assertEqual(argv, ["python3", "tool.py"])
        self.assertEqual(evidence["status"], "fail")
        self.assertIsNone(evidence["selected_executable"])
        self.assertEqual(execution_env, {})

    def test_python_dependency_resolver_rejects_ambiguous_environments(self) -> None:
        tool = {"python_modules": ["torch"]}
        candidates = [Path("/opt/a/bin/python"), Path("/opt/b/bin/python")]
        identity = {"python": {"version": "3.10"}, "modules": {"torch": {"version": "2.5"}}}
        with patch(
            "accagent.framework.tool_runner.python_interpreter_candidates",
            return_value=candidates,
        ), patch(
            "accagent.framework.tool_runner.python_modules_available",
            side_effect=[
                (True, {"returncode": 0, "identity": identity}),
                (True, {"returncode": 0, "identity": identity}),
            ],
        ):
            argv, evidence, execution_env = resolve_python_execution(tool, ["python3", "tool.py"], {})

        self.assertEqual(argv, ["python3", "tool.py"])
        self.assertEqual(evidence["status"], "fail")
        self.assertIn("multiple non-equivalent", evidence["error"])
        self.assertEqual(execution_env, {})

    def test_real_tool_reuse_requires_exact_input_script_environment_and_output_fingerprints(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script = root / "tool.py"
            source = root / "input.txt"
            report = root / "report.json"
            logs = root / "logs"
            script.write_text(
                "import argparse, json\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_argument('--input', required=True)\n"
                "p.add_argument('--out', required=True)\n"
                "a = p.parse_args()\n"
                "value = open(a.input, encoding='utf-8').read()\n"
                "json.dump({'status': 'pass', 'summary': value}, open(a.out, 'w', encoding='utf-8'))\n",
                encoding="utf-8",
            )
            source.write_text("first", encoding="utf-8")
            tool = {
                "name": "fingerprinted_tool",
                "kind": "test",
                "command": f"{Path(sys.executable).resolve()} {script}",
                "execution": {
                    "argv": [str(Path(sys.executable).resolve()), str(script), "--input", str(source), "--out", str(report)],
                    "cwd": str(root),
                    "env": {},
                },
                "script_exists": True,
                "required": True,
                "consumes": [str(source)],
                "produces": [str(report)],
            }

            first = run_tool(tool, root, logs, True, 30, False)
            reused = run_tool(tool, root, logs, True, 30, True)
            source.write_text("second", encoding="utf-8")
            refreshed = run_tool(tool, root, logs, True, 30, True)

            self.assertEqual(first["status"], "pass")
            self.assertTrue(reused["reused_existing_result"])
            self.assertTrue(refreshed["reuse_rejected"])
            self.assertFalse(refreshed.get("reused_existing_result", False))
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["summary"], "second")

    def test_zero_tool_budget_runs_without_outer_wall_clock_timeout(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            logs = root / "logs"
            tool = {
                "name": "unbounded_tool",
                "kind": "test",
                "command": f"{Path(sys.executable).resolve()} -c pass",
                "execution": {
                    "argv": [str(Path(sys.executable).resolve()), "-c", "pass"],
                    "cwd": str(root),
                    "env": {},
                },
                "script_exists": True,
                "required": True,
            }

            with patch("accagent.framework.tool_runner.subprocess.run", wraps=__import__("subprocess").run) as run:
                result = run_tool(tool, root, logs, True, 0, False)

            self.assertEqual(result["status"], "pass")
            self.assertTrue(result["wall_clock_timeout_unbounded"])
            self.assertIsNone(run.call_args.kwargs["timeout"])

    def test_stale_produced_report_cannot_contradict_current_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "report.json"
            report.write_text(
                json.dumps({"status": "pass", "summary": "old pass"}),
                encoding="utf-8",
            )
            signatures = {report_key(report): report_signature(report)}
            result = {"status": "fail", "summary": "returncode=1"}

            attach_produced_json_reports(
                result,
                {"produces": [str(report)]},
                None,
                root,
                signatures,
            )

            self.assertEqual(result["produced_reports"][0]["status"], "stale")
            self.assertEqual(result["tool_report_status"], "stale")
            self.assertNotIn("old pass", result["summary"])

    def test_current_produced_report_is_attached(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "report.json"
            signatures = {report_key(report): report_signature(report)}
            report.write_text(
                json.dumps({"status": "fail", "summary": "current failure"}),
                encoding="utf-8",
            )
            result = {"status": "fail", "summary": "returncode=1"}

            attach_produced_json_reports(
                result,
                {"produces": [str(report)]},
                None,
                root,
                signatures,
            )

            self.assertEqual(result["produced_reports"][0]["status"], "fail")
            self.assertEqual(result["tool_report_status"], "fail")
            self.assertIn("current failure", result["summary"])
