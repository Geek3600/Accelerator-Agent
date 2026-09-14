"""Small stage agents that call deterministic tools."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from accagent.framework.agent_common import CommandResult, ToolRunner, read_json
from accagent.framework.llm_client import PreStageSafetyGate
from accagent.framework.stage_team import run_design_team, team_summary


@dataclass
class StageResult:
    name: str
    passed: bool
    command_result: CommandResult
    output_path: str | None = None
    summary: dict | None = None
    safety_gate: dict | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "command": self.command_result.command,
            "command_log": self.command_result.log_path,
            "output_path": self.output_path,
            "summary": self.summary or {},
            "safety_gate": self.safety_gate or {},
        }


def blocked(rec: dict | None) -> bool:
    if not rec:
        return False
    dec = rec.get("decision", {})
    if not isinstance(dec, dict):
        return False
    decision = str(dec.get("decision") or "").strip()
    if dec.get("tool_command_allowed") is False:
        return True
    return decision in {"stop", "needs_human_approval"}


def block_result(name: str, cmd: list[str], root: Path, rec: dict | None, out: str | None = None) -> StageResult:
    return StageResult(
        name=name,
        passed=False,
        command_result=CommandResult(name, cmd, str(root), 1, "", "pre-stage safety gate stopped stage", 0.0, ""),
        output_path=out,
        summary={"status": "blocked", "errors": ["pre-stage safety gate stopped stage"]},
        safety_gate=rec,
    )


def read_report(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except Exception as exc:
        return {"status": "unreadable", "errors": [f"could not read stage report {path}: {exc}"]}


def stage_report_passed(data: dict) -> bool:
    return data.get("status") in {"ready", "pass"}


def output_status(path: Path) -> dict:
    if not path.exists():
        return {"exists": False}
    try:
        data = read_report(path)
        return {"exists": True, "status": data.get("status")}
    except Exception as exc:
        return {"exists": True, "status": "unreadable", "error": str(exc)}


def tail_text(text: str, limit: int = 4000) -> str:
    value = text.strip()
    if len(value) <= limit:
        return value
    return value[-limit:]


def failed_command_summary(res: CommandResult, path: Path | None = None) -> dict:
    summary = {
        "status": "failed",
        "errors": [f"stage command failed with returncode {res.returncode}"],
        "warnings": [],
        "command_returncode": res.returncode,
        "command_log": res.log_path,
        "failed_output_policy": "existing stage report was not promoted because the current command failed",
    }
    stdout_tail = tail_text(res.stdout)
    if stdout_tail:
        summary["stdout_tail"] = stdout_tail
    if path is not None:
        stale = output_status(path)
        summary["stale_output_ignored"] = stale.get("exists", False)
        summary["stale_output_path"] = str(path)
        summary["stale_output_status"] = stale.get("status")
        if stale.get("error"):
            summary["stale_output_error"] = stale.get("error")
    return summary


@contextmanager
def temporary_env(env: dict[str, str] | None):
    if not env:
        yield
        return
    old_values = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for key, value in old_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class InputPreparationAgent:
    def __init__(self, runner: ToolRunner, env: dict[str, str] | None = None):
        self.runner = runner
        self.env = env

    def run(
        self,
        out: Path,
        task: Path,
        model_source: Path,
        board_materials_dir: Path,
        quantization_materials_dir: Path,
        tool_materials_dir: Path,
        safety_gate: PreStageSafetyGate,
    ) -> StageResult:
        cmd = [
            sys.executable,
            "-m",
            "accagent.framework.stage_input",
            "--run-dir",
            str(out),
            "--task-spec",
            str(task),
            "--model-source",
            str(model_source),
            "--board-materials-dir",
            str(board_materials_dir),
            "--quantization-materials-dir",
            str(quantization_materials_dir),
            "--tool-materials-dir",
            str(tool_materials_dir),
        ]

        rec = safety_gate.ask("input_preparation", cmd)
        if safety_gate.cfg.enforce and blocked(rec):
            return block_result("input_preparation", cmd, self.runner.repo_root, rec)

        res = self.runner.run("input_preparation", cmd, self.env)
        path = out / "input" / "prepared_inputs.json"
        if not res.passed:
            return StageResult(
                name="input_preparation",
                passed=False,
                command_result=res,
                output_path=str(path),
                summary=failed_command_summary(res, path),
                safety_gate=rec,
            )
        data = read_report(path)
        return StageResult(
            name="input_preparation",
            passed=res.passed and data.get("status") == "ready",
            command_result=res,
            output_path=str(path),
            summary={
                "status": data.get("status"),
                "errors": data.get("errors", []),
                "warnings": data.get("warnings", []),
            },
            safety_gate=rec,
        )


class ConstraintExtractionAgent:
    def __init__(self, runner: ToolRunner, env: dict[str, str] | None = None):
        self.runner = runner
        self.env = env

    def run(self, prepared: Path, design: str, safety_gate: PreStageSafetyGate) -> StageResult:
        cmd = [
            sys.executable,
            "-m",
            "accagent.framework.stage_constraints",
            "--prepared-inputs",
            str(prepared),
            "--design-id",
            design,
        ]
        rec = safety_gate.ask("constraint_extraction", cmd, prepared=prepared)
        if safety_gate.cfg.enforce and blocked(rec):
            return block_result("constraint_extraction", cmd, self.runner.repo_root, rec)

        res = self.runner.run("constraint_extraction", cmd, self.env)
        run_dir = prepared.parents[1]
        path = run_dir / "constraint_extraction" / "constraint_extraction_report.json"
        if not res.passed:
            return StageResult(
                name="constraint_extraction",
                passed=False,
                command_result=res,
                output_path=str(path),
                summary=failed_command_summary(res, path),
                safety_gate=rec,
            )
        data = read_report(path)
        return StageResult(
            name="constraint_extraction",
            passed=res.passed and data.get("status") == "ready",
            command_result=res,
            output_path=str(path),
            summary={
                "status": data.get("status"),
                "num_nodes": data.get("num_nodes"),
                "num_constraints": data.get("num_constraints"),
                "errors": data.get("errors", []),
                "outputs": data.get("outputs", {}),
            },
            safety_gate=rec,
        )


class TemplateSelectionAgent:
    def __init__(self, runner: ToolRunner, env: dict[str, str] | None = None):
        self.runner = runner
        self.env = env

    def run(self, sacg: Path, safety_gate: PreStageSafetyGate) -> StageResult:
        cmd = [
            sys.executable,
            "-m",
            "accagent.framework.stage_templates",
            "--sacg-state",
            str(sacg),
        ]
        rec = safety_gate.ask("template_selection", cmd, sacg=sacg)
        if safety_gate.cfg.enforce and blocked(rec):
            return block_result("template_selection", cmd, self.runner.repo_root, rec)

        res = self.runner.run("template_selection", cmd, self.env)
        run_dir = sacg.parents[1]
        path = run_dir / "template_selection" / "template_selection_report.json"
        if not res.passed:
            return StageResult(
                name="template_selection",
                passed=False,
                command_result=res,
                output_path=str(path),
                summary=failed_command_summary(res, path),
                safety_gate=rec,
            )
        data = read_report(path)
        return StageResult(
            name="template_selection",
            passed=res.passed and data.get("status") == "ready",
            command_result=res,
            output_path=str(path),
            summary={
                "status": data.get("status"),
                "selected_template_ids": data.get("selected_template_ids", []),
                "missing_ops": data.get("missing_ops", []),
                "errors": data.get("errors", []),
                "outputs": data.get("outputs", {}),
            },
            safety_gate=rec,
        )


class GenericStageAgent:
    def __init__(self, runner: ToolRunner, name: str, module: str, out_dir: str, report: str, env: dict[str, str] | None = None):
        self.runner = runner
        self.name = name
        self.module = module
        self.out_dir = out_dir
        self.report = report
        self.env = env

    def run(self, sacg: Path, safety_gate: PreStageSafetyGate) -> StageResult:
        cmd = [sys.executable, "-m", self.module, "--sacg-state", str(sacg)]
        rec = safety_gate.ask(self.name, cmd, sacg=sacg)
        if safety_gate.cfg.enforce and blocked(rec):
            return block_result(self.name, cmd, self.runner.repo_root, rec)

        res = self.runner.run(self.name, cmd, self.env)
        run_dir = sacg.parents[1]
        path = run_dir / self.out_dir / self.report
        if not res.passed:
            return StageResult(
                name=self.name,
                passed=False,
                command_result=res,
                output_path=str(path),
                summary=failed_command_summary(res, path),
                safety_gate=rec,
            )
        data = read_report(path)
        return StageResult(
            name=self.name,
            passed=res.passed and stage_report_passed(data),
            command_result=res,
            output_path=str(path),
            summary=data,
            safety_gate=rec,
        )


class SACGValidationAgent:
    def __init__(self, runner: ToolRunner, env: dict[str, str] | None = None):
        self.runner = runner
        self.env = env

    def run(self, sacg: Path, safety_gate: PreStageSafetyGate) -> StageResult:
        cmd = [sys.executable, "-m", "accagent.framework.sacg_store", "validate", str(sacg)]
        rec = safety_gate.ask("sacg_validate", cmd, sacg=sacg)
        if safety_gate.cfg.enforce and blocked(rec):
            return block_result("sacg_validate", cmd, self.runner.repo_root, rec, str(sacg))

        res = self.runner.run("sacg_validate", cmd, self.env)
        run_dir = sacg.parents[1]
        with temporary_env(self.env):
            team = run_design_team(
                stage="sacg_validate",
                objective="Review final SACG validation evidence and decide whether any specialist split is needed before reporting framework readiness.",
                state=read_json(sacg),
                candidate_artifact={
                    "command": cmd,
                    "passed": res.passed,
                    "stdout": res.stdout.strip(),
                    "stderr": res.stderr.strip(),
                    "sacg_state": str(sacg),
                },
                out_dir=run_dir / "sacg_validate",
            )
        return StageResult(
            name="sacg_validate",
            passed=res.passed,
            command_result=res,
            output_path=str(sacg),
            summary={"stdout": res.stdout.strip(), "stderr": res.stderr.strip(), "design_team": team_summary(team)},
            safety_gate=rec,
        )
