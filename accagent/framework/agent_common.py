"""Shared helpers for the agent orchestration layer."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def compact_json(data: object, limit: int = 1000) -> str:
    text = json.dumps(data, sort_keys=True)
    if len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text


@dataclass
class CommandResult:
    name: str
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_sec: float
    log_path: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["passed"] = self.passed
        return data


class ToolRunner:
    """Run deterministic tools and keep one JSON log per command."""

    def __init__(self, repo_root: Path, log_dir: Path):
        self.repo_root = repo_root.resolve()
        self.log_dir = log_dir.resolve()
        self.index = 0

    def run(self, name: str, command: list[str], env: dict[str, str] | None = None) -> CommandResult:
        self.index += 1
        started = time.monotonic()
        proc_env = None
        if env is not None:
            proc_env = {**os.environ, **env}
        print(f"[tool] start {name}", file=sys.stderr, flush=True)
        print(f"[tool] command {' '.join(shlex.quote(arg) for arg in command)}", file=sys.stderr, flush=True)
        proc = subprocess.Popen(
            command,
            cwd=self.repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=proc_env,
            bufsize=1,
        )
        output = []
        assert proc.stdout is not None
        for line in proc.stdout:
            output.append(line)
            print(line, end="", file=sys.stderr, flush=True)
        returncode = proc.wait()
        duration = time.monotonic() - started
        log_path = self.log_dir / f"{self.index:02d}_{name}.json"
        result = CommandResult(
            name=name,
            command=command,
            cwd=str(self.repo_root),
            returncode=returncode,
            stdout="".join(output),
            stderr="",
            duration_sec=duration,
            log_path=str(log_path),
        )
        write_json(log_path, result.to_dict())
        status = "pass" if result.passed else "fail"
        print(f"[tool] done {name}: {status} ({duration:.1f}s)", file=sys.stderr, flush=True)
        print(f"[tool] log {log_path}", file=sys.stderr, flush=True)
        return result
