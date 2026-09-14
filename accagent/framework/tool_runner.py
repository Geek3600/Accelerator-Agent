"""Real tool protocol runner for verification/backend/board evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return int(value)


def reuse_failed_results() -> bool:
    return env_flag("SPATIALACC_REUSE_FAILED_REAL_TOOL_RESULTS", False)


def classify_status(returncode: int | None) -> str:
    if returncode is None:
        return "not_run"
    return "pass" if returncode == 0 else "fail"


def tool_command(tool: dict[str, Any]) -> tuple[str, list[str] | None, Path | None, dict[str, str]]:
    execution = tool.get("execution") if isinstance(tool.get("execution"), dict) else {}
    argv = execution.get("argv") if isinstance(execution.get("argv"), list) else None
    cwd_value = execution.get("cwd")
    cwd = Path(str(cwd_value)) if cwd_value else None
    env = {str(k): str(v) for k, v in dict(execution.get("env") or {}).items() if v is not None and v != ""}
    command = str(tool.get("command") or "")
    return command, [str(item) for item in argv] if argv else None, cwd, env


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def selected_python_environment(
    executable: Path,
    env: dict[str, str],
    explicit_env_keys: set[str] | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    explicit_env_keys = explicit_env_keys or set()
    selected = dict(env)
    prefix = executable.parent.parent if executable.parent.name == "bin" else executable.parent
    prefix_bin = str(executable.parent)
    path_rows = [row for row in selected.get("PATH", "").split(os.pathsep) if row and row != prefix_bin]
    selected["PATH"] = os.pathsep.join([prefix_bin, *path_rows])
    selected["PYTHONNOUSERSITE"] = "1"
    if "PYTHONHOME" not in explicit_env_keys:
        selected.pop("PYTHONHOME", None)
    if "PYTHONPATH" not in explicit_env_keys:
        selected.pop("PYTHONPATH", None)
    if (prefix / "conda-meta").is_dir():
        selected["CONDA_PREFIX"] = str(prefix)
        selected["CONDA_DEFAULT_ENV"] = prefix.name
        selected["CONDA_SHLVL"] = "1"
    prefix_lib = prefix / "lib"
    if prefix_lib.is_dir():
        inherited = [row for row in selected.get("LD_LIBRARY_PATH", "").split(os.pathsep) if row and row != str(prefix_lib)]
        selected["LD_LIBRARY_PATH"] = os.pathsep.join([str(prefix_lib), *inherited])
    evidence = {
        "environment_root": str(prefix),
        "path_prefix": prefix_bin,
        "conda_prefix": selected.get("CONDA_PREFIX"),
        "python_no_user_site": selected.get("PYTHONNOUSERSITE"),
        "pythonhome": selected.get("PYTHONHOME"),
        "pythonpath": selected.get("PYTHONPATH"),
        "ld_library_path_prefix": str(prefix_lib) if prefix_lib.is_dir() else None,
    }
    return selected, evidence


def python_interpreter_candidates(requested: str, env: dict[str, str]) -> list[Path]:
    candidates: list[Path] = []

    def add(value: str | Path | None) -> None:
        if not value:
            return
        text = str(value)
        resolved = shutil.which(text, path=env.get("PATH")) if not Path(text).is_absolute() else text
        if not resolved:
            return
        path = Path(resolved).resolve()
        if path.is_file() and os.access(path, os.X_OK) and path not in candidates:
            candidates.append(path)

    add(env.get("SPATIALACC_PYTHON_EXECUTABLE"))
    add(requested)
    add(sys.executable)

    roots: list[Path] = []
    conda_exe = env.get("CONDA_EXE")
    if conda_exe:
        roots.append(Path(conda_exe).expanduser().resolve().parent.parent / "envs")
    conda_prefix = env.get("CONDA_PREFIX")
    if conda_prefix:
        prefix = Path(conda_prefix).expanduser().resolve()
        add(prefix / "bin" / "python")
        add(prefix / "bin" / "python3")
        roots.append(prefix.parent if prefix.parent.name == "envs" else prefix / "envs")
    roots.extend(
        [
            Path.home() / "miniconda3" / "envs",
            Path.home() / "anaconda3" / "envs",
            Path.home() / ".conda" / "envs",
        ]
    )
    max_candidates = max(1, int(env.get("SPATIALACC_PYTHON_MAX_CANDIDATES", "32")))
    for root in dict.fromkeys(path.resolve() for path in roots):
        if not root.is_dir():
            continue
        for environment in sorted(path for path in root.iterdir() if path.is_dir()):
            add(environment / "bin" / "python")
            add(environment / "bin" / "python3")
            if len(candidates) >= max_candidates:
                return candidates[:max_candidates]
    return candidates[:max_candidates]


def python_modules_available(
    executable: Path,
    modules: list[str],
    env: dict[str, str],
    timeout_sec: float = 60.0,
) -> tuple[bool, dict[str, Any]]:
    invalid = [value for value in modules if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", value) is None]
    if invalid:
        return False, {"returncode": None, "error": f"invalid Python module name(s): {invalid}"}
    code = """
