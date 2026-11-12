"""Shared helpers for the agent orchestration layer."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


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
    stdout_artifact_path: str = ""
    stdout_truncated: bool = False

    @property
    def passed(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["passed"] = self.passed
        return data


class ToolRunner:
    """Run deterministic tools and keep one JSON log per command."""

    DEBUG_LOOP_MAX_CAPTURE_BYTES = 1024 * 1024
    DEBUG_LOOP_RSS_POLL_SEC = 0.1
    DEBUG_LOOP_TERM_GRACE_SEC = 1.0

    def __init__(self, repo_root: Path, log_dir: Path):
        self.repo_root = repo_root.resolve()
        self.log_dir = log_dir.resolve()
        self.index = 0

    @staticmethod
    def _process_group_rss_kib(process_group: int) -> int:
        total_kib = 0
        proc_root = Path("/proc")
        if not proc_root.is_dir():
            return 0
        for entry in proc_root.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                stat = (entry / "stat").read_text(encoding="ascii")
                fields = stat[stat.rfind(")") + 2 :].split()
                if len(fields) < 3 or int(fields[2]) != process_group:
                    continue
                for line in (entry / "status").read_text(encoding="ascii").splitlines():
                    if line.startswith("VmRSS:"):
                        total_kib += int(line.split()[1])
                        break
            except (OSError, ValueError, IndexError):
                continue
        return total_kib

    @staticmethod
    def _debug_loop_rss_limit_kib(env: dict[str, str] | None) -> int:
        if sys.platform != "linux":
            return 0
        value = (env or {}).get(
            "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB",
            os.environ.get("SPATIALACC_DEBUG_LOOP_MAX_RSS_MB", "8192"),
        ).strip().lower()
        if value in {"", "0", "off", "none", "unlimited"}:
            return 0
        try:
            return max(1, int(value)) * 1024
        except ValueError:
            return 8 * 1024 * 1024

    @staticmethod
    def _debug_loop_address_limit_bytes(env: dict[str, str] | None) -> int:
        if sys.platform != "linux":
            return 0
        value = (env or {}).get(
            "SPATIALACC_DEBUG_LOOP_MAX_VMSIZE_MB",
            os.environ.get("SPATIALACC_DEBUG_LOOP_MAX_VMSIZE_MB", "8192"),
        ).strip().lower()
        if value in {"", "0", "off", "none", "unlimited"}:
            return 0
        try:
            return max(1, int(value)) * 1024 * 1024
        except ValueError:
            return 8 * 1024 * 1024 * 1024

    @staticmethod
    def _available_memory_kib() -> int:
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])
        return 0

    @contextmanager
    def _debug_loop_memory_slot(self, env: dict[str, str] | None = None) -> Iterator[None]:
        if sys.platform != "linux":
            yield
            return
        import fcntl

        cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        lock_dir = cache_root / "spatialaccagent"
        lock_dir.mkdir(parents=True, exist_ok=True)
        settings = {**os.environ, **(env or {})}
        slots = max(1, min(2, int(settings.get("SPATIALACC_DEBUG_LOOP_SLOTS", "1"))))
        if slots > 1:
            rss_limit = self._debug_loop_rss_limit_kib(env)
            if not rss_limit:
                raise ValueError("parallel Stage-6 slots require a process-group RSS limit")
            reserve_kib = max(0, int(settings.get("SPATIALACC_DEBUG_LOOP_RESERVE_MB", "4096"))) * 1024
            print(
                "[tool] waiting for a bounded local Stage-6 memory slot "
                f"(slots={slots}, worker_limit_mib={rss_limit // 1024}, reserve_mib={reserve_kib // 1024})",
                file=sys.stderr, flush=True,
            )
            while True:
                for index in range(slots):
                    # Slot zero remains compatible with already running exclusive workers.
                    name = "debug_loop.lock" if index == 0 else f"debug_loop.{index}.lock"
                    lock_file = (lock_dir / name).open("a", encoding="ascii")
                    try:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        lock_file.close()
                        continue
                    if self._available_memory_kib() < rss_limit + reserve_kib:
                        lock_file.close()
                        continue
                    try:
                        print(f"[tool] acquired local Stage-6 memory slot {index}", file=sys.stderr, flush=True)
                        yield
                    finally:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                        lock_file.close()
                    return
                time.sleep(1.0)
        with (lock_dir / "debug_loop.lock").open("a", encoding="ascii") as lock_file:
            print(
                "[tool] waiting for the exclusive local Stage-6 memory slot",
                file=sys.stderr,
                flush=True,
            )
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _terminate_process_group(process_group: int) -> None:
        try:
            os.killpg(process_group, signal.SIGTERM)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + ToolRunner.DEBUG_LOOP_TERM_GRACE_SEC
        while time.monotonic() < deadline:
            try:
                os.killpg(process_group, 0)
            except ProcessLookupError:
                return
            time.sleep(0.05)
        try:
            os.killpg(process_group, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def run(
        self, name: str, command: list[str], env: dict[str, str] | None = None
    ) -> CommandResult:
        if name == "debug_loop":
            with self._debug_loop_memory_slot(env):
                return self._run(name, command, env)
        return self._run(name, command, env)

    def _run(
        self, name: str, command: list[str], env: dict[str, str] | None = None
    ) -> CommandResult:
        self.index += 1
        started = time.monotonic()
        proc_env = None
        if env is not None:
            proc_env = {**os.environ, **env}
        print(f"[tool] start {name}", file=sys.stderr, flush=True)
        print(
            f"[tool] command {' '.join(shlex.quote(arg) for arg in command)}",
            file=sys.stderr,
            flush=True,
        )
        rss_limit_kib = self._debug_loop_rss_limit_kib(env) if name == "debug_loop" else 0
        address_limit_bytes = self._debug_loop_address_limit_bytes(env) if name == "debug_loop" else 0
        execution_command = command
        if address_limit_bytes:
            prlimit = shutil.which("prlimit")
            if prlimit:
                execution_command = [prlimit, f"--as={address_limit_bytes}", "--", *command]
        proc = subprocess.Popen(
            execution_command,
            cwd=self.repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=proc_env,
            bufsize=1,
            start_new_session=bool(rss_limit_kib or address_limit_bytes),
        )
        if address_limit_bytes and execution_command is command:
            try:
                import resource

                resource.prlimit(
                    proc.pid,
                    resource.RLIMIT_AS,
                    (address_limit_bytes, address_limit_bytes),
                )
            except (AttributeError, OSError, ValueError) as exc:
                self._terminate_process_group(proc.pid)
                proc.wait()
                if proc.stdout is not None:
                    proc.stdout.close()
                raise RuntimeError(
                    "could not apply the Stage-6 address-space limit; worker was stopped"
                ) from exc
        stop_monitor = threading.Event()
        memory_guard = threading.Event()
        memory_pressure = threading.Event()
        settings = {**os.environ, **(env or {})}
        reserve_kib = (
            max(0, int(settings.get("SPATIALACC_DEBUG_LOOP_RESERVE_MB", "4096"))) * 1024
            if name == "debug_loop" and int(settings.get("SPATIALACC_DEBUG_LOOP_SLOTS", "1")) > 1
            else 0
        )
        peak_rss_kib = 0

        def monitor_debug_loop_memory() -> None:
            nonlocal peak_rss_kib
            while not stop_monitor.wait(self.DEBUG_LOOP_RSS_POLL_SEC):
                current_rss_kib = self._process_group_rss_kib(proc.pid)
                peak_rss_kib = max(peak_rss_kib, current_rss_kib)
                low_memory = reserve_kib and self._available_memory_kib() < reserve_kib
                if current_rss_kib <= rss_limit_kib and not low_memory:
                    continue
                if low_memory:
                    memory_pressure.set()
                memory_guard.set()
                try:
                    self._terminate_process_group(proc.pid)
                except ProcessLookupError:
                    break
                break

        monitor = None
        if rss_limit_kib:
            monitor = threading.Thread(target=monitor_debug_loop_memory, daemon=True)
            monitor.start()
        output = []
        output_tail: deque[str] = deque()
        output_tail_chars = 0
        stdout_artifact_path = ""
        stdout_artifact = None
        if name == "debug_loop":
            self.log_dir.mkdir(parents=True, exist_ok=True)
            stdout_path = self.log_dir / f"{self.index:02d}_{name}.stdout.log"
            stdout_artifact = stdout_path.open("w", encoding="utf-8")
            stdout_artifact_path = str(stdout_path)
        streamed_chars = 0
        announced_truncation = False
        assert proc.stdout is not None

        def retain_debug_loop_output(chunk: str) -> None:
            nonlocal output_tail_chars, streamed_chars, announced_truncation
            assert stdout_artifact is not None
            stdout_artifact.write(chunk)
            chunk_len = len(chunk)
            if chunk_len >= self.DEBUG_LOOP_MAX_CAPTURE_BYTES:
                output_tail.clear()
                output_tail.append(chunk[-self.DEBUG_LOOP_MAX_CAPTURE_BYTES :])
                output_tail_chars = self.DEBUG_LOOP_MAX_CAPTURE_BYTES
            else:
                output_tail.append(chunk)
                output_tail_chars += chunk_len
                while output_tail_chars > self.DEBUG_LOOP_MAX_CAPTURE_BYTES:
                    excess = output_tail_chars - self.DEBUG_LOOP_MAX_CAPTURE_BYTES
                    first = output_tail.popleft()
                    if excess < len(first):
                        output_tail.appendleft(first[excess:])
                        output_tail_chars -= excess
                    else:
                        output_tail_chars -= len(first)
            remaining_stream_chars = self.DEBUG_LOOP_MAX_CAPTURE_BYTES - streamed_chars
            if remaining_stream_chars > 0:
                print(chunk[:remaining_stream_chars], end="", file=sys.stderr, flush=True)
                streamed_chars += min(chunk_len, remaining_stream_chars)
            if chunk_len > remaining_stream_chars and not announced_truncation:
                print(
                    f"[tool] remaining debug_loop stdout is being streamed to {stdout_artifact_path}",
                    file=sys.stderr,
                    flush=True,
                )
                announced_truncation = True

        try:
            if stdout_artifact is None:
                for line in proc.stdout:
                    output.append(line)
                    print(line, end="", file=sys.stderr, flush=True)
            else:
                while chunk := proc.stdout.read(64 * 1024):
                    retain_debug_loop_output(chunk)
        finally:
            proc.stdout.close()
            if stdout_artifact is not None:
                stdout_artifact.close()
        returncode = proc.wait()
        stop_monitor.set()
        if monitor is not None:
            monitor.join(timeout=1)
        memory_guard_message = ""
        if memory_guard.is_set():
            returncode = 125
            reason = (
                f"system available memory fell below the Stage-6 reserve of {reserve_kib // 1024} MiB; "
                if memory_pressure.is_set()
                else "Stage-6 debug_loop exceeded its local process-group RSS limit: "
                f"limit={rss_limit_kib // 1024} MiB, observed_at_least={peak_rss_kib // 1024} MiB; "
            )
            memory_guard_message = (
                "[framework] " + reason +
                "the worker process group was terminated before system-wide OOM.\n"
            )
        stdout_truncated = bool(stdout_artifact_path and announced_truncation)
        if stdout_artifact_path:
            output = ["".join(output_tail)]
            if stdout_truncated:
                output.append(
                    "\n[framework] complete debug_loop stdout is in "
                    f"{stdout_artifact_path}\n"
                )
        if memory_guard_message:
            output.append(memory_guard_message)
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
            stdout_artifact_path=stdout_artifact_path,
            stdout_truncated=stdout_truncated,
        )
        write_json(log_path, result.to_dict())
        status = "pass" if result.passed else "fail"
        print(f"[tool] done {name}: {status} ({duration:.1f}s)", file=sys.stderr, flush=True)
        print(f"[tool] log {log_path}", file=sys.stderr, flush=True)
        return result