import hashlib
import importlib
import json
import os
import platform
import sys

modules = {}
for name in %r:
    module = importlib.import_module(name)
    source = getattr(module, "__file__", None)
    source_sha256 = None
    if source and os.path.isfile(source):
        with open(source, "rb") as handle:
            source_sha256 = hashlib.sha256(handle.read()).hexdigest()
    modules[name] = {
        "version": str(getattr(module, "__version__", "unknown")),
        "source": os.path.realpath(source) if source else None,
        "source_sha256": source_sha256,
    }
payload = {
    "python": {
        "executable": os.path.realpath(sys.executable),
        "version": sys.version,
        "implementation": platform.python_implementation(),
        "cache_tag": getattr(sys.implementation, "cache_tag", None),
        "prefix": os.path.realpath(sys.prefix),
        "base_prefix": os.path.realpath(sys.base_prefix),
    },
    "modules": modules,
}
print("SPATIALACC_PYTHON_PROBE=" + json.dumps(payload, sort_keys=True))
""" % modules
    probe_started = time.monotonic()
    try:
        proc = subprocess.run(
            [str(executable), "-c", code],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=max(1.0, timeout_sec),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, {
            "returncode": 124 if isinstance(exc, subprocess.TimeoutExpired) else None,
            "error": str(exc),
            "duration_sec": time.monotonic() - probe_started,
        }
    identity = None
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith("SPATIALACC_PYTHON_PROBE="):
            try:
                identity = json.loads(line.split("=", 1)[1])
            except json.JSONDecodeError:
                identity = None
            break
    available = proc.returncode == 0 and isinstance(identity, dict)
    return available, {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1000:],
        "stderr_tail": proc.stderr[-2000:],
        "duration_sec": time.monotonic() - probe_started,
        "identity": identity,
    }


def resolve_python_execution(
    tool: dict[str, Any],
    argv: list[str] | None,
    env: dict[str, str],
    timeout_sec: float = 120.0,
    explicit_env_keys: set[str] | None = None,
) -> tuple[list[str] | None, dict[str, Any] | None, dict[str, str]]:
    raw_modules = tool.get("python_modules", [])
    if not isinstance(raw_modules, list):
        return argv, {
            "status": "fail",
            "required_modules": [],
            "selected_executable": None,
            "probes": [],
            "error": "python_modules must be a list of module names",
        }, env
    modules = [str(value) for value in raw_modules if str(value)]
    if not modules:
        return argv, None, env
    if not argv or re.fullmatch(r"(?:python(?:\d+(?:\.\d+)*)?|pypy(?:\d+)?)", Path(argv[0]).name) is None:
        return argv, {
            "status": "fail",
            "required_modules": modules,
            "selected_executable": None,
            "probes": [],
            "error": "tool declares Python modules but does not use a supported Python argv entry",
        }, env
    raw_versions = tool.get("python_module_versions", {})
    if raw_versions is not None and not isinstance(raw_versions, dict):
        return argv, {
            "status": "fail",
            "required_modules": modules,
            "selected_executable": None,
            "probes": [],
            "error": "python_module_versions must be an object of exact allowed versions",
        }, env
    version_contract = {
        str(name): ([str(value)] if isinstance(values, str) else [str(value) for value in values])
        for name, values in dict(raw_versions or {}).items()
        if isinstance(values, (str, list, tuple))
    }
    resolution_started = time.monotonic()
    probes: list[dict[str, Any]] = []
    compatible: list[tuple[Path, dict[str, str], dict[str, Any], dict[str, Any]]] = []
    explicit_value = env.get("SPATIALACC_PYTHON_EXECUTABLE")
    explicit_path = Path(explicit_value).expanduser().resolve() if explicit_value else None
    requested_path = Path(argv[0]).expanduser().resolve() if Path(argv[0]).is_absolute() else None
    explicit_candidate = explicit_path or requested_path
    candidates = python_interpreter_candidates(argv[0], env)
    if explicit_candidate is not None:
        candidates = [candidate for candidate in candidates if candidate == explicit_candidate]
    for candidate in candidates:
        elapsed = time.monotonic() - resolution_started
        remaining = timeout_sec - elapsed
        if remaining <= 0:
            probes.append({"executable": str(candidate), "status": "fail", "error": "Python resolution budget exhausted"})
            break
        candidate_env, environment_identity = selected_python_environment(candidate, env, explicit_env_keys)
        available, evidence = python_modules_available(candidate, modules, candidate_env, timeout_sec=min(60.0, remaining))
        identity = evidence.get("identity") if isinstance(evidence.get("identity"), dict) else {}
        observed_modules = identity.get("modules", {}) if isinstance(identity.get("modules"), dict) else {}
        version_errors = []
        for module, allowed in version_contract.items():
            observed = str((observed_modules.get(module) or {}).get("version") or "unknown")
            if allowed and observed not in allowed:
                version_errors.append(f"{module}={observed} not in {allowed}")
        if version_errors:
            available = False
            evidence["error"] = "; ".join(version_errors)
        identity_fingerprint = canonical_sha256(
            {"identity": identity, "effective_environment": environment_identity}
        ) if available else None
        row = {
            "executable": str(candidate),
            "status": "pass" if available else "fail",
            "environment": environment_identity,
            "environment_fingerprint_sha256": identity_fingerprint,
            **evidence,
        }
        probes.append(row)
        if available:
            compatible.append((candidate, candidate_env, row, environment_identity))
            if explicit_candidate is not None:
                break
    if not compatible:
        return argv, {
            "status": "fail",
            "required_modules": modules,
            "required_module_versions": version_contract,
            "selected_executable": None,
            "selection_policy": "explicit override, requested interpreter, current interpreter, then bounded installed conda environments",
            "resolution_duration_sec": time.monotonic() - resolution_started,
            "probes": probes,
            "error": "no installed Python interpreter satisfies every required module and version contract",
        }, env
    fingerprints = {str(row.get("environment_fingerprint_sha256")) for _, _, row, _ in compatible}
    if explicit_candidate is None and len(fingerprints) > 1:
        return argv, {
            "status": "fail",
            "required_modules": modules,
            "required_module_versions": version_contract,
            "selected_executable": None,
            "selection_policy": "automatic discovery rejects multiple non-equivalent compatible environments",
            "resolution_duration_sec": time.monotonic() - resolution_started,
            "probes": probes,
            "error": "multiple non-equivalent Python environments satisfy the tool; set SPATIALACC_PYTHON_EXECUTABLE explicitly",
        }, env
    candidate, candidate_env, selected_probe, environment_identity = compatible[0]
    return [str(candidate), *argv[1:]], {
        "status": "pass",
        "required_modules": modules,
        "required_module_versions": version_contract,
        "selected_executable": str(candidate),
        "selected_identity": selected_probe.get("identity"),
        "effective_environment": environment_identity,
        "environment_fingerprint_sha256": selected_probe.get("environment_fingerprint_sha256"),
        "selection_policy": "explicit override, requested interpreter, current interpreter, then bounded installed conda environments",
        "resolution_duration_sec": time.monotonic() - resolution_started,
        "probes": probes,
    }, candidate_env


def argv_flag_value(argv: list[str] | None, flag: str) -> str | None:
    if not argv or flag not in argv:
        return None
    index = argv.index(flag)
    if index + 1 >= len(argv):
        return None
    return argv[index + 1]


def resolve_tool_path(value: str, cwd: Path | None, repo_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    base = cwd or repo_root
    return base / path


def report_signature(path: Path) -> tuple[int, int, int, str] | None:
    try:
        stat = path.stat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size, digest
    except OSError:
        return None


def report_key(path: Path) -> str:
    return str(path.resolve())


def exact_file_fingerprint(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        stat = resolved.stat()
    except OSError as exc:
        return {"path": str(resolved), "status": "missing", "error": str(exc), "cache_reusable": False}
    if not resolved.is_file():
        return {
            "path": str(resolved),
            "status": "directory" if resolved.is_dir() else "not_regular_file",
            "cache_reusable": False,
        }
    try:
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    except OSError as exc:
        return {"path": str(resolved), "status": "unreadable", "error": str(exc), "cache_reusable": False}
    return {
        "path": str(resolved),
        "status": "file",
        "size": stat.st_size,
        "sha256": digest,
        "cache_reusable": True,
    }


def declared_artifact_fingerprints(
    values: list[Any],
    cwd: Path | None,
    repo_root: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in values:
        value = str(raw)
        path = resolve_tool_path(value, cwd, repo_root)
        path_like = path.exists() or "/" in value or "\\" in value or bool(Path(value).suffix)
        if not path_like:
            rows.append({"declaration": value, "status": "descriptive", "cache_reusable": True})
            continue
        row = exact_file_fingerprint(path)
        row["declaration"] = value
        rows.append(row)
    return rows


def script_fingerprints(argv: list[str] | None, cwd: Path | None, repo_root: Path) -> list[dict[str, Any]]:
    if not argv:
        return []
    candidates: list[str] = []
    executable_name = Path(argv[0]).name
    if re.fullmatch(r"(?:python(?:\d+(?:\.\d+)*)?|pypy(?:\d+)?)", executable_name) and len(argv) > 1:
        if argv[1] == "-m" and len(argv) > 2:
            return [{"module": argv[2], "status": "python_module_entry", "cache_reusable": False}]
        if not argv[1].startswith("-"):
            candidates.append(argv[1])
    else:
        candidates.append(argv[0])
    rows = []
    for value in candidates:
        row = exact_file_fingerprint(resolve_tool_path(value, cwd, repo_root))
        row["declaration"] = value
        rows.append(row)
    return rows


def relevant_environment_identity(env: dict[str, str], declared_env: dict[str, str]) -> dict[str, Any]:
    excluded = {
        "SPATIALACC_REUSE_REAL_TOOL_RESULTS",
        "SPATIALACC_REUSE_FAILED_REAL_TOOL_RESULTS",
        "SPATIALACC_TOOL_TIMEOUT_SEC",
        "SPATIALACC_PYTHON_RESOLUTION_TIMEOUT_SEC",
    }
    prefixes = ("SPATIALACC_", "HF_", "HUGGINGFACE_", "TRANSFORMERS_", "TORCH_", "CUDA_")
    names = {
        key
        for key in env
        if key not in excluded
        and (key in declared_env or key in {"PATH", "CONDA_PREFIX", "PYTHONHOME", "PYTHONPATH", "PYTHONNOUSERSITE", "LD_LIBRARY_PATH"} or key.startswith(prefixes))
    }
    values = {key: env.get(key, "") for key in sorted(names)}
    return {"keys": sorted(names), "sha256": canonical_sha256(values)}


def execution_fingerprint(
    tool: dict[str, Any],
    requested_argv: list[str] | None,
    argv: list[str] | None,
    cwd: Path | None,
    repo_root: Path,
    env: dict[str, str],
    declared_env: dict[str, str],
    python_environment: dict[str, Any] | None,
) -> dict[str, Any]:
    consumes = declared_artifact_fingerprints(
        list(tool.get("consumes") or []) if isinstance(tool.get("consumes"), list) else [],
        cwd,
        repo_root,
    )
    scripts = script_fingerprints(argv, cwd, repo_root)
    reusable = all(bool(row.get("cache_reusable")) for row in [*consumes, *scripts])
    payload = {
        "name": tool.get("name"),
        "kind": tool.get("kind"),
        "requested_argv": requested_argv,
        "argv": argv,
        "cwd": str((cwd or repo_root).resolve()),
        "python_environment_group": tool.get("python_environment_group"),
        "python_modules": tool.get("python_modules", []),
        "python_module_versions": tool.get("python_module_versions", {}),
        "python_environment_fingerprint_sha256": (
            python_environment.get("environment_fingerprint_sha256")
            if isinstance(python_environment, dict)
            else None
        ),
        "environment": relevant_environment_identity(env, declared_env),
        "scripts": scripts,
        "consumes": consumes,
    }
    return {
        "schema_version": "spatialaccagent.real_tool_execution_fingerprint.v1",
        "sha256": canonical_sha256(payload),
        "cache_reusable": reusable,
        "payload": payload,
    }


def output_fingerprints(
    tool: dict[str, Any],
    argv: list[str] | None,
    cwd: Path | None,
    repo_root: Path,
) -> dict[str, Any]:
    values = list(tool.get("produces") or []) if isinstance(tool.get("produces"), list) else []
    out_value = argv_flag_value(argv, "--out")
    if out_value and out_value not in values:
        values.append(out_value)
    rows = declared_artifact_fingerprints(values, cwd, repo_root)
    exact_rows = [row for row in rows if row.get("status") != "descriptive"]
    reusable = bool(exact_rows) and all(bool(row.get("cache_reusable")) for row in exact_rows)
    payload = {"artifacts": rows}
    return {
        "schema_version": "spatialaccagent.real_tool_output_fingerprint.v1",
        "sha256": canonical_sha256(payload),
        "cache_reusable": reusable,
        **payload,
    }


def expected_report_paths(
    tool: dict[str, Any],
    argv: list[str] | None,
    cwd: Path | None,
    repo_root: Path,
) -> list[Path]:
    paths: list[Path] = []
    out_value = argv_flag_value(argv, "--out")
    if out_value:
        paths.append(resolve_tool_path(out_value, cwd, repo_root))
    for item in tool.get("produces", []) if isinstance(tool.get("produces"), list) else []:
        path = resolve_tool_path(str(item), cwd, repo_root)
        if path.suffix.lower() == ".json":
            paths.append(path)
    unique: dict[str, Path] = {}
    for path in paths:
        unique[report_key(path)] = path
    return list(unique.values())


def capture_report_signatures(
    tool: dict[str, Any],
    argv: list[str] | None,
    cwd: Path | None,
    repo_root: Path,
) -> dict[str, tuple[int, int, int, str] | None]:
    return {report_key(path): report_signature(path) for path in expected_report_paths(tool, argv, cwd, repo_root)}


def report_is_fresh(path: Path, prior_signatures: dict[str, tuple[int, int, int, str] | None]) -> bool:
    current = report_signature(path)
    return current is not None and current != prior_signatures.get(report_key(path))


def attach_tool_report(
    result: dict[str, Any],
    argv: list[str] | None,
    cwd: Path | None,
    repo_root: Path,
    prior_signatures: dict[str, tuple[int, int, int, str] | None],
) -> None:
    out_value = argv_flag_value(argv, "--out")
    if not out_value:
        return
    report_path = resolve_tool_path(out_value, cwd, repo_root)
    result["tool_report_path"] = str(report_path)
    if not report_path.exists():
        result["tool_report_status"] = "missing"
        return
    if not report_is_fresh(report_path, prior_signatures):
        result["tool_report_status"] = "stale"
        result["tool_report_error"] = "report predates the current tool invocation"
        return
    try:
        report = read_json(report_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result["tool_report_status"] = "unreadable"
        result["tool_report_error"] = str(exc)
        return
    report_status = report.get("status")
    report_summary = report.get("summary")
    result["tool_report_status"] = report_status
    result["tool_report_summary"] = report_summary
    result["tool_report_blockers"] = report.get("blockers", []) if isinstance(report.get("blockers"), list) else []
    if report_summary:
        result["summary"] = f"{result.get('summary', '')} report_status={report_status} report_summary={report_summary}".strip()


def attach_produced_json_reports(
    result: dict[str, Any],
    tool: dict[str, Any],
    cwd: Path | None,
    repo_root: Path,
    prior_signatures: dict[str, tuple[int, int, int, str] | None],
) -> None:
    reports: list[dict[str, Any]] = []
    for item in tool.get("produces", []) if isinstance(tool.get("produces"), list) else []:
        path = resolve_tool_path(str(item), cwd, repo_root)
        if path.is_dir():
            continue
        if path.suffix.lower() != ".json" or not path.exists():
            continue
        if not report_is_fresh(path, prior_signatures):
            reports.append(
                {
                    "path": str(path),
                    "status": "stale",
                    "error": "report predates the current tool invocation",
                }
            )
            continue
        try:
            data = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            reports.append({"path": str(path), "status": "unreadable", "error": str(exc)})
            continue
        reports.append(
            {
                "path": str(path),
                "status": data.get("status"),
                "summary": data.get("summary"),
                "blockers": data.get("blockers", []) if isinstance(data.get("blockers"), list) else [],
                "schema_version": data.get("schema_version"),
            }
        )
    if not reports:
        return
    result["produced_reports"] = reports
    primary = next((item for item in reports if item.get("status") == result.get("status")), reports[0])
    result.setdefault("tool_report_path", primary.get("path"))
    result.setdefault("tool_report_status", primary.get("status"))
    if primary.get("summary"):
        result.setdefault("tool_report_summary", primary.get("summary"))
    if primary.get("blockers"):
        result["tool_report_blockers"] = primary.get("blockers", [])
    if primary.get("blockers"):
        blocker_text = "; ".join(str(item) for item in primary["blockers"][:4])
        result["summary"] = f"{result.get('summary', '')} report_status={primary.get('status')} blockers={blocker_text}".strip()
    elif primary.get("summary"):
        result["summary"] = f"{result.get('summary', '')} report_status={primary.get('status')} report_summary={primary.get('summary')}".strip()


def run_tool(tool: dict[str, Any], repo_root: Path, out_dir: Path, enabled: bool, timeout_sec: int, reuse_existing: bool) -> dict[str, Any]:
    name = str(tool["name"])
    command, argv, cwd, tool_env = tool_command(tool)
    execution = tool.get("execution") if isinstance(tool.get("execution"), dict) else {}
    try:
        effective_timeout_sec = int(execution.get("timeout_sec") or timeout_sec)
    except (TypeError, ValueError):
        effective_timeout_sec = timeout_sec
    started = time.monotonic()
    env = os.environ.copy()
    env.update(tool_env)
    requested_argv = list(argv) if argv else None
    unbounded_wall_clock = effective_timeout_sec <= 0
    python_resolution_timeout_sec = float(max(1, env_int("SPATIALACC_PYTHON_RESOLUTION_TIMEOUT_SEC", 120)))
    resolution_budget = (
        python_resolution_timeout_sec
        if unbounded_wall_clock
        else min(float(effective_timeout_sec), python_resolution_timeout_sec)
    )
    argv, python_environment, env = resolve_python_execution(
        tool,
        argv,
        env,
        timeout_sec=resolution_budget,
        explicit_env_keys=set(tool_env),
    )
    if argv and python_environment is not None and python_environment.get("status") == "pass":
        command = shlex.join(argv)
        env["SPATIALACC_PYTHON_ENVIRONMENT_FINGERPRINT"] = str(
            python_environment.get("environment_fingerprint_sha256") or ""
        )
        if tool.get("python_environment_group"):
            env["SPATIALACC_PYTHON_ENVIRONMENT_GROUP"] = str(tool.get("python_environment_group"))
    log_path = out_dir / f"{name}.json"
    prior_signatures = capture_report_signatures(tool, argv, cwd, repo_root)
    fingerprint = execution_fingerprint(
        tool,
        requested_argv,
        argv,
        cwd,
        repo_root,
        env,
        tool_env,
        python_environment,
    )
    result: dict[str, Any] = {
        "schema_version": "spatialaccagent.real_tool_result.v0",
        "name": name,
        "kind": tool.get("kind"),
        "command": command,
        "execution": {
            **dict(tool.get("execution") or {}),
            "requested_argv": requested_argv,
            "argv": argv,
        },
        "python_environment": python_environment,
        "python_environment_group": tool.get("python_environment_group"),
        "execution_fingerprint": fingerprint,
        "execution_fingerprint_sha256": fingerprint["sha256"],
        "enabled": enabled,
        "required": bool(tool.get("required", False)),
        "required_group": tool.get("required_group"),
        "script_exists": bool(tool.get("script_exists", False)),
        "timeout_sec": effective_timeout_sec,
        "wall_clock_timeout_unbounded": unbounded_wall_clock,
        "returncode": None,
        "status": "not_run",
        "stdout_tail": "",
        "stderr_tail": "",
        "duration_sec": 0.0,
        "log_path": str(log_path),
    }
    if not enabled:
        result["summary"] = "real tool execution disabled"
        write_json(log_path, result)
        return result
    if python_environment is not None and python_environment.get("status") != "pass":
        result["status"] = "fail"
        result["summary"] = str(python_environment.get("error") or "required Python environment is unavailable")
        result["duration_sec"] = time.monotonic() - started
        write_json(log_path, result)
        return result
    if reuse_existing and log_path.exists():
        try:
            previous = read_json(log_path)
            current_outputs = output_fingerprints(tool, argv, cwd, repo_root)
            reusable = bool(
                fingerprint.get("cache_reusable")
                and current_outputs.get("cache_reusable")
                and previous.get("execution_fingerprint_sha256") == fingerprint.get("sha256")
                and isinstance(previous.get("output_fingerprints"), dict)
                and previous["output_fingerprints"].get("sha256") == current_outputs.get("sha256")
                and previous["output_fingerprints"].get("cache_reusable") is True
            )
            if reusable and (previous.get("status") == "pass" or reuse_failed_results()):
                previous["enabled"] = enabled
                previous["reused_existing_result"] = True
                previous["reuse_policy"] = "exact execution/input/environment/output fingerprint match"
                previous["summary"] = f"reused existing {previous.get('status')} result from {log_path}"
                previous["log_path"] = str(log_path)
                write_json(log_path, previous)
                return previous
            result["reuse_rejected"] = True
            result["reuse_rejection"] = {
                "previous_status": previous.get("status"),
                "previous_execution_fingerprint_sha256": previous.get("execution_fingerprint_sha256"),
                "current_execution_fingerprint_sha256": fingerprint.get("sha256"),
                "previous_output_fingerprint_sha256": (
                    previous.get("output_fingerprints", {}).get("sha256")
                    if isinstance(previous.get("output_fingerprints"), dict)
                    else None
                ),
                "current_output_fingerprint_sha256": current_outputs.get("sha256"),
                "input_cache_reusable": fingerprint.get("cache_reusable"),
                "output_cache_reusable": current_outputs.get("cache_reusable"),
            }
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    if not command or command.startswith("<"):
        result["summary"] = "tool command not configured"
        write_json(log_path, result)
        return result
    if command.endswith(".c"):
        result["summary"] = "C board utility requires board-side compile/run wrapper"
        write_json(log_path, result)
        return result
    if not result["script_exists"] and not argv and not command.startswith("ssh ") and not command.startswith("timeout "):
        result["status"] = "fail"
        result["summary"] = "tool script not found"
        write_json(log_path, result)
        return result

    remaining_timeout_sec = None if unbounded_wall_clock else effective_timeout_sec - (time.monotonic() - started)
    if remaining_timeout_sec is not None and remaining_timeout_sec <= 0:
        result["returncode"] = 124
        result["status"] = "fail"
        result["summary"] = f"tool timeout budget exhausted during environment resolution ({effective_timeout_sec}s)"
        result["duration_sec"] = time.monotonic() - started
        result["output_fingerprints"] = output_fingerprints(tool, argv, cwd, repo_root)
        write_json(log_path, result)
        return result

    try:
        proc = subprocess.run(
            argv if argv else command,
            cwd=cwd or repo_root,
            shell=False if argv else True,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=remaining_timeout_sec,
            check=False,
        )
        result["returncode"] = proc.returncode
        result["status"] = classify_status(proc.returncode)
        result["stdout_tail"] = proc.stdout[-8000:]
        result["stderr_tail"] = proc.stderr[-8000:]
        result["summary"] = f"returncode={proc.returncode}"
        attach_tool_report(result, argv, cwd, repo_root, prior_signatures)
        attach_produced_json_reports(result, tool, cwd, repo_root, prior_signatures)
    except subprocess.TimeoutExpired as exc:
        result["returncode"] = 124
        result["status"] = "fail"
        result["stdout_tail"] = (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else ""
        result["stderr_tail"] = (exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else ""
        result["summary"] = f"timeout after total budget {effective_timeout_sec}s"
        attach_tool_report(result, argv, cwd, repo_root, prior_signatures)
        attach_produced_json_reports(result, tool, cwd, repo_root, prior_signatures)
    result["duration_sec"] = time.monotonic() - started
    result["output_fingerprints"] = output_fingerprints(tool, argv, cwd, repo_root)
    write_json(log_path, result)
    return result


def run_tools(tools: list[dict[str, Any]], repo_root: Path, out_dir: Path) -> list[dict[str, Any]]:
    enabled = env_flag("SPATIALACC_RUN_REAL_TOOLS", True)
    reuse_existing = env_flag("SPATIALACC_REUSE_REAL_TOOL_RESULTS", False)
    timeout_sec = env_int("SPATIALACC_TOOL_TIMEOUT_SEC", 0)
    return [run_tool(tool, repo_root, out_dir, enabled, timeout_sec, reuse_existing) for tool in tools]
