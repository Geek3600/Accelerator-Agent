"""Run hash-bound semantic harnesses with the configured real simulator."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from math import ceil
from pathlib import Path
from typing import Any, Callable

from accagent.framework.board_progress import (
    adaptive_semantic_stall_evidence,
    read_complete_jsonl,
)


SCHEMA_VERSION = "spatialaccagent.semantic_simulator_execution.v1"
MAX_VCS_COMPILE_JOBS = 32
MEMORY_INIT_DEFINE = "ENABLE_INITIAL_MEM_"
READMEM_LITERAL_RE = re.compile(r'\$readmem[hb]\s*\(\s*"([^"]+)"')
SEMANTIC_STALL_EXIT_CODE = 86
ZERO_TIME_LIVELOCK_EXIT_CODE = 87
REMOTE_JOB_RETRY_REQUEST = "remote_job_retry_request.json"
REMOTE_ARTIFACT_RECEIPT = ".spatialacc_local_evidence_persisted.json"
DEFAULT_REMOTE_ARTIFACT_KEEP_COMPLETED = 2
HISTORICAL_SEMANTIC_EXECUTION_RECOVERY_SCHEMA = (
    "spatialaccagent.historical_semantic_execution_recovery.v1"
)
STATIC_SOURCE_CLOSURE_SCHEMA = "spatialaccagent.static_sv_source_closure.v1"
REMOTE_PROCESS_SNAPSHOT_SCHEMA = "spatialaccagent.remote_process_snapshot.v1"
REMOTE_RUNNER_PROCESS_PROVENANCE_SCHEMA = (
    "spatialaccagent.remote_runner_process_provenance.v1"
)
REMOTE_JOB_PROCESS_MARKER = "SPATIALACC_REMOTE_JOB_PROCESS"
REMOTE_JOB_PROCESS_SUMMARY_MARKER = "SPATIALACC_REMOTE_JOB_PROCESS_SUMMARY"
FORCE_FRESH_REMOTE_VCS_ENV = "SPATIALACC_FORCE_FRESH_REMOTE_VCS"


def force_fresh_remote_vcs() -> bool:
    """Return whether this invocation is an evidence-producing targeted replay.

    Normal unchanged semantic validation may safely recover content-addressed
    evidence.  A targeted CCTG localization replay is different: its purpose
    is to observe the current internal boundary execution, so an old completed
    job cannot satisfy it even when all static inputs match.
    """

    return os.environ.get(FORCE_FRESH_REMOTE_VCS_ENV, "0") == "1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def configured_vcs(run_dir: Path) -> tuple[dict[str, Any], list[str]]:
    profile_path = run_dir / "input" / "tool_profile.json"
    if not profile_path.is_file():
        return {}, [f"tool profile is missing: {profile_path}"]
    profile = read_json(profile_path)
    candidates = [
        row
        for row in profile.get("tools", [])
        if isinstance(row, dict)
        and str(row.get("name") or "").lower() == "vcs"
        and str(row.get("role") or "") == "functional_verification"
    ]
    if len(candidates) != 1:
        return {}, [f"tool profile must declare exactly one functional VCS tool, found {len(candidates)}"]
    tool = candidates[0]
    errors = []
    for field in ("executable", "scope"):
        if not tool.get(field):
            errors.append(f"configured VCS tool is missing {field}")
    if tool.get("scope") == "remote" and not tool.get("host"):
        errors.append("configured remote VCS tool is missing host")
    return tool, errors


def wall_timeout(timeout_sec: int | None) -> int | None:
    """Treat zero/negative wall budgets as unbounded real-tool execution."""

    if timeout_sec is None or timeout_sec <= 0:
        return None
    return timeout_sec


def command_result(argv: list[str], cwd: Path, timeout_sec: int | None) -> dict[str, Any]:
    started = time.monotonic()
    result: dict[str, Any] = {
        "argv": argv,
        "cwd": str(cwd),
        "returncode": None,
        "status": "fail",
        "stdout_tail": "",
        "stderr_tail": "",
    }
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=wall_timeout(timeout_sec),
            check=False,
        )
        result.update(
            {
                "returncode": completed.returncode,
                "status": "pass" if completed.returncode == 0 else "fail",
                "stdout_tail": completed.stdout[-12000:],
                "stderr_tail": completed.stderr[-12000:],
            }
        )
    except subprocess.TimeoutExpired as exc:
        result.update(
            {
                "returncode": 124,
                "stdout_tail": (exc.stdout if isinstance(exc.stdout, str) else "")[-12000:],
                "stderr_tail": (exc.stderr if isinstance(exc.stderr, str) else "")[-12000:],
            }
        )
    result["duration_sec"] = time.monotonic() - started
    return result


def checked_path(row: dict[str, Any], label: str, blockers: list[str]) -> Path | None:
    path = Path(str(row.get("path") or ""))
    if not path.is_file():
        blockers.append(f"{label} is missing: {path}")
        return None
    expected = str(row.get("sha256") or "")
    if expected and sha256_file(path) != expected:
        blockers.append(f"{label} hash mismatch: {path}")
        return None
    return path


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.") or "unknown"


def persistent_remote_artifact_root(host: str) -> str:
    configured = os.environ.get("SPATIALACC_REMOTE_ARTIFACT_ROOT", "").strip()
    if configured:
        root = configured.rstrip("/")
        if (
            not root.startswith("/")
            or any(part in {".", ".."} for part in root.split("/"))
            or any(value in root for value in ("\0", "\n", "\r"))
        ):
            raise ValueError(
                "SPATIALACC_REMOTE_ARTIFACT_ROOT must be a safe absolute path"
            )
        return root
    user = (
        host.split("@", 1)[0]
        if "@" in host
        else os.environ.get("USER", "user")
    )
    return f"/home/{safe_id(user)}/workspace/spatialaccagent_artifacts"


def persistent_remote_tool_workdir(host: str, tool_kind: str, run_id: str) -> str:
    return (
        f"{persistent_remote_artifact_root(host)}/"
        f"{safe_id(tool_kind)}/{safe_id(run_id)}"
    )


def remote_artifact_keep_completed() -> int:
    raw = os.environ.get(
        "SPATIALACC_REMOTE_ARTIFACT_KEEP_COMPLETED",
        str(DEFAULT_REMOTE_ARTIFACT_KEEP_COMPLETED),
    )
    try:
        requested = int(raw)
    except ValueError:
        requested = DEFAULT_REMOTE_ARTIFACT_KEEP_COMPLETED
    return min(32, max(0, requested))


def semantic_vcs_compile_jobs() -> int:
    raw = os.environ.get("SPATIALACC_VCS_COMPILE_JOBS", "1")
    try:
        requested = int(raw)
    except ValueError:
        requested = 1
    return min(MAX_VCS_COMPILE_JOBS, max(1, requested))


def semantic_vcs_parallel_compile_args() -> list[str]:
    jobs = semantic_vcs_compile_jobs()
    return [f"-j{jobs}"] if jobs > 1 else []


def semantic_vcs_compile_define_args(defines: list[str]) -> list[str]:
    return [f"+define+{value}" for value in sorted(set(defines))]


def source_memory_init_contract(source: Path) -> tuple[bool, set[str]]:
    guarded = False
    references: set[str] = set()
    try:
        with source.open("r", encoding="utf-8", errors="ignore") as stream:
            for line in stream:
                if f"`ifdef {MEMORY_INIT_DEFINE}" in line:
                    guarded = True
                references.update(READMEM_LITERAL_RE.findall(line))
    except OSError:
        return False, set()
    return guarded, references


def semantic_memory_init_payload(
    run_dir: Path,
    sources: list[Path],
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    defines: set[str] = set()
    dependencies: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    project_root = (run_dir / "generated" / "chisel").resolve()
    for source in sources:
        guarded, references = source_memory_init_contract(source)
        if guarded:
            defines.add(MEMORY_INIT_DEFINE)
        for reference in sorted(references):
            relative = Path(reference)
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(
                    f"semantic memory initialization path is not remotely portable: {reference} in {source}"
                )
                continue
            candidates = [project_root / relative, source.parent / relative, Path.cwd() / relative]
            dependency = next((path.resolve() for path in candidates if path.is_file()), None)
            if dependency is None:
                errors.append(
                    f"semantic memory initialization dependency is missing: {reference} declared by {source}"
                )
                continue
            identity = {
                "remote_relative_path": relative.as_posix(),
                "path": str(dependency),
                "sha256": sha256_file(dependency),
                "declared_by": str(source),
            }
            previous = dependencies.get(relative.as_posix())
            if previous and previous["sha256"] != identity["sha256"]:
                errors.append(
                    f"conflicting semantic memory initialization dependencies for {relative.as_posix()}"
                )
                continue
            dependencies[relative.as_posix()] = identity
    return sorted(defines), [dependencies[key] for key in sorted(dependencies)], errors


def semantic_input_fingerprint(
    contract: dict[str, Any],
    run_dir: Path | None = None,
) -> tuple[str, list[str]]:
    harness = contract.get("dut_harness", {}) if isinstance(contract.get("dut_harness"), dict) else {}
    source_rows = harness.get("source_files", []) if isinstance(harness.get("source_files"), list) else []
    input_rows = contract.get("input_vectors", []) if isinstance(contract.get("input_vectors"), list) else []
    blockers: list[str] = []
    paths: list[Path] = []
    testbench = checked_path(
        {"path": contract.get("testbench"), "sha256": contract.get("testbench_sha256")},
        "semantic testbench",
        blockers,
    )
    if testbench is not None:
        paths.append(testbench)
    for index, row in enumerate(source_rows):
        if isinstance(row, dict):
            path = checked_path(row, f"semantic harness source {index}", blockers)
            if path is not None:
                paths.append(path)
    for index, row in enumerate(input_rows):
        if isinstance(row, dict):
            path = checked_path(row, f"semantic input vector {index}", blockers)
            if path is not None:
                paths.append(path)
    weight_row = contract.get("real_weight_stream", {}) if isinstance(contract.get("real_weight_stream"), dict) else {}
    if weight_row:
        path = checked_path(weight_row, "semantic real-weight stream", blockers)
        if path is not None:
            paths.append(path)
    runtime_contract = (
        contract.get("runtime_constant_stream", {})
        if isinstance(contract.get("runtime_constant_stream"), dict)
        else {}
    )
    runtime_row = (
        runtime_contract.get("stream", {})
        if isinstance(runtime_contract.get("stream"), dict)
        else runtime_contract
    )
    if runtime_row:
        path = checked_path(runtime_row, "semantic runtime-constant stream", blockers)
        if path is not None:
            paths.append(path)
    if not source_rows:
        blockers.append("semantic harness has no source files")
    if len(paths) != 1 + len(source_rows) + len(input_rows) + bool(weight_row) + bool(runtime_row):
        blockers.append("not every semantic simulator payload passed path/hash validation")
    if blockers:
        return "", blockers
    payload_hashes = [sha256_file(path) for path in paths]
    if run_dir is not None:
        defines, dependencies, init_errors = semantic_memory_init_payload(
            run_dir,
            paths[1 : 1 + len(source_rows)],
        )
        blockers.extend(init_errors)
        if blockers:
            return "", blockers
        if defines or dependencies:
            payload_hashes.extend(
                [
                    "semantic_memory_initialization_contract.v1",
                    *(f"define:{value}" for value in defines),
                    *(
                        f"readmem:{row['remote_relative_path']}:{row['sha256']}"
                        for row in dependencies
                    ),
                ]
            )
    return hashlib.sha256("".join(payload_hashes).encode("ascii")).hexdigest(), []


def _sha256_rows(rows: list[dict[str, Any]]) -> str:
    """Return a stable identity for a list of already hash-bound file rows."""

    body = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _semantic_contract_identity(
    run_dir: Path,
    stage_id: str,
    contract: dict[str, Any],
    tool: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Build the current remote-payload identity without creating a work directory.

    The normal semantic runner stages these same bytes before VCS is launched.
    Recovery uses this projection so a mutable latest report cannot be mistaken for
    a current execution merely because it has the same path.
    """

    harness = (
        contract.get("dut_harness", {})
        if isinstance(contract.get("dut_harness"), dict)
        else {}
    )
    source_rows = (
        harness.get("source_files", [])
        if isinstance(harness.get("source_files"), list)
        else []
    )
    input_rows = (
        contract.get("input_vectors", [])
        if isinstance(contract.get("input_vectors"), list)
        else []
    )
    errors: list[str] = []
    testbench = checked_path(
        {
            "path": contract.get("testbench"),
            "sha256": contract.get("testbench_sha256"),
        },
        "semantic testbench",
        errors,
    )
    sources = [
        path
        for index, row in enumerate(source_rows)
        if isinstance(row, dict)
        for path in [checked_path(row, f"semantic harness source {index}", errors)]
        if path is not None
    ]
    inputs = [
        path
        for index, row in enumerate(input_rows)
        if isinstance(row, dict)
        for path in [checked_path(row, f"semantic input vector {index}", errors)]
        if path is not None
    ]
    weight_row = (
        contract.get("real_weight_stream", {})
        if isinstance(contract.get("real_weight_stream"), dict)
        else {}
    )
    runtime_contract = (
        contract.get("runtime_constant_stream", {})
        if isinstance(contract.get("runtime_constant_stream"), dict)
        else {}
    )
    runtime_row = (
        runtime_contract.get("stream", {})
        if isinstance(runtime_contract.get("stream"), dict)
        else runtime_contract
    )
    weight = checked_path(weight_row, "semantic real-weight stream", errors) if weight_row else None
    runtime = checked_path(runtime_row, "semantic runtime-constant stream", errors) if runtime_row else None
    if not source_rows:
        errors.append("semantic harness has no source files")
    if len(sources) != len(source_rows):
        errors.append("not every semantic harness source passed path/hash validation")
    if len(inputs) != len(input_rows):
        errors.append("not every semantic input vector passed path/hash validation")
    names = [path.name for path in sources]
    if len(set(names)) != len(names):
        errors.append("semantic harness source basename collision")
    if testbench is None:
        errors.append("semantic testbench is unavailable")
    if errors:
        return {}, errors

    defines, dependencies, init_errors = semantic_memory_init_payload(run_dir, sources)
    errors.extend(init_errors)
    fingerprint, fingerprint_errors = semantic_input_fingerprint(contract, run_dir)
    errors.extend(fingerprint_errors)
    if errors:
        return {}, errors
    target_arch = str(
        (
            tool.get("env", {}).get("VCS_TARGET_ARCH")
            if isinstance(tool.get("env"), dict)
            else None
        )
        or os.environ.get("SPATIALACC_VCS_TARGET_ARCH")
        or "linux64"
    )
    payload: dict[str, str] = {
        **{path.name: sha256_file(path) for path in sources},
        "semantic_tb.sv": sha256_file(testbench),
        **{f"input_{index}.memh": sha256_file(path) for index, path in enumerate(inputs)},
    }
    if weight is not None:
        payload["weight.memh"] = sha256_file(weight)
    if runtime is not None:
        payload["runtime.memh"] = sha256_file(runtime)
    for dependency in dependencies:
        name = str(dependency.get("remote_relative_path") or "")
        digest = str(dependency.get("sha256") or "")
        if not name or not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append("semantic memory initialization dependency is malformed")
            continue
        previous = payload.get(name)
        if previous and previous != digest:
            errors.append(f"semantic payload path collision: {name}")
            continue
        payload[name] = digest
    if errors:
        return {}, errors
    plusargs = [
        *(f"+INPUT_{index}_MEMH=input_{index}.memh" for index in range(len(inputs))),
        *( ["+WEIGHT_MEMH=weight.memh"] if weight is not None else [] ),
        *( ["+RUNTIME_MEMH=runtime.memh"] if runtime is not None else [] ),
        "+OUTPUT_MEMH=rtl_output.memh",
    ]
    return {
        "stage_id": stage_id,
        "top_module": f"semantic_{safe_id(stage_id).lower()}_tb",
        "semantic_input_fingerprint_sha256": fingerprint,
        "source_names": names,
        "source_hashes": {path.name: sha256_file(path) for path in sources},
        "source_paths": {path.name: str(path) for path in sources},
        "testbench": {"path": str(testbench), "sha256": sha256_file(testbench)},
        "payload": payload,
        "compile_defines": defines,
        "plusargs": plusargs,
        "tool_profile": {
            "name": tool.get("name"),
            "role": tool.get("role"),
            "scope": tool.get("scope"),
            "host": tool.get("host"),
            "port": int(tool.get("port") or 22),
            "executable": tool.get("executable"),
            "vcs_target_arch": target_arch,
            "compile_jobs": semantic_vcs_compile_jobs(),
        },
    }, []


def _strip_sv_comments_and_literals(text: str) -> str:
    """Keep structural tokens while removing comments and string contents.

    This is deliberately a conservative scanner, not a substitute for RTL
    elaboration.  It is used only to prove that an old *extra* compile-unit was
    not reachable from an otherwise byte-identical current source closure.
    Unsupported syntax makes recovery fail closed.
    """

    output: list[str] = []
    index = 0
    state = "code"
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if char == "/" and nxt == "/":
                output.extend((" ", " "))
                index += 2
                state = "line_comment"
                continue
            if char == "/" and nxt == "*":
                output.extend((" ", " "))
                index += 2
                state = "block_comment"
                continue
            if char == '"':
                output.append(" ")
                index += 1
                state = "string"
                continue
            output.append(char)
            index += 1
            continue
        if state == "line_comment":
            output.append("\n" if char == "\n" else " ")
            index += 1
            if char == "\n":
                state = "code"
            continue
        if state == "block_comment":
            if char == "*" and nxt == "/":
                output.extend((" ", " "))
                index += 2
                state = "code"
            else:
                output.append("\n" if char == "\n" else " ")
                index += 1
            continue
        # String literal: preserve newlines only. Escaped characters remain
        # opaque so identifier-looking text cannot manufacture a dependency.
        if char == "\\" and index + 1 < len(text):
            output.extend((" ", "\n" if nxt == "\n" else " "))
            index += 2
        elif char == '"':
            output.append(" ")
            index += 1
            state = "code"
        else:
            output.append("\n" if char == "\n" else " ")
            index += 1
    return "".join(output)


def _skip_sv_space(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _skip_sv_balanced(text: str, index: int, opener: str, closer: str) -> int | None:
    if index >= len(text) or text[index] != opener:
        return None
    depth = 0
    for cursor in range(index, len(text)):
        if text[cursor] == opener:
            depth += 1
        elif text[cursor] == closer:
            depth -= 1
            if depth == 0:
                return cursor + 1
    return None


def _sv_module_definitions(paths: list[Path]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    definitions: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    header = re.compile(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\b")
    endmodule = re.compile(r"\bendmodule\b")
    for path in paths:
        try:
            cleaned = _strip_sv_comments_and_literals(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"cannot read SystemVerilog source {path}: {exc}")
            continue
        for match in header.finditer(cleaned):
            end = endmodule.search(cleaned, match.end())
            if end is None:
                errors.append(f"unterminated module declaration in {path}: {match.group(1)}")
                continue
            name = match.group(1)
            if name in definitions:
                errors.append(f"duplicate SystemVerilog module definition: {name}")
                continue
            definitions[name] = {
                "path": path,
                "body": cleaned[match.end() : end.start()],
            }
    return definitions, errors


def _sv_instance_targets(body: str, candidate_modules: set[str]) -> set[str]:
    """Find static module instantiations for a closed, known module universe."""

    targets: set[str] = set()
    identifier = re.compile(r"\b([A-Za-z_][A-Za-z0-9_$]*)\b")
    for match in identifier.finditer(body):
        target = match.group(1)
        if target not in candidate_modules:
            continue
        cursor = _skip_sv_space(body, match.end())
        if cursor < len(body) and body[cursor] == "#":
            cursor = _skip_sv_space(body, cursor + 1)
            parsed = _skip_sv_balanced(body, cursor, "(", ")")
            if parsed is None:
                continue
            cursor = _skip_sv_space(body, parsed)
        instance = identifier.match(body, cursor)
        if instance is None:
            continue
        cursor = _skip_sv_space(body, instance.end())
        while cursor < len(body) and body[cursor] == "[":
            parsed = _skip_sv_balanced(body, cursor, "[", "]")
            if parsed is None:
                break
            cursor = _skip_sv_space(body, parsed)
        if cursor < len(body) and body[cursor] == "(":
            targets.add(target)
    return targets


def static_sv_source_closure(
    *,
    sources: list[Path],
    testbench: Path,
    top_module: str,
    external_module_sources: dict[str, Path] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Prove reachable SV compile units from a top plus known historical extras.

    The proof is intentionally narrower than a simulator elaboration claim. It
    only authorizes reuse when every current reachable module resolves locally
    and no historical-only module is referenced from that closure.
    """

    external_module_sources = external_module_sources or {}
    all_paths = [*sources, testbench, *external_module_sources.values()]
    unique_paths = list(dict.fromkeys(path.resolve() for path in all_paths))
    definitions, errors = _sv_module_definitions(unique_paths)
    source_set = {path.resolve() for path in sources}
    testbench_path = testbench.resolve()
    external_paths = {path.resolve() for path in external_module_sources.values()}
    external_names = {
        name
        for name, definition in definitions.items()
        if Path(definition["path"]).resolve() in external_paths
    }
    if top_module not in definitions:
        errors.append(f"static source closure cannot find top module: {top_module}")
    candidate_names = set(definitions)
    edges = {
        name: sorted(_sv_instance_targets(str(definition["body"]), candidate_names))
        for name, definition in definitions.items()
    }
    reachable: set[str] = set()
    pending = [top_module] if top_module in definitions else []
    historical_references: set[str] = set()
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        for target in edges.get(name, []):
            if target in external_names:
                historical_references.add(target)
                continue
            if target in definitions:
                pending.append(target)
    reachable_paths = {
        Path(definitions[name]["path"]).resolve()
        for name in reachable
        if name in definitions
    }
    unexpected_reachable_paths = sorted(
        str(path) for path in reachable_paths if path not in source_set and path != testbench_path
    )
    if unexpected_reachable_paths:
        errors.append(
            "static source closure reached a source outside the current harness: "
            + ", ".join(unexpected_reachable_paths)
        )
    if historical_references:
        errors.append(
            "current static source closure references historical-only module(s): "
            + ", ".join(sorted(historical_references))
        )
    rows = [
        {"path": str(path), "sha256": sha256_file(path)}
        for path in sorted(reachable_paths)
    ]
    proof = {
        "schema_version": STATIC_SOURCE_CLOSURE_SCHEMA,
        "status": "pass" if not errors else "fail",
        "top_module": top_module,
        "reachable_modules": sorted(reachable),
        "reachable_source_files": rows,
        "reachable_source_set_sha256": _sha256_rows(rows),
        "historical_only_module_definitions": sorted(external_names),
        "historical_only_modules_referenced_by_current_closure": sorted(historical_references),
        "source_graph": {
            name: edges[name]
            for name in sorted(reachable)
            if name in edges
        },
    }
    return proof, errors


def _historical_snapshot_path(row: dict[str, Any], iteration_dir: Path) -> Path | None:
    raw = str(row.get("snapshot_path") or "")
    expected = str(row.get("source_sha256") or "")
    if not raw or not re.fullmatch(r"[0-9a-f]{64}", expected):
        return None
    path = Path(raw)
    try:
        resolved = path.resolve()
        if not resolved.is_relative_to(iteration_dir.resolve()):
            return None
    except OSError:
        return None
    if not resolved.is_file() or sha256_file(resolved) != expected:
        return None
    return resolved


def _archived_semantic_execution_candidates(
    run_dir: Path,
    stage_id: str,
) -> list[dict[str, Any]]:
    """Discover only completed Stage-8 snapshots with a real semantic execution."""

    candidates: list[dict[str, Any]] = []
    # One Stage-8 iteration often snapshots both the canonical capability
    # report and a hierarchy-view copy of that same VCS execution. Rechecking
    # the source closure twice is redundant and can make recovery needlessly
    # expensive for large generated harnesses.
    seen_execution_identities: set[tuple[str, str, str, str]] = set()
    loop_dir = run_dir / "repair_execution" / "loop"
    for record_path in sorted(loop_dir.glob("iteration_*/iteration_record.json"), reverse=True):
        record = read_json(record_path) if record_path.is_file() else {}
        if record.get("schema_version") != "spatialaccagent.stage8_repair_loop_iteration.v1":
            continue
        disposition = record.get("disposition", {}) if isinstance(record.get("disposition"), dict) else {}
        if disposition.get("status") != "complete":
            continue
        repair_report = (
            record.get("repair_execution_report", {})
            if isinstance(record.get("repair_execution_report"), dict)
            else {}
        )
        stage_passed = any(
            isinstance(row, dict)
            and isinstance(row.get("result"), dict)
            and row["result"].get("stage_passed") is True
            for row in repair_report.get("step_results", [])
            if isinstance(repair_report.get("step_results"), list)
        )
        if not stage_passed:
            continue
        rows = record.get("evidence_snapshots", [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or row.get("role") != "capability_report":
                continue
            snapshot = _historical_snapshot_path(row, record_path.parent)
            if snapshot is None:
                continue
            report = read_json(snapshot)
            stats = report.get("stats", {}) if isinstance(report.get("stats"), dict) else {}
            if (
                report.get("schema_version") != "spatialaccagent.single_layer_functional_sim.v1"
                or report.get("status") != "pass"
                or report.get("real_weight_execution", {}).get("verified") is not True
                or stats.get("schema_version") != SCHEMA_VERSION
                or stats.get("status") != "pass"
                or stats.get("stage_id") != stage_id
            ):
                continue
            persistence = (
                stats.get("remote_artifact_persistence", {})
                if isinstance(stats.get("remote_artifact_persistence"), dict)
                else {}
            )
            identity = (
                str(stats.get("input_fingerprint_sha256") or ""),
                str(report.get("output_sha256") or stats.get("rtl_output_sha256") or ""),
                str(persistence.get("receipt") or ""),
                stage_id,
            )
            if identity in seen_execution_identities:
                continue
            seen_execution_identities.add(identity)
            candidates.append(
                {
                    "iteration": int(record.get("iteration") or 0),
                    "iteration_record": record_path,
                    "iteration_record_sha256": sha256_file(record_path),
                    "report_path": snapshot,
                    "report_sha256": sha256_file(snapshot),
                    "report": report,
                    "stats": stats,
                }
            )
    return candidates


def _receipt_evidence_file(
    receipt: dict[str, Any],
    suffix: str,
) -> Path | None:
    for row in receipt.get("evidence_files", []):
        if not isinstance(row, dict):
            continue
        source = str(row.get("source_relative_path") or row.get("source_path") or "")
        if not source.endswith(suffix):
            continue
        path = Path(str(row.get("path") or ""))
        expected = str(row.get("sha256") or "")
        if path.is_file() and re.fullmatch(r"[0-9a-f]{64}", expected) and sha256_file(path) == expected:
            return path
    return None


def _archived_historical_source_snapshot(
    *,
    receipt: dict[str, Any],
    receipt_path: Path,
    job_contract: dict[str, Any],
    source_name: str,
    timeout_sec: int,
) -> tuple[Path | None, str | None]:
    """Obtain a hash-checked historical source snapshot for closure comparison.

    New jobs archive these sources locally.  For legacy receipts, copy only the
    missing historical compile unit from the retained remote workdir and preserve
    it beside the receipt; the receipt itself remains immutable.
    """

    payload = {
        str(row.get("path")): str(row.get("sha256"))
        for row in job_contract.get("payload", [])
        if isinstance(row, dict) and row.get("path") and row.get("sha256")
    }
    expected = payload.get(source_name)
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected or "")):
        return None, f"historical source {source_name} has no job-contract hash"
    for row in receipt.get("source_snapshots", []):
        if not isinstance(row, dict):
            continue
        source_path = Path(str(row.get("source_path") or ""))
        snapshot = Path(str(row.get("snapshot_path") or ""))
        if source_path.name != source_name:
            continue
        if snapshot.is_file() and sha256_file(snapshot) == expected:
            return snapshot, None
    cache_dir = receipt_path.parent / "historical_source_snapshots"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{expected[:16]}_{source_name}"
    if cached.is_file() and sha256_file(cached) == expected:
        return cached, None
    if cached.exists():
        cached.unlink()
    remote_dir = str(receipt.get("remote_workdir") or "")
    profile = job_contract.get("tool_profile", {}) if isinstance(job_contract.get("tool_profile"), dict) else {}
    host = str(profile.get("host") or "")
    port = int(profile.get("port") or 22)
    if (
        not host
        or not remote_dir.startswith("/")
        or Path(source_name).name != source_name
    ):
        return None, f"historical source {source_name} has no safe retained-remote location"
    downloaded = copy_remote_file(
        host,
        port,
        f"{remote_dir.rstrip('/')}/{source_name}",
        cached,
        cache_dir,
        timeout_sec,
    )
    if downloaded.get("status") != "pass" or not cached.is_file():
        return None, f"could not recover historical source snapshot {source_name} from retained remote evidence"
    if sha256_file(cached) != expected:
        cached.unlink(missing_ok=True)
        return None, f"recovered historical source snapshot hash mismatch: {source_name}"
    return cached, None


def _historical_execution_matches_current_contract(
    *,
    run_dir: Path,
    stage_id: str,
    contract: dict[str, Any],
    tool: dict[str, Any],
    candidate: dict[str, Any],
    timeout_sec: int,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate one archived VCS pass against the present semantic workload."""

    errors: list[str] = []
    current, current_errors = _semantic_contract_identity(run_dir, stage_id, contract, tool)
    errors.extend(current_errors)
    if not current:
        # A changed or incomplete semantic contract means the archived run is
        # not reusable.  Return the validation errors instead of indexing an
        # incomplete identity and turning a normal re-run into a KeyError.
        return None, errors or ["current semantic contract identity is unavailable"]
    stats = candidate.get("stats", {}) if isinstance(candidate.get("stats"), dict) else {}
    run = stats.get("run", {}) if isinstance(stats.get("run"), dict) else {}
    if (
        stats.get("status") != "pass"
        or stats.get("compile", {}).get("status") != "pass"
        or run.get("status") != "pass"
        or run.get("returncode") != 0
        or run.get("remote_state") != "done"
        or stats.get("remote_artifact_persistence", {}).get("status") != "pass"
    ):
        errors.append("archived semantic execution is not a completed remote VCS pass")
    receipt_ref = stats.get("remote_artifact_persistence", {}) if isinstance(stats.get("remote_artifact_persistence"), dict) else {}
    receipt_path = Path(str(receipt_ref.get("receipt") or ""))
    if not receipt_path.is_file():
        errors.append("archived semantic execution has no durable local remote-artifact receipt")
        return None, errors
    receipt = read_json(receipt_path)
    if receipt.get("schema_version") != "spatialaccagent.remote_artifact_receipt.v1" or receipt.get("status") != "pass":
        errors.append("archived remote-artifact receipt is not a pass")
    job_ref = receipt.get("job_contract", {}) if isinstance(receipt.get("job_contract"), dict) else {}
    job_path = Path(str(job_ref.get("path") or ""))
    if (
        not job_path.is_file()
        or not re.fullmatch(r"[0-9a-f]{64}", str(job_ref.get("sha256") or ""))
        or sha256_file(job_path) != job_ref.get("sha256")
    ):
        errors.append("archived remote job contract is missing or has drifted")
        return None, errors
    job = read_json(job_path)
    historic_fingerprint = str(stats.get("input_fingerprint_sha256") or "")
    if (
        job.get("schema_version") != "spatialaccagent.remote_semantic_job.v1"
        or job.get("stage_id") != stage_id
        or job.get("top_module") != current.get("top_module")
        or job.get("input_fingerprint_sha256") != historic_fingerprint
        or receipt.get("input_fingerprint_sha256") != historic_fingerprint
    ):
        errors.append("archived VCS job identity does not bind the historical semantic execution")
    historic_tool = job.get("tool_profile", {}) if isinstance(job.get("tool_profile"), dict) else {}
    # `-j` only controls compiler parallelism. It does not alter the compiled
    # source payload or simulator semantics, so record it in the proof but do
    # not force a costly rerun when a resumed controller has a different local
    # performance setting.
    for field, value in current.get("tool_profile", {}).items():
        if field == "compile_jobs":
            continue
        if historic_tool.get(field) != value:
            errors.append(f"semantic simulator identity changed: {field}")
    if job.get("compile_defines") != current.get("compile_defines"):
        errors.append("semantic VCS compile defines changed")
    if job.get("plusargs") != current.get("plusargs"):
        errors.append("semantic VCS plusargs changed")
    old_payload = {
        str(row.get("path")): str(row.get("sha256"))
        for row in job.get("payload", [])
        if isinstance(row, dict) and row.get("path") and row.get("sha256")
    }
    old_source_names = [str(value) for value in job.get("source_names", []) if str(value)]
    if len(old_source_names) != len(set(old_source_names)):
        errors.append("historical VCS source list has duplicate basenames")
    current_source_names = list(current.get("source_names", []))
    common_order = [name for name in old_source_names if name in set(current_source_names)]
    if common_order != current_source_names:
        errors.append("current semantic source order is not the historical order with only removed compile units")
    for name in current_source_names:
        if old_payload.get(name) != current.get("source_hashes", {}).get(name):
            errors.append(f"current semantic source changed: {name}")
    old_non_sources = {name: digest for name, digest in old_payload.items() if name not in set(old_source_names)}
    expected_non_sources = {
        name: digest
        for name, digest in current.get("payload", {}).items()
        if name not in set(current_source_names)
    }
    if old_non_sources != expected_non_sources:
        errors.append("semantic testbench, input, weight, runtime, or readmem payload changed")
    old_extra_sources = [name for name in old_source_names if name not in set(current_source_names)]
    historical_sources: dict[str, Path] = {}
    for name in old_extra_sources:
        path, error = _archived_historical_source_snapshot(
            receipt=receipt,
            receipt_path=receipt_path,
            job_contract=job,
            source_name=name,
            timeout_sec=timeout_sec,
        )
        if error:
            errors.append(error)
        elif path is not None:
            historical_sources[name] = path
    if len(historical_sources) != len(old_extra_sources):
        errors.append("not every removed historical source has a verified snapshot")
    source_paths = [Path(current["source_paths"][name]) for name in current_source_names]
    closure, closure_errors = static_sv_source_closure(
        sources=source_paths,
        testbench=Path(str(current["testbench"]["path"])),
        top_module=str(current["top_module"]),
        external_module_sources=historical_sources,
    )
    errors.extend(closure_errors)
    output = _receipt_evidence_file(receipt, "rtl_output.memh")
    vcs_log = _receipt_evidence_file(receipt, "vcs.log")
    sim_log = _receipt_evidence_file(receipt, "sim.log")
    sim_stderr = _receipt_evidence_file(receipt, "sim.stderr.log")
    report = candidate.get("report", {}) if isinstance(candidate.get("report"), dict) else {}
    output_hash = str(report.get("output_sha256") or stats.get("rtl_output_sha256") or "")
    if output is None or sha256_file(output) != output_hash:
        errors.append("archived RTL output is missing or does not match the functional report")
    if None in {vcs_log, sim_log, sim_stderr}:
        errors.append("archived VCS logs are incomplete")
    if errors:
        return None, errors
    return {
        "current": current,
        "historic_stats": stats,
        "historic_report": report,
        "historic_report_path": str(candidate["report_path"]),
        "historic_report_sha256": candidate["report_sha256"],
        "iteration_record": str(candidate["iteration_record"]),
        "iteration_record_sha256": candidate["iteration_record_sha256"],
        "iteration": candidate["iteration"],
        "receipt": str(receipt_path),
        "receipt_sha256": sha256_file(receipt_path),
        "job_contract": str(job_path),
        "job_contract_sha256": sha256_file(job_path),
        "historic_input_fingerprint_sha256": historic_fingerprint,
        "current_semantic_input_fingerprint_sha256": current["semantic_input_fingerprint_sha256"],
        "compile_parallelism": {
            "historic_compile_jobs": historic_tool.get("compile_jobs"),
            "current_compile_jobs": current.get("tool_profile", {}).get("compile_jobs"),
            "semantic_identity_impact": "none",
        },
        "removed_historical_sources": [
            {
                "name": name,
                "path": str(historical_sources[name]),
                "sha256": sha256_file(historical_sources[name]),
            }
            for name in sorted(historical_sources)
        ],
        "source_closure": closure,
        "evidence": {
            "rtl_output": str(output),
            "vcs_log": str(vcs_log),
            "sim_log": str(sim_log),
            "sim_stderr_log": str(sim_stderr),
        },
    }, []


def recover_archived_semantic_execution(
    run_dir: Path,
    stage_id: str,
    contract: dict[str, Any],
    timeout_sec: int,
) -> dict[str, Any] | None:
    """Rehydrate a current semantic execution only from immutable Stage-8 evidence.

    A previous VCS pass is never accepted from a mutable latest report.  The
    candidate must be a completed repair-loop snapshot, its receipt and output
    must still be hash-valid, all current non-source payload bytes must match,
    and any removed source must be statically proven unreachable from the
    current top.  This keeps a benign generated-file-list cleanup from causing
    an expensive and potentially looping re-verification cycle.
    """

    tool, tool_errors = configured_vcs(run_dir)
    if tool_errors or tool.get("scope") != "remote":
        return None
    accepted: list[dict[str, Any]] = []
    for candidate in _archived_semantic_execution_candidates(run_dir, stage_id):
        checked, errors = _historical_execution_matches_current_contract(
            run_dir=run_dir,
            stage_id=stage_id,
            contract=contract,
            tool=tool,
            candidate=candidate,
            timeout_sec=timeout_sec,
        )
        if checked is not None and not errors:
            accepted.append(checked)
    if not accepted:
        return None
    outputs = {
        sha256_file(Path(item["evidence"]["rtl_output"]))
        for item in accepted
    }
    closures = {
        str(item["source_closure"].get("reachable_source_set_sha256") or "")
        for item in accepted
    }
    if len(outputs) != 1 or len(closures) != 1:
        return None
    accepted.sort(key=lambda item: int(item.get("iteration") or 0), reverse=True)
    selected = accepted[0]
    recovery_seed = {
        "schema_version": HISTORICAL_SEMANTIC_EXECUTION_RECOVERY_SCHEMA,
        "stage_id": stage_id,
        "historic_job_contract_sha256": selected["job_contract_sha256"],
        "current_semantic_input_fingerprint_sha256": selected[
            "current_semantic_input_fingerprint_sha256"
        ],
        "reachable_source_set_sha256": selected["source_closure"][
            "reachable_source_set_sha256"
        ],
        "rtl_output_sha256": next(iter(outputs)),
    }
    recovery_id = hashlib.sha256(
        json.dumps(recovery_seed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    recovery_dir = (
        run_dir
        / "verification"
        / "semantic_execution_recovery"
        / safe_id(stage_id)
        / recovery_id
    )
    recovery_dir.mkdir(parents=True, exist_ok=True)
    output_capture = Path(str(contract.get("rtl_output_capture") or ""))
    if not output_capture.name:
        return None
    output_capture.parent.mkdir(parents=True, exist_ok=True)
    restored_files = {
        "vcs_log": recovery_dir / "vcs.log",
        "sim_log": recovery_dir / "sim.log",
        "sim_stderr_log": recovery_dir / "sim.stderr.log",
        "rtl_output": output_capture,
    }
    source_files = {
        "vcs_log": Path(selected["evidence"]["vcs_log"]),
        "sim_log": Path(selected["evidence"]["sim_log"]),
        "sim_stderr_log": Path(selected["evidence"]["sim_stderr_log"]),
        "rtl_output": Path(selected["evidence"]["rtl_output"]),
    }
    for name, destination in restored_files.items():
        source = source_files[name]
        if not destination.is_file() or sha256_file(destination) != sha256_file(source):
            shutil.copy2(source, destination)
    proof_path = recovery_dir / "historical_semantic_execution_recovery.json"
    proof = {
        **recovery_seed,
        "status": "pass",
        "summary": (
            "reused a completed hash-bound remote VCS execution after proving the current "
            "semantic payload and reachable source closure are unchanged"
        ),
        "selected_historical_execution": {
            key: selected[key]
            for key in (
                "iteration",
                "iteration_record",
                "iteration_record_sha256",
                "historic_report_path",
                "historic_report_sha256",
                "receipt",
                "receipt_sha256",
                "job_contract",
                "job_contract_sha256",
                "historic_input_fingerprint_sha256",
                "current_semantic_input_fingerprint_sha256",
                "compile_parallelism",
            )
        },
        "removed_historical_sources": selected["removed_historical_sources"],
        "static_source_closure": selected["source_closure"],
        "restored_evidence": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in restored_files.items()
        },
        "policy": {
            "mutable_latest_reports_are_not_evidence": True,
            "completed_stage8_snapshot_required": True,
            "remote_receipt_and_output_hash_required": True,
            "all_current_non_source_payload_bytes_must_match": True,
            "removed_sources_must_be_proven_unreachable": True,
            "compile_parallelism_is_a_performance_setting_not_a_semantic_input": True,
            "real_tool_was_not_relaunched": True,
        },
    }
    write_json(proof_path, proof)
    stats = json.loads(json.dumps(selected["historic_stats"]))
    # A recovered report must describe the current compilable closure, not the
    # historical compiler's superseded file list.  The latter can contain
    # unreachable generated units which are intentionally absent from the
    # current harness.  Keep it as audit-only provenance while exposing only
    # the statically proven current source closure to later certificate binding.
    historic_source_files = stats.get("source_files", [])
    current_testbench = Path(str(contract.get("testbench") or "")).resolve()
    current_source_files = [
        str(Path(row["path"]).resolve())
        for row in selected["source_closure"].get("reachable_source_files", [])
        if isinstance(row, dict)
        and row.get("path")
        and Path(str(row["path"])).resolve() != current_testbench
    ]
    stats["historical_compile_source_files"] = historic_source_files
    stats["source_files"] = sorted(dict.fromkeys(current_source_files))
    stats.update(
        {
            "current_semantic_input_fingerprint_sha256": selected[
                "current_semantic_input_fingerprint_sha256"
            ],
            "historical_semantic_execution_recovery": {
                "status": "pass",
                "proof": str(proof_path),
                "proof_sha256": sha256_file(proof_path),
                "real_tool_was_not_relaunched": True,
            },
            "local_workdir": str(recovery_dir),
            "vcs_log": str(restored_files["vcs_log"]),
            "sim_log": str(restored_files["sim_log"]),
            "sim_stderr_log": str(restored_files["sim_stderr_log"]),
            "output_capture": str(output_capture),
            "rtl_output_sha256": sha256_file(output_capture),
            "remote_job_reuse": {
                "status": "pass",
                "real_tool_was_not_relaunched": True,
                "identity_source": "completed_stage8_hash_bound_historical_execution",
                "historic_input_fingerprint_sha256": selected[
                    "historic_input_fingerprint_sha256"
                ],
                "current_recovery_proof": str(proof_path),
                "current_recovery_proof_sha256": sha256_file(proof_path),
            },
        }
    )
    return stats


def reusable_semantic_execution(
    run_dir: Path,
    stage_id: str,
    contract: dict[str, Any],
    functional_report_path: Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not functional_report_path.is_file():
        return None, [f"canonical functional report is missing: {functional_report_path}"]
    report = read_json(functional_report_path)
    executions = report.get("module_results", []) if isinstance(report.get("module_results"), list) else []
    report_mode = str(report.get("mode") or "")
    report_status = str(report.get("status") or "")
    reusable_report = (
        report_mode == "functional" and report_status == "pass"
    ) or (
        report_mode == "golden" and report_status in {"pass", "fail"}
    )
    if not reusable_report or len(executions) != 1:
        errors.append("canonical semantic report does not contain one reusable real-tool execution")
        return None, errors
    canonical_run_id = str(report.get("canonical_run_id") or "")
    if not canonical_run_id:
        errors.append("canonical functional report has no run identity")
    execution = executions[0] if isinstance(executions[0], dict) else {}
    if execution.get("status") != "pass" or execution.get("stage_id") != stage_id:
        errors.append("canonical functional execution does not pass for the requested stage")
    fingerprint, fingerprint_errors = semantic_input_fingerprint(contract, run_dir)
    errors.extend(fingerprint_errors)
    if fingerprint and execution.get("input_fingerprint_sha256") != fingerprint:
        errors.append("canonical functional execution input fingerprint is stale")
    output_capture = Path(str(contract.get("rtl_output_capture") or ""))
    recorded_capture = Path(str(execution.get("output_capture") or ""))
    if not output_capture.is_file() or output_capture.resolve() != recorded_capture.resolve():
        errors.append("canonical functional output capture path is missing or changed")
    elif sha256_file(output_capture) != execution.get("rtl_output_sha256"):
        errors.append("canonical functional output capture hash is stale")
    for label in ("vcs_log", "sim_log"):
        path = Path(str(execution.get(label) or ""))
        if not path.is_file():
            errors.append(f"canonical functional {label} is missing")
    tool, tool_errors = configured_vcs(run_dir)
    errors.extend(tool_errors)
    recorded_tool = execution.get("tool_profile", {}) if isinstance(execution.get("tool_profile"), dict) else {}
    expected_tool = dict(tool)
    if tool:
        expected_tool["port"] = int(tool.get("port") or 22)
    for field in ("name", "role", "scope", "host", "port", "executable"):
        if tool and recorded_tool.get(field) != expected_tool.get(field):
            errors.append(f"canonical functional simulator identity changed: {field}")
    if errors:
        return None, errors
    reused = dict(execution)
    reused["canonical_reuse"] = {
        "status": "pass",
        "source": f"same-contract {report_mode} real-tool execution",
        "source_report_status": report_status,
        "canonical_run_id": canonical_run_id,
        "functional_report": str(functional_report_path),
        "functional_report_sha256": sha256_file(functional_report_path),
        "input_fingerprint_sha256": fingerprint,
        "rtl_output_sha256": execution.get("rtl_output_sha256"),
        "real_tool_was_not_relaunched": True,
    }
    return reused, []


def ssh_options(port: int) -> list[str]:
    return [
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=20",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ServerAliveCountMax=240",
        "-o",
        "TCPKeepAlive=yes",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/tmp/spatialaccagent_semantic_known_hosts",
        "-p",
        str(port),
    ]


def scp_options(port: int) -> list[str]:
    return [
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=20",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ServerAliveCountMax=240",
        "-o",
        "TCPKeepAlive=yes",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/tmp/spatialaccagent_semantic_known_hosts",
        "-P",
        str(port),
    ]


def remote_shell(host: str, port: int, command: str) -> list[str]:
    return ["ssh", *ssh_options(port), host, f"bash -lc {shlex.quote(command)}"]


def remote_stage_cleanup_command(remote_stage_root: str) -> str:
    root = shlex.quote(remote_stage_root.rstrip("/"))
    return " ".join(
        [
            "set -u;",
            f"stage_root={root};",
            "pids='';",
            "for proc in /proc/[0-9]*; do",
            "pid=${proc#/proc/};",
            "[ \"$pid\" = \"$$\" ] && continue;",
            "cwd=$(readlink \"$proc/cwd\" 2>/dev/null || true);",
            "case \"$cwd\" in \"$stage_root\"/*)",
            "comm=$(cat \"$proc/comm\" 2>/dev/null || true);",
            "case \"$comm\" in bash|sh|time|vcs|vcs1|vlogan|simv) pids=\"$pids $pid\";; esac;;",
            "esac;",
            "done;",
            "if [ -n \"$pids\" ]; then",
            "kill -TERM $pids 2>/dev/null || true;",
            "sleep 2;",
            "kill -KILL $pids 2>/dev/null || true;",
            "fi;",
            "printf 'SPATIALACC_REMOTE_STAGE_CLEANUP pids=%s\\n' \"${pids# }\";",
        ]
    )


def remote_stage_prune_command(
    remote_stage_root: str,
    keep_remote_dir: str,
    keep_completed: int | None = None,
) -> str:
    root = shlex.quote(remote_stage_root.rstrip("/"))
    keep = shlex.quote(keep_remote_dir.rstrip("/"))
    keep_count = (
        remote_artifact_keep_completed()
        if keep_completed is None
        else min(32, max(0, int(keep_completed)))
    )
    receipt = shlex.quote(REMOTE_ARTIFACT_RECEIPT)
    return " ".join(
        [
            "set -euo pipefail;",
            f"stage_root={root}; keep={keep}; keep_completed={keep_count}; receipt={receipt};",
            "case \"$keep\" in \"$stage_root\"/*) ;; *) exit 2;; esac;",
            "deleted=0; active_count=0; retained_count=0; unacknowledged_count=0; candidates=''; active_cwds='';",
            # Scan /proc once.  The previous implementation repeated the
            # full process scan for every archived directory, which made
            # housekeeping exceed the SSH budget on large remote runs.
            "for proc in /proc/[0-9]*; do cwd=$(readlink \"$proc/cwd\" 2>/dev/null || true); [ -n \"$cwd\" ] && active_cwds=\"${active_cwds}${cwd}\"$'\\n'; done;",
            "if [ -d \"$stage_root\" ]; then",
            "for path in \"$stage_root\"/*; do",
            "[ -d \"$path\" ] || continue;",
            "[ \"$path\" = \"$keep\" ] && continue;",
            "base=${path##*/}; prefix=${base%%_*}; suffix=${base#*_};",
            "[ \"$base\" != \"$suffix\" ] || continue;",
            "[ ${#prefix} -eq 12 ] || continue;",
            "case \"$prefix\" in *[!0-9a-f]*|'') continue;; esac;",
            "case \"$suffix\" in *[!0-9]*|'') continue;; esac;",
            "active=0;",
            "while IFS= read -r cwd; do",
            "[ -n \"$cwd\" ] || continue;",
            "case \"$cwd\" in \"$path\"|\"$path\"/*) active=1; break;; esac;",
            "done <<< \"$active_cwds\";",
            "if [ \"$active\" -eq 1 ]; then",
            "active_count=$((active_count + 1));",
            "elif [ ! -s \"$path/$receipt\" ] || ! grep -Fq '\"status\": \"pass\"' \"$path/$receipt\"; then",
            "unacknowledged_count=$((unacknowledged_count + 1));",
            "else",
            "mtime=$(stat -c %Y \"$path\" 2>/dev/null || printf '0');",
            "candidates=\"${candidates}${mtime}\"$'\\t'\"${path}\"$'\\n';",
            "fi;",
            "done;",
            "if [ -n \"$candidates\" ]; then",
            "while IFS=$'\\t' read -r _ path; do",
            "[ -n \"$path\" ] || continue;",
            "if [ \"$retained_count\" -lt \"$keep_completed\" ]; then",
            "retained_count=$((retained_count + 1));",
            "else rm -rf -- \"$path\"; deleted=$((deleted + 1)); fi;",
            "done < <(printf '%s' \"$candidates\" | sort -rn);",
            "fi;",
            "fi;",
            "printf 'SPATIALACC_REMOTE_STAGE_PRUNE deleted=%s active=%s retained=%s unacknowledged=%s\\n' \"$deleted\" \"$active_count\" \"$retained_count\" \"$unacknowledged_count\";",
        ]
    )


def remote_completed_job_cleanup_command(
    remote_stage_root: str,
    remote_dir: str,
) -> str:
    root = shlex.quote(remote_stage_root.rstrip("/"))
    target = shlex.quote(remote_dir.rstrip("/"))
    return " ".join(
        [
            "set -eu;",
            f"stage_root={root}; target={target};",
            "case \"$target\" in \"$stage_root\"/*) ;; *) exit 2;; esac;",
            "if [ ! -d \"$target\" ]; then",
            "printf 'SPATIALACC_REMOTE_RETRY_CLEANUP state=missing\\n'; exit 0;",
            "fi;",
            "active=0;",
            "for proc in /proc/[0-9]*; do",
            "cwd=$(readlink \"$proc/cwd\" 2>/dev/null || true);",
            "case \"$cwd\" in \"$target\"|\"$target\"/*) active=1; break;; esac;",
            "done;",
            "if [ \"$active\" -eq 1 ]; then",
            "printf 'SPATIALACC_REMOTE_RETRY_CLEANUP state=active\\n';",
            "else",
            "rm -rf -- \"$target\";",
            "printf 'SPATIALACC_REMOTE_RETRY_CLEANUP state=removed\\n';",
            "fi;",
        ]
    )


def cleanup_retryable_remote_job(
    host: str,
    port: int,
    remote_stage_root: str,
    remote_dir: str,
    cwd: Path,
    timeout_sec: int,
) -> dict[str, Any]:
    result = command_result(
        remote_shell(
            host,
            port,
            remote_completed_job_cleanup_command(remote_stage_root, remote_dir),
        ),
        cwd,
        timeout_sec,
    )
    match = re.search(
        r"SPATIALACC_REMOTE_RETRY_CLEANUP state=(\w+)",
        str(result.get("stdout_tail") or ""),
    )
    state = match.group(1) if match else "indeterminate"
    return {
        **result,
        "cleanup_state": state,
        "remote_workdir": remote_dir,
    }


def copy_remote_file(
    host: str,
    port: int,
    remote_path: str,
    local_path: Path,
    cwd: Path,
    timeout_sec: int,
) -> dict[str, Any]:
    return command_result(
        ["scp", *scp_options(port), f"{host}:{remote_path}", str(local_path)],
        cwd,
        timeout_sec,
    )


def persist_remote_artifact_receipt(
    *,
    host: str,
    port: int,
    run_dir: Path,
    namespace: str,
    remote_stage_root: str,
    remote_dir: str,
    fingerprint: str,
    job_contract_path: Path,
    evidence_paths: list[Path],
    required_evidence_paths: list[Path],
    source_identity_paths: list[Path],
    snapshot_source_paths: list[Path] | None = None,
    timeout_sec: int,
) -> dict[str, Any]:
    receipt_dir = (
        run_dir
        / "verification"
        / "remote_artifacts"
        / safe_id(namespace)
        / fingerprint
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)
    contract_archive = receipt_dir / "job_contract.json"
    blockers: list[str] = []
    contract_identity: dict[str, Any] = {"status": "not_run"}
    if (
        re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None
        or not remote_stage_root
        or not remote_dir.startswith(remote_stage_root.rstrip("/") + "/")
    ):
        blockers.append("remote artifact identity is outside its bound stage root")
    if not job_contract_path.is_file():
        blockers.append(f"remote job contract is missing: {job_contract_path}")
    else:
        shutil.copy2(job_contract_path, contract_archive)
        contract = read_json(contract_archive)
        contract_fingerprint = str(contract.get("input_fingerprint_sha256") or "")
        explicit_workdir = contract.get("remote_workdir")
        remote_basename = Path(remote_dir.rstrip("/")).name
        derived_workdir_matches = (
            contract.get("schema_version") == "spatialaccagent.remote_semantic_job.v1"
            and re.fullmatch(
                rf"{re.escape(fingerprint[:12])}_[0-9]+",
                remote_basename,
            )
            is not None
        )
        workdir_matches = (
            explicit_workdir == remote_dir
            if explicit_workdir is not None
            else derived_workdir_matches
        )
        contract_identity = {
            "status": (
                "pass"
                if contract_fingerprint == fingerprint and workdir_matches
                else "fail"
            ),
            "binding_mode": (
                "explicit_remote_workdir"
                if explicit_workdir is not None
                else "fingerprint_derived_remote_workdir"
            ),
            "contract_schema_version": contract.get("schema_version"),
            "contract_fingerprint_sha256": contract_fingerprint or None,
            "remote_workdir": remote_dir,
        }
        if contract_identity["status"] != "pass":
            blockers.append(
                "archived remote job contract does not bind the fingerprint/workdir"
            )

    def indexed_files(
        paths: list[Path],
        archive_dir: Path | None = None,
    ) -> list[dict[str, Any]]:
        rows = []
        seen: set[Path] = set()
        for raw_path in paths:
            path = raw_path.resolve()
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            archived_path = path
            if archive_dir is not None:
                archive_dir.mkdir(parents=True, exist_ok=True)
                archived_path = (
                    archive_dir / f"{len(rows):03d}_{safe_id(path.name)}"
                ).resolve()
                if archived_path != path:
                    shutil.copy2(path, archived_path)
            rows.append(
                {
                    "path": str(archived_path),
                    "relative_path": (
                        str(archived_path.relative_to(run_dir.resolve()))
                        if archived_path.is_relative_to(run_dir.resolve())
                        else None
                    ),
                    "source_path": str(path),
                    "source_relative_path": (
                        str(path.relative_to(run_dir.resolve()))
                        if path.is_relative_to(run_dir.resolve())
                        else None
                    ),
                    "bytes": archived_path.stat().st_size,
                    "sha256": sha256_file(archived_path),
                }
            )
        return rows

    missing_required = [
        str(path)
        for path in required_evidence_paths
        if not path.is_file()
    ]
    if missing_required:
        blockers.append(
            "required local evidence is missing: " + ", ".join(missing_required)
        )
    source_snapshots = []
    snapshots_dir = receipt_dir / "source_snapshots"
    for index, source in enumerate(snapshot_source_paths or []):
        if not source.is_file():
            blockers.append(f"requested source snapshot is missing: {source}")
            continue
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        destination = snapshots_dir / f"{index:03d}_{source.name}"
        shutil.copy2(source, destination)
        source_snapshots.append(
            {
                "source_path": str(source.resolve()),
                "snapshot_path": str(destination.resolve()),
                "bytes": destination.stat().st_size,
                "sha256": sha256_file(destination),
            }
        )
    receipt_path = receipt_dir / "receipt.json"
    remote_acknowledgment_path = receipt_dir / "remote_acknowledgment.json"
    remote_receipt_path = f"{remote_dir}/{REMOTE_ARTIFACT_RECEIPT}"
    receipt = {
        "schema_version": "spatialaccagent.remote_artifact_receipt.v1",
        "status": "pass" if not blockers else "fail",
        "created_unix_time": time.time(),
        "namespace": namespace,
        "input_fingerprint_sha256": fingerprint,
        "remote_stage_root": remote_stage_root,
        "remote_workdir": remote_dir,
        "remote_receipt_path": remote_receipt_path,
        "job_contract": (
            {
                "path": str(contract_archive),
                "sha256": sha256_file(contract_archive),
            }
            if contract_archive.is_file()
            else None
        ),
        "job_contract_identity": contract_identity,
        "evidence_files": indexed_files(evidence_paths, receipt_dir / "evidence"),
        "required_evidence_paths": [str(path.resolve()) for path in required_evidence_paths],
        "source_identities": indexed_files(source_identity_paths),
        "source_snapshots": source_snapshots,
        "retention_policy": {
            "remote_prune_requires_this_receipt": True,
            "active_and_current_jobs_are_never_pruned": True,
            "completed_jobs_retained": remote_artifact_keep_completed(),
        },
        "blockers": blockers,
    }
    write_json(receipt_path, receipt)
    if blockers:
        return {
            "status": "fail",
            "receipt": str(receipt_path),
            "receipt_sha256": sha256_file(receipt_path),
            "remote_receipt": remote_receipt_path,
            "blockers": blockers,
        }
    write_json(remote_acknowledgment_path, receipt)
    upload = command_result(
        [
            "scp",
            *scp_options(port),
            str(remote_acknowledgment_path),
            f"{host}:{remote_receipt_path}",
        ],
        receipt_dir,
        timeout_sec,
    )
    status = "pass" if upload.get("status") == "pass" else "fail"
    upload_blockers = (
        []
        if status == "pass"
        else ["local evidence receipt could not be acknowledged in the remote workdir"]
    )
    local_receipt = {
        **receipt,
        "status": status,
        "receipt_upload": upload,
        "blockers": upload_blockers,
    }
    write_json(receipt_path, local_receipt)
    return {
        "status": status,
        "receipt": str(receipt_path),
        "receipt_sha256": sha256_file(receipt_path),
        "remote_acknowledgment": str(remote_acknowledgment_path),
        "remote_acknowledgment_sha256": sha256_file(remote_acknowledgment_path),
        "remote_receipt": remote_receipt_path,
        "receipt_upload": upload,
        "blockers": upload_blockers,
    }


def prepare_remote_artifact_acknowledgment_retry(
    receipt_path: Path,
) -> dict[str, Any]:
    receipt = read_json(receipt_path) if receipt_path.is_file() else {}
    blockers: list[str] = []
    if receipt.get("schema_version") != "spatialaccagent.remote_artifact_receipt.v1":
        blockers.append("local remote-artifact receipt schema is invalid")
    fingerprint = str(receipt.get("input_fingerprint_sha256") or "")
    remote_stage_root = str(receipt.get("remote_stage_root") or "").rstrip("/")
    remote_dir = str(receipt.get("remote_workdir") or "").rstrip("/")
    remote_receipt = str(receipt.get("remote_receipt_path") or "")
    if (
        re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None
        or not remote_stage_root
        or not remote_dir.startswith(remote_stage_root + "/")
        or remote_receipt != f"{remote_dir}/{REMOTE_ARTIFACT_RECEIPT}"
    ):
        blockers.append("local receipt remote identity is invalid")

    def verify_rows(rows: Any, path_field: str, label: str) -> list[dict[str, Any]]:
        verified: list[dict[str, Any]] = []
        if not isinstance(rows, list):
            blockers.append(f"local receipt {label} inventory is invalid")
            return verified
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                blockers.append(f"local receipt {label}[{index}] is invalid")
                continue
            path = Path(str(row.get(path_field) or ""))
            expected = str(row.get("sha256") or "")
            if not path.is_file() or not expected or sha256_file(path) != expected:
                blockers.append(
                    f"archived {label}[{index}] is missing or changed: {path}"
                )
                continue
            verified.append(row)
        return verified

    contract = receipt.get("job_contract")
    if not isinstance(contract, dict):
        blockers.append("local receipt has no archived job contract")
    else:
        verify_rows([contract], "path", "job contract")
    evidence_rows = verify_rows(receipt.get("evidence_files"), "path", "evidence")
    snapshot_rows = verify_rows(
        receipt.get("source_snapshots"), "snapshot_path", "source snapshot"
    )
    archived_sources = {
        str(Path(str(row.get("source_path") or "")).resolve())
        for row in evidence_rows
        if row.get("source_path")
    }
    required_sources = {
        str(Path(str(path)).resolve())
        for path in receipt.get("required_evidence_paths", [])
        if str(path)
    }
    missing_required = sorted(required_sources - archived_sources)
    if missing_required:
        blockers.append(
            "required evidence has no immutable archived copy: "
            + ", ".join(missing_required)
        )
    if not evidence_rows:
        blockers.append("local receipt has no verified evidence files")
    if receipt.get("namespace") == "board_vcs" and not snapshot_rows:
        blockers.append("board VCS receipt has no verified staged-source snapshots")
    if blockers:
        return {"status": "fail", "receipt": str(receipt_path), "blockers": blockers}

    acknowledgment_path = receipt_path.parent / "remote_acknowledgment.json"
    existing_acknowledgment = (
        read_json(acknowledgment_path) if acknowledgment_path.is_file() else {}
    )
    existing_revalidation = existing_acknowledgment.get("archive_revalidation")
    revalidated_unix_time = (
        existing_revalidation.get("revalidated_unix_time")
        if (
            existing_acknowledgment.get("input_fingerprint_sha256") == fingerprint
            and isinstance(existing_revalidation, dict)
            and isinstance(existing_revalidation.get("revalidated_unix_time"), (int, float))
        )
        else time.time()
    )
    acknowledgment = {
        key: value
        for key, value in receipt.items()
        if key not in {"receipt_upload", "blockers", "status"}
    }
    acknowledgment.update(
        {
            "status": "pass",
            "blockers": [],
            "archive_revalidation": {
                "status": "pass",
                "verified_evidence_file_count": len(evidence_rows),
                "verified_source_snapshot_count": len(snapshot_rows),
                "revalidated_unix_time": revalidated_unix_time,
            },
        }
    )
    write_json(acknowledgment_path, acknowledgment)
    return {
        "status": "ready",
        "receipt": str(receipt_path),
        "remote_acknowledgment": str(acknowledgment_path),
        "remote_acknowledgment_sha256": sha256_file(acknowledgment_path),
        "remote_receipt": remote_receipt,
        "blockers": [],
    }


def finalize_remote_artifact_acknowledgment_retry(
    receipt_path: Path,
    verified_remote_sha256: str,
) -> dict[str, Any]:
    prepared = prepare_remote_artifact_acknowledgment_retry(receipt_path)
    if prepared.get("status") != "ready":
        return prepared
    expected = str(prepared["remote_acknowledgment_sha256"])
    if verified_remote_sha256 != expected:
        return {
            "status": "fail",
            "receipt": str(receipt_path),
            "blockers": ["remote acknowledgment hash does not match local archive"],
        }
    receipt = read_json(receipt_path)
    receipt.update(
        {
            "status": "pass",
            "blockers": [],
            "receipt_upload": {
                "status": "pass",
                "transport": "externally_verified_scp",
                "remote_receipt": prepared["remote_receipt"],
                "remote_sha256": verified_remote_sha256,
                "verified_unix_time": time.time(),
            },
        }
    )
    write_json(receipt_path, receipt)
    return {
        **prepared,
        "status": "pass",
        "receipt_sha256": sha256_file(receipt_path),
    }


REMOTE_SEMANTIC_JOB_CONTRACT = ".spatialacc_semantic_job.json"


def adaptive_stall_evidence_from_progress_callback(
    progress_callback: Callable[[dict[str, Any]], None] | None,
    remote_dir: str,
) -> dict[str, Any]:
    if progress_callback is None:
        return {}
    snapshot_path = getattr(progress_callback, "snapshot_path", None)
    raw_path = getattr(progress_callback, "raw_path", None)
    fingerprint = str(getattr(progress_callback, "fingerprint", "") or "")
    if isinstance(snapshot_path, Path) and snapshot_path.is_file():
        try:
            snapshot = read_json(snapshot_path)
        except Exception:
            snapshot = {}
        evidence = snapshot.get("adaptive_semantic_stall_evidence")
        if (
            isinstance(evidence, dict)
            and snapshot.get("remote_workdir") == remote_dir
            and (not fingerprint or snapshot.get("input_fingerprint_sha256") == fingerprint)
        ):
            return evidence
    if not isinstance(raw_path, Path) or not raw_path.is_file():
        return {}
    parsed = read_complete_jsonl(raw_path)
    records = parsed.get("records", [])
    return adaptive_semantic_stall_evidence(
        records if isinstance(records, list) else []
    )


def zero_time_livelock_evidence_from_progress_callback(
    progress_callback: Callable[[dict[str, Any]], None] | None,
    remote_dir: str,
) -> dict[str, Any]:
    """Return a verifier-owned zero-simulation-time failure, when proven.

    This is intentionally separate from a semantic stall: a semantic stall
    advances simulation cycles while architectural state remains unchanged;
    this failure means the simulator stopped advancing cycles altogether while
    its remote job remains alive.
    """

    if progress_callback is None:
        return {}
    evidence = getattr(progress_callback, "zero_time_livelock_evidence", {})
    if not isinstance(evidence, dict):
        return {}
    if evidence.get("remote_workdir") != remote_dir:
        return {}
    return evidence


def terminate_remote_on_proven_semantic_stall(
    *,
    host: str,
    port: int,
    remote_dir: str,
    cwd: Path,
    label: str,
    pid: int | None,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    if (
        not semantic_stall_termination_label_allowed(label)
        or not isinstance(pid, int)
        or pid <= 0
        or evidence.get("status") != "proven_semantic_stall"
    ):
        return {
            "status": "not_run",
            "reason": "a running VCS simulation with proven adaptive semantic stall is required",
        }
    exit_name = f".spatialacc_{safe_id(label)}.exit"
    marker = "SPATIALACC_ADAPTIVE_SEMANTIC_STALL_TERMINATED"
    command = " ".join(
        [
            "set -u;",
            f"cd {shlex.quote(remote_dir)};",
            f"pid={pid};",
            f"exit_file={shlex.quote(exit_name)};",
            "if [ -f \"$exit_file\" ]; then",
            f"printf '{marker} state=already_done pid=%s\\n' \"$pid\";",
            "elif kill -0 \"$pid\" 2>/dev/null; then",
            "kill -TERM -- \"-$pid\" 2>/dev/null || kill -TERM \"$pid\" 2>/dev/null || true;",
            "attempt=0;",
            "while kill -0 \"$pid\" 2>/dev/null && [ \"$attempt\" -lt 5 ]; do",
            "attempt=$((attempt + 1)); sleep 1;",
            "done;",
            "if kill -0 \"$pid\" 2>/dev/null; then",
            "kill -KILL -- \"-$pid\" 2>/dev/null || kill -KILL \"$pid\" 2>/dev/null || true;",
            "fi;",
            f"printf '{SEMANTIC_STALL_EXIT_CODE}\\n' > \"$exit_file\";",
            f"printf '{marker} state=terminated pid=%s rc={SEMANTIC_STALL_EXIT_CODE}\\n' \"$pid\";",
            "else",
            f"printf '{marker} state=raced_with_completion pid=%s\\n' \"$pid\";",
            "fi;",
        ]
    )
    result = command_result(remote_shell(host, port, command), cwd, 60)
    output = f"{result.get('stdout_tail') or ''}\n{result.get('stderr_tail') or ''}"
    terminated = (
        result.get("status") == "pass"
        and f"{marker} state=terminated" in output
    )
    return {
        "schema_version": "spatialaccagent.adaptive_semantic_stall_termination.v1",
        "status": "pass" if terminated else "not_run",
        "remote_workdir": remote_dir,
        "remote_pid": pid,
        "remote_exit_code": SEMANTIC_STALL_EXIT_CODE if terminated else None,
        "evidence": evidence,
        "transport": result,
        "fixed_wall_clock_timeout": False,
        "fixed_cycle_timeout": False,
    }


def terminate_remote_on_proven_zero_time_livelock(
    *,
    host: str,
    port: int,
    remote_dir: str,
    cwd: Path,
    label: str,
    pid: int | None,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    if (
        not semantic_stall_termination_label_allowed(label)
        or not isinstance(pid, int)
        or pid <= 0
        or evidence.get("status") != "proven_zero_time_livelock"
    ):
        return {
            "status": "not_run",
            "reason": "a running VCS simulation with proven zero-time livelock is required",
        }
    exit_name = f".spatialacc_{safe_id(label)}.exit"
    marker = "SPATIALACC_ZERO_TIME_LIVELOCK_TERMINATED"
    command = " ".join(
        [
            "set -u;",
            f"cd {shlex.quote(remote_dir)};",
            f"pid={pid};",
            f"exit_file={shlex.quote(exit_name)};",
            "if [ -f \"$exit_file\" ]; then",
            f"printf '{marker} state=already_done pid=%s\\n' \"$pid\";",
            "elif kill -0 \"$pid\" 2>/dev/null; then",
            "kill -TERM -- \"-$pid\" 2>/dev/null || kill -TERM \"$pid\" 2>/dev/null || true;",
            "attempt=0;",
            "while kill -0 \"$pid\" 2>/dev/null && [ \"$attempt\" -lt 5 ]; do",
            "attempt=$((attempt + 1)); sleep 1;",
            "done;",
            "if kill -0 \"$pid\" 2>/dev/null; then",
            "kill -KILL -- \"-$pid\" 2>/dev/null || kill -KILL \"$pid\" 2>/dev/null || true;",
            "fi;",
            f"printf '{ZERO_TIME_LIVELOCK_EXIT_CODE}\\n' > \"$exit_file\";",
            f"printf '{marker} state=terminated pid=%s rc={ZERO_TIME_LIVELOCK_EXIT_CODE}\\n' \"$pid\";",
            "else",
            f"printf '{marker} state=raced_with_completion pid=%s\\n' \"$pid\";",
            "fi;",
        ]
    )
    result = command_result(remote_shell(host, port, command), cwd, 60)
    output = f"{result.get('stdout_tail') or ''}\n{result.get('stderr_tail') or ''}"
    terminated = (
        result.get("status") == "pass"
        and f"{marker} state=terminated" in output
    )
    return {
        "schema_version": "spatialaccagent.zero_time_livelock_termination.v1",
        "status": "pass" if terminated else "not_run",
        "remote_workdir": remote_dir,
        "remote_pid": pid,
        "remote_exit_code": ZERO_TIME_LIVELOCK_EXIT_CODE if terminated else None,
        "evidence": evidence,
        "transport": result,
        "fixed_wall_clock_timeout": False,
        "fixed_cycle_timeout": False,
    }


def semantic_stall_termination_label_allowed(label: str) -> bool:
    """Restrict adaptive termination to real VCS simulation job namespaces."""

    return bool(
        label == "vcs_simulate"
        or label == "vcs_checkpoint_equivalence_simulate"
        or label.startswith("vcs_checkpoint_equivalence_simulate_")
    )


def progress_callback_observation(
    progress_callback: Callable[[dict[str, Any]], None] | None,
    *,
    host: str,
    port: int,
    remote_dir: str,
    cwd: Path,
    state: str,
    pid: int | None,
    poll_attempt: int,
    label: str,
    process_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observation: dict[str, Any] = {
        "state": state,
        "pid": pid,
        "poll_attempt": poll_attempt,
        "remote_workdir": remote_dir,
        "label": label,
    }
    if isinstance(process_snapshot, dict):
        observation["process_snapshot"] = process_snapshot
    if progress_callback is None:
        return observation
    log_name = str(
        getattr(progress_callback, "remote_progress_log_name", "") or ""
    )
    if not log_name:
        return observation
    if Path(log_name).name != log_name or log_name in {".", ".."}:
        raise ValueError("remote progress log name must be an isolated basename")
    command = " ".join(
        [
            "set -u;",
            f"cd {shlex.quote(remote_dir)};",
            f"if [ -f {shlex.quote(log_name)} ]; then",
            f"tail -c 12000 -- {shlex.quote(log_name)};",
            "fi;",
        ]
    )
    result = command_result(remote_shell(host, port, command), cwd, 60)
    observation["progress_log_tail"] = str(result.get("stdout_tail") or "")
    observation["progress_log_transport"] = {
        "status": result.get("status"),
        "returncode": result.get("returncode"),
    }
    return observation


def semantic_remote_job_contract(
    staging: Path,
    *,
    fingerprint: str,
    stage_id: str,
    top_module: str,
    tool_profile: dict[str, Any],
    compile_defines: list[str],
    source_names: list[str],
    plusargs: list[str],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    payload = [
        {
            "path": path.relative_to(staging).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in sorted(staging.rglob("*"))
        if path.is_file() and path.name != REMOTE_SEMANTIC_JOB_CONTRACT
    ]
    contract = {
        "schema_version": "spatialaccagent.remote_semantic_job.v1",
        "stage_id": stage_id,
        "top_module": top_module,
        "input_fingerprint_sha256": fingerprint,
        "tool_profile": tool_profile,
        "compile_defines": list(compile_defines),
        "source_names": list(source_names),
        "plusargs": list(plusargs),
        "payload": payload,
    }
    return contract, payload


def remote_semantic_job_candidates(
    host: str,
    port: int,
    remote_stage_root: str,
    fingerprint: str,
    cwd: Path,
    probe_timeout_sec: int = 60,
) -> tuple[list[str] | None, dict[str, Any]]:
    prefix = fingerprint[:12]
    completion_marker = "SPATIALACC_REMOTE_CANDIDATES_COMPLETE"
    command = " ".join(
        [
            "set -eu; export LANG=C LC_ALL=C;",
            f"root={shlex.quote(remote_stage_root)}; count=0;",
            "if [ -d \"$root\" ]; then",
            f"for path in \"$root\"/{shlex.quote(prefix + '_')}*; do",
            "[ -d \"$path\" ] || continue;",
            "suffix=${path##*/}; suffix=${suffix#*_};",
            "case \"$suffix\" in ''|*[!0-9]*) continue;; esac;",
            "mtime=$(stat -c '%Y' \"$path\");",
            "printf '%s|%s\\n' \"$mtime\" \"$path\"; count=$((count + 1));",
            "done;",
            "fi;",
            f"printf '{completion_marker} count=%s\\n' \"$count\";",
        ]
    )
    result = command_result(remote_shell(host, port, command), cwd, probe_timeout_sec)
    stdout = str(result.get("stdout_tail") or "")
    marker = re.search(rf"{completion_marker} count=(\d+)", stdout)
    if result.get("status") != "pass" or marker is None:
        return None, {
            "status": "indeterminate",
            "failure_class": "remote_transport_failure",
            "probe": result,
            "summary": "remote semantic candidate discovery did not complete",
        }
    rows: list[tuple[float, str]] = []
    expected_prefix = remote_stage_root.rstrip("/") + "/" + prefix + "_"
    malformed_lines: list[str] = []
    for line in stdout.splitlines():
        if completion_marker in line:
            continue
        timestamp, separator, path = line.partition("|")
        if not separator or not path.startswith(expected_prefix):
            if line.strip():
                malformed_lines.append(line)
            continue
        suffix = path[len(expected_prefix):]
        if not suffix.isdigit():
            malformed_lines.append(line)
            continue
        try:
            rows.append((float(timestamp), path))
        except ValueError:
            malformed_lines.append(line)
            continue
    expected_count = int(marker.group(1))
    if malformed_lines or len(rows) != expected_count:
        return None, {
            "status": "indeterminate",
            "failure_class": "remote_transport_failure",
            "probe": result,
            "reported_candidate_count": expected_count,
            "parsed_candidate_count": len(rows),
            "malformed_lines": malformed_lines[-8:],
            "summary": "remote semantic candidate listing was incomplete or malformed",
        }
    return [path for _, path in sorted(rows, reverse=True)], {
        "status": "pass",
        "probe": result,
        "candidate_count": len(rows),
    }


def remote_semantic_payload_matches(
    host: str,
    port: int,
    remote_dir: str,
    cwd: Path,
    local_job_contract_path: Path,
    payload: list[dict[str, str]],
    probe_timeout_sec: int = 60,
) -> tuple[bool | None, dict[str, Any]]:
    recovery_dir = cwd / "remote_recovery_identity"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    remote_contract = recovery_dir / REMOTE_SEMANTIC_JOB_CONTRACT
    presence_marker = "SPATIALACC_REMOTE_CONTRACT_PRESENCE"
    presence_command = " ".join(
        [
            "set -u;",
            f"if [ ! -d {shlex.quote(remote_dir)} ]; then",
            f"printf '{presence_marker} state=directory_missing\\n';",
            f"elif [ -f {shlex.quote(remote_dir + '/' + REMOTE_SEMANTIC_JOB_CONTRACT)} ]; then",
            f"printf '{presence_marker} state=present\\n';",
            "else",
            f"printf '{presence_marker} state=missing\\n';",
            "fi;",
        ]
    )
    presence = command_result(
        remote_shell(host, port, presence_command), recovery_dir, probe_timeout_sec
    )
    presence_match = re.search(
        rf"{presence_marker} state=(present|missing|directory_missing)",
        str(presence.get("stdout_tail") or ""),
    )
    if presence.get("status") != "pass" or presence_match is None:
        return None, {
            "status": "indeterminate",
            "failure_class": "remote_transport_failure",
            "contract_presence_probe": presence,
            "summary": "remote semantic identity presence probe did not complete",
        }
    contract_presence = presence_match.group(1)
    if contract_presence == "directory_missing":
        return False, {
            "status": "fail",
            "identity_source": "candidate_directory_disappeared",
            "contract_presence_probe": presence,
        }
    if contract_presence == "present":
        remote_contract.unlink(missing_ok=True)
        contract_download = copy_remote_file(
            host,
            port,
            f"{remote_dir}/{REMOTE_SEMANTIC_JOB_CONTRACT}",
            remote_contract,
            recovery_dir,
            probe_timeout_sec,
        )
        if contract_download.get("status") != "pass" or not remote_contract.is_file():
            return None, {
                "status": "indeterminate",
                "failure_class": "remote_transport_failure",
                "contract_presence_probe": presence,
                "contract_download": contract_download,
                "summary": "remote semantic job contract download did not complete",
            }
        remote_contract_sha = sha256_file(remote_contract)
        local_contract_sha = sha256_file(local_job_contract_path)
        matched = remote_contract_sha == local_contract_sha
        return matched, {
            "status": "pass" if matched else "fail",
            "identity_source": "full_remote_job_contract",
            "remote_job_contract_sha256": remote_contract_sha,
            "expected_job_contract_sha256": local_contract_sha,
            "contract_download": contract_download,
        }

    relative_paths = [str(row["path"]) for row in payload]
    if not relative_paths:
        return False, {
            "status": "fail",
            "identity_source": "legacy_full_payload_sha256_compatibility",
            "summary": "legacy remote job has no payload files to bind its identity",
        }
    hash_marker = "SPATIALACC_REMOTE_PAYLOAD_HASHES"
    hash_command = " ".join(
        [
            "set -u; export LANG=C LC_ALL=C;",
            f"if ! cd {shlex.quote(remote_dir)}; then",
            f"printf '{hash_marker} state=directory_missing\\n'; exit 0; fi;",
            "for path in",
            *(shlex.quote(path) for path in relative_paths),
            "; do if [ ! -f \"$path\" ]; then",
            f"printf '{hash_marker} state=payload_missing path=%s\\n' \"$path\"; exit 0; fi; done;",
            "sha256sum --",
            *(shlex.quote(path) for path in relative_paths),
            "; rc=$?;",
            f"printf '{hash_marker} state=complete rc=%s count={len(relative_paths)}\\n' \"$rc\";",
            "exit 0;",
        ]
    )
    hashes = command_result(
        remote_shell(host, port, hash_command), recovery_dir, probe_timeout_sec
    )
    hash_stdout = str(hashes.get("stdout_tail") or "")
    hash_state = re.search(
        rf"{hash_marker} state=(complete|payload_missing|directory_missing)(?: rc=(-?\d+))?(?: count=(\d+))?",
        hash_stdout,
    )
    if hashes.get("status") != "pass" or hash_state is None:
        return None, {
            "status": "indeterminate",
            "failure_class": "remote_transport_failure",
            "identity_source": "legacy_full_payload_sha256_compatibility",
            "hash_probe": hashes,
            "summary": "remote semantic payload hash probe did not complete",
        }
    if hash_state.group(1) != "complete":
        return False, {
            "status": "fail",
            "identity_source": "legacy_full_payload_sha256_compatibility",
            "hash_probe": hashes,
            "remote_payload_state": hash_state.group(1),
        }
    hash_rc = int(hash_state.group(2)) if hash_state.group(2) is not None else None
    reported_count = int(hash_state.group(3)) if hash_state.group(3) is not None else None
    actual_lines = [
        line
        for line in hash_stdout.splitlines()
        if line.strip() and hash_marker not in line
    ]
    actual_hashes = [line.split(maxsplit=1)[0] for line in actual_lines]
    expected_hashes = [str(row["sha256"]) for row in payload]
    matched = (
        hash_rc == 0
        and reported_count == len(payload)
        and len(actual_lines) == len(payload)
        and actual_hashes == expected_hashes
    )
    return matched, {
        "status": "pass" if matched else "fail",
        "identity_source": "legacy_full_payload_sha256_compatibility",
        "contract_presence_probe": presence,
        "payload_file_count": len(payload),
        "hash_command_status": hashes.get("status"),
        "hash_command_returncode": hash_rc,
        "reported_payload_file_count": reported_count,
    }


def normalized_exit_signal(returncode: int | None) -> int | None:
    """Normalize direct and shell-encoded process signal exit codes."""

    if not isinstance(returncode, int) or isinstance(returncode, bool):
        return None
    if returncode < 0:
        return -returncode
    if 129 <= returncode <= 255:
        return returncode - 128
    return None


def remote_job_state_probe_command(
    remote_dir: str,
    pid_name: str,
    exit_name: str,
) -> str:
    """Build one bounded status probe for a detached remote simulator session."""

    process_program = (
        '$4 == sid {'
        ' count += 1;'
        ' if (count <= 32) {'
        ' printf "SPATIALACC_REMOTE_JOB_PROCESS pid=%s ppid=%s pgid=%s sid=%s stat=%s comm=%s\\n",'
        ' $1, $2, $3, $4, $5, $6;'
        ' }'
        '}'
        ' END {'
        ' printf "SPATIALACC_REMOTE_JOB_PROCESS_SUMMARY count=%d truncated=%s\\n",'
        ' count, (count > 32 ? "true" : "false");'
        '}'
    )
    return " ".join(
        [
            "set -u;",
            f"if ! cd {shlex.quote(remote_dir)}; then",
            "printf 'SPATIALACC_REMOTE_JOB_STATUS state=missing\\n'; exit 0; fi;",
            f"if [ -f {shlex.quote(exit_name)} ]; then",
            f"rc=$(cat {shlex.quote(exit_name)});",
            "printf 'SPATIALACC_REMOTE_JOB_STATUS state=done rc=%s\\n' \"$rc\";",
            f"elif [ -f {shlex.quote(pid_name)} ]; then",
            f"pid=$(cat {shlex.quote(pid_name)});",
            "if kill -0 \"$pid\" 2>/dev/null; then",
            "printf 'SPATIALACC_REMOTE_JOB_STATUS state=running pid=%s\\n' \"$pid\";",
            "ps -e -o pid= -o ppid= -o pgid= -o sid= -o stat= -o comm= | "
            f"awk -v sid=\"$pid\" {shlex.quote(process_program)};",
            "else",
            "printf 'SPATIALACC_REMOTE_JOB_STATUS state=lost pid=%s\\n' \"$pid\";",
            "fi;",
            "else",
            "printf 'SPATIALACC_REMOTE_JOB_STATUS state=missing\\n';",
            "fi;",
        ]
    )


def parse_remote_job_state_probe(output: str) -> dict[str, Any]:
    """Parse a bounded remote job state and its last observed session tree."""

    status_match = re.search(
        r"SPATIALACC_REMOTE_JOB_STATUS state=(\w+)(?: rc=(-?\d+))?(?: pid=(\d+))?",
        output,
    )
    state = status_match.group(1) if status_match else "unknown"
    pid = (
        int(status_match.group(3))
        if status_match is not None and status_match.group(3) is not None
        else None
    )
    processes = []
    for match in re.finditer(
        r"SPATIALACC_REMOTE_JOB_PROCESS pid=(\d+) ppid=(\d+) pgid=(\d+) "
        r"sid=(\d+) stat=(\S+) comm=(\S+)",
        output,
    ):
        processes.append(
            {
                "pid": int(match.group(1)),
                "ppid": int(match.group(2)),
                "pgid": int(match.group(3)),
                "sid": int(match.group(4)),
                "state": match.group(5),
                "command": match.group(6),
            }
        )
    summary_match = re.search(
        r"SPATIALACC_REMOTE_JOB_PROCESS_SUMMARY count=(\d+) truncated=(true|false)",
        output,
    )
    reported_count = (
        int(summary_match.group(1)) if summary_match is not None else len(processes)
    )
    simulator_like = any(
        "simv" in str(row["command"]).lower()
        or str(row["command"]).lower() in {"vcs", "vcs1"}
        for row in processes
    )
    simulator_commands = sorted(
        {
            str(row["command"])
            for row in processes
            if "simv" in str(row["command"]).lower()
            or str(row["command"]).lower() in {"vcs", "vcs1"}
        }
    )
    return {
        "state": state,
        "returncode": (
            int(status_match.group(2))
            if status_match is not None and status_match.group(2) is not None
            else None
        ),
        "pid": pid,
        "process_snapshot": {
            "schema_version": REMOTE_PROCESS_SNAPSHOT_SCHEMA,
            "status": "observed" if processes else "not_observed",
            "session_leader_pid": pid,
            "processes": processes,
            "reported_process_count": reported_count,
            "truncated": (
                summary_match is not None and summary_match.group(2) == "true"
            ),
            "simulator_like_process_observed": simulator_like,
            "simulator_process_commands": simulator_commands,
        },
    }


def remote_runner_process_provenance(
    *,
    label: str,
    command: str | None,
    launch_pid: int | None,
    exit_code: int | None,
    last_process_snapshot: dict[str, Any] | None,
    reattached: bool,
) -> dict[str, Any]:
    """Describe runner ownership without attributing a signal to HDL source."""

    snapshot = (
        last_process_snapshot
        if isinstance(last_process_snapshot, dict)
        else {
            "schema_version": REMOTE_PROCESS_SNAPSHOT_SCHEMA,
            "status": "not_observed",
            "processes": [],
            "simulator_like_process_observed": False,
        }
    )
    signal_number = normalized_exit_signal(exit_code)
    simulator_observed = snapshot.get("simulator_like_process_observed") is True
    if signal_number is not None and simulator_observed:
        attribution = "runner_owned_simulator_process_signal_exit"
    elif signal_number is not None:
        attribution = "runner_owned_session_signal_exit_without_simulator_snapshot"
    elif exit_code == 0:
        attribution = "normal_runner_owned_process_exit"
    elif exit_code is not None:
        attribution = "runner_owned_nonzero_process_exit"
    else:
        attribution = "runner_exit_not_observed"
    return {
        "schema_version": REMOTE_RUNNER_PROCESS_PROVENANCE_SCHEMA,
        "status": "observed" if exit_code is not None else "incomplete",
        "label": label,
        "detached_runner_session": True,
        "reattached_existing_job": reattached,
        "launch_pid": launch_pid,
        "command_sha256": (
            hashlib.sha256(command.encode("utf-8")).hexdigest()
            if isinstance(command, str) and command
            else None
        ),
        "exit_code": exit_code,
        "signal_number": signal_number,
        "attribution": attribution,
        "last_running_process_count": snapshot.get("reported_process_count"),
        "last_simulator_process_commands": snapshot.get(
            "simulator_process_commands", []
        ),
        "last_running_process_snapshot": snapshot,
        "deterministic_hdl_or_testbench_event_observed": False,
        "source_semantic_repair_eligible": False,
    }


def remote_background_job_state(
    host: str,
    port: int,
    remote_dir: str,
    cwd: Path,
    label: str,
    probe_timeout_sec: int = 60,
) -> dict[str, Any]:
    stem = f".spatialacc_{safe_id(label)}"
    pid_name = f"{stem}.pid"
    exit_name = f"{stem}.exit"
    command = remote_job_state_probe_command(remote_dir, pid_name, exit_name)
    result = command_result(remote_shell(host, port, command), cwd, probe_timeout_sec)
    parsed = parse_remote_job_state_probe(str(result.get("stdout_tail") or ""))
    state = str(parsed.get("state") or "unknown")
    determinate = result.get("status") == "pass" and state in {
        "done",
        "running",
        "lost",
        "missing",
    }
    return {
        "state": state,
        "certainty": "determinate" if determinate else "indeterminate",
        "returncode": parsed.get("returncode"),
        "pid": parsed.get("pid"),
        "process_snapshot": parsed.get("process_snapshot", {}),
        "probe": result,
    }


def wait_for_existing_remote_job(
    host: str,
    port: int,
    remote_dir: str,
    cwd: Path,
    timeout_sec: int,
    label: str,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    unbounded = wall_timeout(timeout_sec) is None
    attempts = 0
    transport_failures = 0
    state = "unknown"
    returncode: int | None = None
    observer_errors: list[str] = []
    semantic_stall_evidence: dict[str, Any] = {}
    semantic_stall_termination: dict[str, Any] = {"status": "not_run"}
    zero_time_livelock_evidence: dict[str, Any] = {}
    zero_time_livelock_termination: dict[str, Any] = {"status": "not_run"}
    last_running_process_snapshot: dict[str, Any] = {}
    while unbounded or time.monotonic() - started < timeout_sec:
        row = remote_background_job_state(host, port, remote_dir, cwd, label)
        attempts += 1
        if row.get("probe", {}).get("status") != "pass":
            transport_failures += 1
            time.sleep(15.0)
            continue
        state = str(row.get("state") or "unknown")
        process_snapshot = row.get("process_snapshot")
        if (
            state == "running"
            and isinstance(process_snapshot, dict)
            and process_snapshot.get("processes")
            and (
                process_snapshot.get("simulator_like_process_observed") is True
                or last_running_process_snapshot.get(
                    "simulator_like_process_observed"
                )
                is not True
            )
        ):
            last_running_process_snapshot = dict(process_snapshot)
        if progress_callback is not None:
            try:
                progress_callback(
                    progress_callback_observation(
                        progress_callback,
                        host=host,
                        port=port,
                        remote_dir=remote_dir,
                        cwd=cwd,
                        state=state,
                        pid=row.get("pid"),
                        poll_attempt=attempts,
                        label=label,
                        process_snapshot=(
                            row.get("process_snapshot")
                            if isinstance(row.get("process_snapshot"), dict)
                            else None
                        ),
                    )
                )
            except Exception as exc:
                observer_errors.append(str(exc)[:1000])
            try:
                observed_stall = adaptive_stall_evidence_from_progress_callback(
                    progress_callback,
                    remote_dir,
                )
                if observed_stall.get("status") == "proven_semantic_stall":
                    semantic_stall_evidence = observed_stall
                    if (
                        state == "running"
                        and semantic_stall_termination.get("status") != "pass"
                    ):
                        semantic_stall_termination = (
                            terminate_remote_on_proven_semantic_stall(
                                host=host,
                                port=port,
                                remote_dir=remote_dir,
                                cwd=cwd,
                                label=label,
                                pid=row.get("pid"),
                                evidence=observed_stall,
                            )
                        )
            except Exception as exc:
                observer_errors.append(str(exc)[:1000])
            try:
                observed_zero_time_livelock = (
                    zero_time_livelock_evidence_from_progress_callback(
                        progress_callback,
                        remote_dir,
                    )
                )
                if (
                    observed_zero_time_livelock.get("status")
                    == "proven_zero_time_livelock"
                ):
                    zero_time_livelock_evidence = observed_zero_time_livelock
                    if (
                        state == "running"
                        and zero_time_livelock_termination.get("status") != "pass"
                    ):
                        zero_time_livelock_termination = (
                            terminate_remote_on_proven_zero_time_livelock(
                                host=host,
                                port=port,
                                remote_dir=remote_dir,
                                cwd=cwd,
                                label=label,
                                pid=row.get("pid"),
                                evidence=observed_zero_time_livelock,
                            )
                        )
            except Exception as exc:
                observer_errors.append(str(exc)[:1000])
        if state == "done":
            returncode = row.get("returncode")
            break
        if state in {"lost", "missing"}:
            break
        if state == "unknown":
            transport_failures += 1
            time.sleep(15.0)
            continue
        time.sleep(15.0)
    timed_out = not unbounded and returncode is None
    semantic_stall = (
        returncode == SEMANTIC_STALL_EXIT_CODE
        and semantic_stall_evidence.get("status") == "proven_semantic_stall"
    )
    zero_time_livelock = (
        returncode == ZERO_TIME_LIVELOCK_EXIT_CODE
        and zero_time_livelock_evidence.get("status")
        == "proven_zero_time_livelock"
    )
    return {
        "status": "pass" if returncode == 0 else "fail",
        "returncode": returncode if returncode is not None else (124 if timed_out else 255),
        "failure_class": (
            None
            if returncode == 0
            else "adaptive_semantic_stall"
            if semantic_stall
            else "zero_time_simulation_livelock"
            if zero_time_livelock
            else "remote_tool_failure"
            if returncode is not None
            else "remote_tool_poll_budget_exhausted"
            if timed_out and state == "running"
            else "remote_transport_failure"
        ),
        "transport": "reattached_exact_fingerprint_detached_remote_job",
        "remote_workdir": remote_dir,
        "remote_state": state,
        "poll_attempts": attempts,
        "poll_transport_failures": transport_failures,
        "remote_job_preserved": returncode is None,
        "duration_sec": time.monotonic() - started,
        "progress_observer_errors": observer_errors[-8:],
        "adaptive_semantic_stall_evidence": semantic_stall_evidence,
        "adaptive_semantic_stall_termination": semantic_stall_termination,
        "zero_time_livelock_evidence": zero_time_livelock_evidence,
        "zero_time_livelock_termination": zero_time_livelock_termination,
        "runner_process_provenance": remote_runner_process_provenance(
            label=label,
            command=None,
            launch_pid=None,
            exit_code=returncode,
            last_process_snapshot=last_running_process_snapshot,
            reattached=True,
        ),
    }


def recover_exact_remote_semantic_job(
    host: str,
    port: int,
    remote_stage_root: str,
    fingerprint: str,
    cwd: Path,
    local_job_contract_path: Path,
    payload: list[dict[str, str]],
    timeout_sec: int,
    simulate_command: str,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
    allow_relaunch: bool = True,
    allow_initial_simulation_launch: bool = False,
) -> dict[str, Any] | None:
    started = time.monotonic()
    unbounded = wall_timeout(timeout_sec) is None
    deadline = None if unbounded else started + timeout_sec
    retry_request_path = cwd / REMOTE_JOB_RETRY_REQUEST
    retry_request: dict[str, Any] = {}
    if retry_request_path.is_file():
        try:
            candidate_request = read_json(retry_request_path)
            runner_path = Path(
                str(candidate_request.get("runner_report_path") or "")
            )
            runner_sha256 = str(
                candidate_request.get("runner_report_sha256") or ""
            )
            if (
                candidate_request.get("status") == "ready"
                and candidate_request.get("action")
                == "discard_completed_remote_workdir_and_retry_same_fingerprint"
                and candidate_request.get("input_fingerprint_sha256") == fingerprint
                and runner_path.is_file()
                and runner_sha256
                and sha256_file(runner_path) == runner_sha256
            ):
                retry_request = candidate_request
        except Exception:
            retry_request = {}

    def probe_timeout() -> int:
        if deadline is None:
            return 60
        return max(1, min(60, ceil(deadline - time.monotonic())))

    def retry_pause() -> bool:
        if deadline is not None and time.monotonic() >= deadline:
            return False
        delay = 15.0 if deadline is None else min(15.0, max(0.0, deadline - time.monotonic()))
        if delay > 0:
            time.sleep(delay)
        return deadline is None or time.monotonic() < deadline

    def indeterminate(
        phase: str,
        evidence: dict[str, Any],
        attempts: int,
        remote_dir: str | None = None,
    ) -> dict[str, Any]:
        result = {
            "recovery_state": "indeterminate",
            "status": "fail",
            "failure_class": "remote_semantic_recovery_indeterminate",
            "phase": phase,
            "probe_attempts": attempts,
            "remote_job_preserved": True,
            "evidence": evidence,
            "summary": (
                "remote semantic job recovery remained indeterminate; "
                "remote state was preserved and fresh execution is prohibited"
            ),
        }
        if remote_dir is not None:
            result["remote_dir"] = remote_dir
        return result

    candidate_attempts = 0
    candidate_evidence: dict[str, Any] = {}
    while True:
        candidate_probe = remote_semantic_job_candidates(
            host,
            port,
            remote_stage_root,
            fingerprint,
            cwd,
            probe_timeout(),
        )
        candidate_attempts += 1
        if isinstance(candidate_probe, tuple):
            candidates, candidate_evidence = candidate_probe
        else:
            # Compatibility with callers/tests that supplied the pre-tri-state list shape.
            candidates, candidate_evidence = candidate_probe, {"status": "pass"}
        if candidates is not None:
            break
        if not retry_pause():
            return indeterminate(
                "candidate_discovery", candidate_evidence, candidate_attempts
            )

    for remote_dir in candidates:
        if (
            retry_request
            and retry_request.get("remote_workdir") == remote_dir
        ):
            cleanup = cleanup_retryable_remote_job(
                host,
                port,
                remote_stage_root,
                remote_dir,
                cwd,
                probe_timeout(),
            )
            cleanup_state = cleanup.get("cleanup_state")
            if cleanup.get("status") == "pass" and cleanup_state in {
                "missing",
                "removed",
            }:
                retry_request_path.unlink(missing_ok=True)
                continue
            return indeterminate(
                "retryable_environment_cleanup",
                cleanup,
                1,
                remote_dir,
            )
        identity_attempts = 0
        identity: dict[str, Any] = {}
        while True:
            identity_matches, identity = remote_semantic_payload_matches(
                host,
                port,
                remote_dir,
                cwd,
                local_job_contract_path,
                payload,
                probe_timeout(),
            )
            identity_attempts += 1
            if identity_matches is not None:
                break
            if not retry_pause():
                return indeterminate(
                    "payload_identity", identity, identity_attempts, remote_dir
                )
        if not identity_matches:
            continue

        compile_state_attempts = 0
        while True:
            compile_state = remote_background_job_state(
                host,
                port,
                remote_dir,
                cwd,
                "vcs_compile",
                probe_timeout(),
            )
            compile_state_attempts += 1
            if compile_state.get("certainty") == "determinate" or (
                "certainty" not in compile_state
                and compile_state.get("probe", {}).get("status") == "pass"
                and compile_state.get("state") in {"done", "running", "lost", "missing"}
            ):
                break
            if not retry_pause():
                return indeterminate(
                    "compile_job_state",
                    compile_state,
                    compile_state_attempts,
                    remote_dir,
                )
        if compile_state.get("state") == "running":
            compile_result = wait_for_existing_remote_job(
                host, port, remote_dir, cwd, timeout_sec, "vcs_compile"
            )
        elif compile_state.get("state") == "done":
            compile_rc = compile_state.get("returncode")
            compile_result = {
                "status": "pass" if compile_rc == 0 else "fail",
                "returncode": compile_rc,
                "failure_class": None if compile_rc == 0 else "remote_tool_failure",
                "transport": "recovered_exact_fingerprint_detached_remote_job",
                "remote_workdir": remote_dir,
                "remote_state": "done",
            }
        else:
            continue
        if compile_result.get("status") != "pass":
            return {
                "recovery_state": "recovered",
                "remote_dir": remote_dir,
                "compile": compile_result,
                "simulate": {"status": "not_run", "summary": "recovered compile did not pass"},
                "identity": identity,
            }

        simulate_state_attempts = 0
        while True:
            simulate_state = remote_background_job_state(
                host,
                port,
                remote_dir,
                cwd,
                "vcs_simulate",
                probe_timeout(),
            )
            simulate_state_attempts += 1
            if simulate_state.get("certainty") == "determinate" or (
                "certainty" not in simulate_state
                and simulate_state.get("probe", {}).get("status") == "pass"
                and simulate_state.get("state") in {"done", "running", "lost", "missing"}
            ):
                break
            if not retry_pause():
                return indeterminate(
                    "simulate_job_state",
                    simulate_state,
                    simulate_state_attempts,
                    remote_dir,
                )
        if simulate_state.get("state") == "running":
            simulate_result = wait_for_existing_remote_job(
                host,
                port,
                remote_dir,
                cwd,
                timeout_sec,
                "vcs_simulate",
                progress_callback,
            )
        elif simulate_state.get("state") == "done":
            simulate_rc = simulate_state.get("returncode")
            observer_errors: list[str] = []
            semantic_stall_evidence: dict[str, Any] = {}
            if progress_callback is not None:
                try:
                    progress_callback(
                        progress_callback_observation(
                            progress_callback,
                            host=host,
                            port=port,
                            remote_dir=remote_dir,
                            cwd=cwd,
                            state="done",
                            pid=None,
                            poll_attempt=1,
                            label="vcs_simulate",
                        )
                    )
                    semantic_stall_evidence = (
                        adaptive_stall_evidence_from_progress_callback(
                            progress_callback,
                            remote_dir,
                        )
                    )
                except Exception as exc:
                    observer_errors.append(str(exc)[:1000])
            semantic_stall = (
                simulate_rc == SEMANTIC_STALL_EXIT_CODE
                and semantic_stall_evidence.get("status")
                == "proven_semantic_stall"
            )
            simulate_result = {
                "status": "pass" if simulate_rc == 0 else "fail",
                "returncode": simulate_rc,
                "failure_class": (
                    None
                    if simulate_rc == 0
                    else "adaptive_semantic_stall"
                    if semantic_stall
                    else "remote_tool_failure"
                ),
                "transport": "recovered_exact_fingerprint_detached_remote_job",
                "remote_workdir": remote_dir,
                "remote_state": "done",
                "progress_observer_errors": observer_errors,
                "adaptive_semantic_stall_evidence": semantic_stall_evidence,
                "adaptive_semantic_stall_termination": {
                    "status": "recovered_completed_job"
                    if semantic_stall
                    else "not_run"
                },
            }
        elif simulate_state.get("state") in {"missing", "lost"}:
            if not allow_relaunch:
                if (
                    simulate_state.get("state") == "missing"
                    and allow_initial_simulation_launch
                ):
                    simulate_result = run_remote_background_command(
                        host,
                        port,
                        simulate_command,
                        remote_dir,
                        cwd,
                        timeout_sec,
                        "vcs_simulate",
                        progress_callback,
                    )
                    return {
                        "recovery_state": "recovered",
                        "remote_dir": remote_dir,
                        "compile": compile_result,
                        "simulate": simulate_result,
                        "identity": identity,
                    }
                return {
                    "recovery_state": "recovered",
                    "remote_dir": remote_dir,
                    "compile": compile_result,
                    "simulate": {
                        "status": "fail",
                        "returncode": 255,
                        "failure_class": "remote_job_lost",
                        "remote_workdir": remote_dir,
                        "remote_state": simulate_state.get("state"),
                        "summary": (
                            "the exact remote simulation is no longer attachable; "
                            "relaunch is forbidden for a pending job"
                        ),
                    },
                    "identity": identity,
                }
            simulate_result = run_remote_background_command(
                host,
                port,
                simulate_command,
                remote_dir,
                cwd,
                timeout_sec,
                "vcs_simulate",
                progress_callback,
            )
        else:
            continue
        return {
            "recovery_state": "recovered",
            "remote_dir": remote_dir,
            "compile": compile_result,
            "simulate": simulate_result,
            "identity": identity,
        }
    return None


def run_remote_background_command(
    host: str,
    port: int,
    command: str,
    remote_dir: str,
    cwd: Path,
    timeout_sec: int,
    label: str,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    remote_stage_cleanup: dict[str, Any] = {
        "status": "not_run",
        "summary": "remote stage single-instance cleanup is required only before compilation",
    }
    remote_stage_prune: dict[str, Any] = {
        "status": "not_run",
        "summary": "remote stage pruning is required only before compilation",
    }
    if label == "vcs_compile":
        remote_stage_root = str(Path(remote_dir).parent)
        remote_stage_cleanup = command_result(
            remote_shell(
                host,
                port,
                remote_stage_cleanup_command(remote_stage_root),
            ),
            cwd,
            60 if wall_timeout(timeout_sec) is None else min(timeout_sec, 60),
        )
        if remote_stage_cleanup.get("status") != "pass":
            return {
                "cwd": str(cwd),
                "remote_command": command,
                "remote_workdir": remote_dir,
                "transport": "detached_remote_job_with_short_ssh_polling",
                "launch": {
                    "status": "not_run",
                    "summary": "remote stage single-instance cleanup failed before VCS launch",
                },
                "remote_stage_cleanup": remote_stage_cleanup,
                "remote_stage_prune": remote_stage_prune,
                "remote_state": "not_run",
                "returncode": 125,
                "status": "fail",
                "failure_class": "remote_stage_cleanup_failure",
                "remote_job_preserved": True,
                "duration_sec": time.monotonic() - started,
            }
        remote_stage_prune = command_result(
            remote_shell(
                host,
                port,
                remote_stage_prune_command(
                    remote_stage_root,
                    remote_dir,
                    remote_artifact_keep_completed(),
                ),
            ),
            cwd,
            60 if wall_timeout(timeout_sec) is None else min(timeout_sec, 60),
        )
        if remote_stage_prune.get("status") != "pass":
            # Archive retention is housekeeping, not a tool-correctness
            # prerequisite.  The current content-addressed directory is
            # isolated and active-job cleanup already passed, so preserve the
            # warning but allow the exact VCS command to run.  No deletion is
            # attempted after a failed prune.
            remote_stage_prune["nonblocking"] = True
            remote_stage_prune["summary"] = (
                "remote artifact prune did not complete within its maintenance "
                "budget; current isolated VCS job proceeds without deletion"
            )
    stem = f".spatialacc_{safe_id(label)}"
    pid_name = f"{stem}.pid"
    exit_name = f"{stem}.exit"
    stdout_name = f"{stem}.stdout.log"
    stderr_name = f"{stem}.stderr.log"
    inner = " ".join(
        [
            "set +e;",
            f"bash -lc {shlex.quote(command)};",
            "rc=$?;",
            f"printf '%s\\n' \"$rc\" > {shlex.quote(exit_name)};",
            "exit \"$rc\";",
        ]
    )
    launch_command = " ".join(
        [
            "set -u;",
            f"cd {shlex.quote(remote_dir)};",
            f"rm -f {shlex.quote(pid_name)} {shlex.quote(exit_name)} {shlex.quote(stdout_name)} {shlex.quote(stderr_name)};",
            f"nohup setsid bash -lc {shlex.quote(inner)} > {shlex.quote(stdout_name)} 2> {shlex.quote(stderr_name)} < /dev/null &",
            "pid=$!;",
            f"printf '%s\\n' \"$pid\" > {shlex.quote(pid_name)};",
            "printf 'SPATIALACC_REMOTE_JOB_STARTED pid=%s\\n' \"$pid\";",
        ]
    )
    unbounded = wall_timeout(timeout_sec) is None
    launch = command_result(
        remote_shell(host, port, launch_command),
        cwd,
        60 if unbounded else min(timeout_sec, 60),
    )
    launch_match = re.search(
        r"SPATIALACC_REMOTE_JOB_STARTED pid=(\d+)",
        str(launch.get("stdout_tail") or ""),
    )
    launch_pid = int(launch_match.group(1)) if launch_match is not None else None
    poll_attempts = 0
    transport_failures = 0
    state = "unknown"
    remote_returncode: int | None = None
    poll_records: list[dict[str, Any]] = []
    observer_errors: list[str] = []
    semantic_stall_evidence: dict[str, Any] = {}
    semantic_stall_termination: dict[str, Any] = {"status": "not_run"}
    zero_time_livelock_evidence: dict[str, Any] = {}
    zero_time_livelock_termination: dict[str, Any] = {"status": "not_run"}
    last_running_process_snapshot: dict[str, Any] = {}
    while unbounded or time.monotonic() - started < timeout_sec:
        remaining = None if unbounded else timeout_sec - (time.monotonic() - started)
        poll_command = remote_job_state_probe_command(remote_dir, pid_name, exit_name)
        poll_timeout = 60 if remaining is None else max(1, min(int(remaining), 60))
        poll = command_result(remote_shell(host, port, poll_command), cwd, poll_timeout)
        poll_attempts += 1
        if poll.get("status") != "pass":
            transport_failures += 1
            poll_records.append(
                {
                    "attempt": poll_attempts,
                    "status": "transport_failure",
                    "returncode": poll.get("returncode"),
                    "stderr_tail": poll.get("stderr_tail"),
                }
            )
            time.sleep(15.0 if remaining is None else min(15.0, max(0.0, remaining)))
            continue
        parsed = parse_remote_job_state_probe(str(poll.get("stdout_tail") or ""))
        state = str(parsed.get("state") or "unknown")
        poll_records.append({"attempt": poll_attempts, "status": state})
        process_snapshot = parsed.get("process_snapshot")
        if (
            state == "running"
            and isinstance(process_snapshot, dict)
            and process_snapshot.get("processes")
            and (
                process_snapshot.get("simulator_like_process_observed") is True
                or last_running_process_snapshot.get(
                    "simulator_like_process_observed"
                )
                is not True
            )
        ):
            last_running_process_snapshot = dict(process_snapshot)
        if progress_callback is not None:
            remote_pid = parsed.get("pid")
            try:
                progress_callback(
                    progress_callback_observation(
                        progress_callback,
                        host=host,
                        port=port,
                        remote_dir=remote_dir,
                        cwd=cwd,
                        state=state,
                        pid=remote_pid if isinstance(remote_pid, int) else None,
                        poll_attempt=poll_attempts,
                        label=label,
                        process_snapshot=(
                            parsed.get("process_snapshot")
                            if isinstance(parsed.get("process_snapshot"), dict)
                            else None
                        ),
                    )
                )
            except Exception as exc:
                observer_errors.append(str(exc)[:1000])
            try:
                observed_zero_time_livelock = (
                    zero_time_livelock_evidence_from_progress_callback(
                        progress_callback,
                        remote_dir,
                    )
                )
                if (
                    observed_zero_time_livelock.get("status")
                    == "proven_zero_time_livelock"
                ):
                    zero_time_livelock_evidence = observed_zero_time_livelock
                    if (
                        state == "running"
                        and zero_time_livelock_termination.get("status") != "pass"
                    ):
                        zero_time_livelock_termination = (
                            terminate_remote_on_proven_zero_time_livelock(
                                host=host,
                                port=port,
                                remote_dir=remote_dir,
                                cwd=cwd,
                                label=label,
                                pid=remote_pid if isinstance(remote_pid, int) else None,
                                evidence=observed_zero_time_livelock,
                            )
                        )
            except Exception as exc:
                observer_errors.append(str(exc)[:1000])
            try:
                observed_stall = adaptive_stall_evidence_from_progress_callback(
                    progress_callback,
                    remote_dir,
                )
                if observed_stall.get("status") == "proven_semantic_stall":
                    semantic_stall_evidence = observed_stall
                    if (
                        state == "running"
                        and semantic_stall_termination.get("status") != "pass"
                    ):
                        semantic_stall_termination = (
                            terminate_remote_on_proven_semantic_stall(
                                host=host,
                                port=port,
                                remote_dir=remote_dir,
                                cwd=cwd,
                                label=label,
                                pid=remote_pid if isinstance(remote_pid, int) else None,
                                evidence=observed_stall,
                            )
                        )
            except Exception as exc:
                observer_errors.append(str(exc)[:1000])
        if state == "done":
            remote_returncode = parsed.get("returncode")
            break
        if state in {"lost", "missing", "unknown"}:
            break
        time.sleep(15.0 if remaining is None else min(15.0, max(0.0, remaining)))

    timed_out = not unbounded and remote_returncode is None and state == "running"
    semantic_stall = (
        remote_returncode == SEMANTIC_STALL_EXIT_CODE
        and semantic_stall_evidence.get("status") == "proven_semantic_stall"
    )
    zero_time_livelock = (
        remote_returncode == ZERO_TIME_LIVELOCK_EXIT_CODE
        and zero_time_livelock_evidence.get("status")
        == "proven_zero_time_livelock"
    )

    local_stdout = cwd / f"{safe_id(label)}.remote.stdout.log"
    local_stderr = cwd / f"{safe_id(label)}.remote.stderr.log"
    stdout_download = copy_remote_file(host, port, f"{remote_dir}/{stdout_name}", local_stdout, cwd, 60)
    stderr_download = copy_remote_file(host, port, f"{remote_dir}/{stderr_name}", local_stderr, cwd, 60)
    stdout_tail = local_stdout.read_text(encoding="utf-8", errors="replace")[-12000:] if local_stdout.is_file() else ""
    stderr_tail = local_stderr.read_text(encoding="utf-8", errors="replace")[-12000:] if local_stderr.is_file() else ""
    if remote_returncode is not None:
        status = "pass" if remote_returncode == 0 else "fail"
        failure_class = (
            None
            if remote_returncode == 0
            else "adaptive_semantic_stall"
            if semantic_stall
            else "zero_time_simulation_livelock"
            if zero_time_livelock
            else "remote_tool_failure"
        )
        returncode = remote_returncode
    elif timed_out:
        status = "fail"
        failure_class = "remote_tool_poll_budget_exhausted"
        returncode = 124
    else:
        status = "fail"
        failure_class = "remote_transport_failure"
        returncode = 255
    return {
        "argv": remote_shell(host, port, launch_command),
        "cwd": str(cwd),
        "remote_command": command,
        "remote_workdir": remote_dir,
        "transport": "detached_remote_job_with_short_ssh_polling",
        "launch": launch,
        "remote_stage_cleanup": remote_stage_cleanup,
        "remote_stage_prune": remote_stage_prune,
        "poll_attempts": poll_attempts,
        "poll_transport_failures": transport_failures,
        "poll_tail": poll_records[-8:],
        "remote_state": state,
        "returncode": returncode,
        "status": status,
        "failure_class": failure_class,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "stdout_download": stdout_download,
        "stderr_download": stderr_download,
        "remote_job_preserved": timed_out,
        "duration_sec": time.monotonic() - started,
        "progress_observer_errors": observer_errors[-8:],
        "adaptive_semantic_stall_evidence": semantic_stall_evidence,
        "adaptive_semantic_stall_termination": semantic_stall_termination,
        "zero_time_livelock_evidence": zero_time_livelock_evidence,
        "zero_time_livelock_termination": zero_time_livelock_termination,
        "runner_process_provenance": remote_runner_process_provenance(
            label=label,
            command=command,
            launch_pid=launch_pid,
            exit_code=remote_returncode,
            last_process_snapshot=last_running_process_snapshot,
            reattached=False,
        ),
    }


def run_remote_vcs_semantic_harness(
    run_dir: Path,
    stage_id: str,
    contract: dict[str, Any],
    tool: dict[str, Any],
    timeout_sec: int,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    harness = contract.get("dut_harness", {}) if isinstance(contract.get("dut_harness"), dict) else {}
    source_rows = harness.get("source_files", []) if isinstance(harness.get("source_files"), list) else []
    blockers: list[str] = []
    testbench = checked_path(
        {"path": contract.get("testbench"), "sha256": contract.get("testbench_sha256")},
        "semantic testbench",
        blockers,
    )
    sources = [
        path
        for index, row in enumerate(source_rows)
        if isinstance(row, dict)
        for path in [checked_path(row, f"semantic harness source {index}", blockers)]
        if path is not None
    ]
    input_rows = contract.get("input_vectors", []) if isinstance(contract.get("input_vectors"), list) else []
    inputs = [
        path
        for index, row in enumerate(input_rows)
        if isinstance(row, dict)
        for path in [checked_path(row, f"semantic input vector {index}", blockers)]
        if path is not None
    ]
    weight_row = contract.get("real_weight_stream", {}) if isinstance(contract.get("real_weight_stream"), dict) else {}
    runtime_contract = (
        contract.get("runtime_constant_stream", {})
        if isinstance(contract.get("runtime_constant_stream"), dict)
        else {}
    )
    runtime_row = (
        runtime_contract.get("stream", {})
        if isinstance(runtime_contract.get("stream"), dict)
        else runtime_contract
    )
    weight = checked_path(weight_row, "semantic real-weight stream", blockers) if weight_row else None
    runtime = checked_path(runtime_row, "semantic runtime-constant stream", blockers) if runtime_row else None
    output_capture = Path(str(contract.get("rtl_output_capture") or ""))
    top_module = f"semantic_{safe_id(stage_id).lower()}_tb"
    if not source_rows:
        blockers.append("semantic harness has no source files")
    if len(inputs) != len(input_rows):
        blockers.append("not every semantic input vector passed path/hash validation")
    if not output_capture.name:
        blockers.append("semantic RTL output capture path is missing")
    if blockers:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "simulator": "vcs",
            "stage_id": stage_id,
            "blockers": blockers,
            "summary": "semantic VCS inputs failed closed before remote execution",
        }

    fingerprint, fingerprint_errors = semantic_input_fingerprint(contract, run_dir)
    blockers.extend(fingerprint_errors)
    if progress_callback is not None:
        try:
            setattr(progress_callback, "fingerprint", fingerprint)
        except Exception:
            pass
    compile_defines, memory_init_dependencies, memory_init_errors = semantic_memory_init_payload(
        run_dir,
        sources,
    )
    blockers.extend(memory_init_errors)
    if blockers:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "simulator": "vcs",
            "stage_id": stage_id,
            "blockers": blockers,
            "summary": "semantic VCS fingerprint validation failed closed",
        }
    work_dir = run_dir / "verification" / "operator_leaf_vcs" / safe_id(stage_id)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    staging = work_dir / "staging"
    staging.mkdir(parents=True)

    copied_sources: list[Path] = []
    seen_names: set[str] = set()
    for source in sources:
        if source.name in seen_names:
            blockers.append(f"semantic harness source basename collision: {source.name}")
            continue
        seen_names.add(source.name)
        destination = staging / source.name
        shutil.copy2(source, destination)
        copied_sources.append(destination)
    assert testbench is not None
    shutil.copy2(testbench, staging / "semantic_tb.sv")
    plusargs = []
    for index, source in enumerate(inputs):
        name = f"input_{index}.memh"
        shutil.copy2(source, staging / name)
        plusargs.append(f"+INPUT_{index}_MEMH={name}")
    if weight is not None:
        shutil.copy2(weight, staging / "weight.memh")
        plusargs.append("+WEIGHT_MEMH=weight.memh")
    if runtime is not None:
        shutil.copy2(runtime, staging / "runtime.memh")
        plusargs.append("+RUNTIME_MEMH=runtime.memh")
    plusargs.append("+OUTPUT_MEMH=rtl_output.memh")

    for dependency in memory_init_dependencies:
        destination = staging / str(dependency["remote_relative_path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(str(dependency["path"])), destination)
    if blockers:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "simulator": "vcs",
            "stage_id": stage_id,
            "blockers": blockers,
            "summary": "semantic VCS staging failed closed",
        }

    host = str(tool["host"])
    port = int(tool.get("port") or 22)
    executable = str(tool["executable"])
    tool_env = tool.get("env", {}) if isinstance(tool.get("env"), dict) else {}
    target_arch = str(
        tool_env.get("VCS_TARGET_ARCH")
        or os.environ.get("SPATIALACC_VCS_TARGET_ARCH")
        or "linux64"
    )
    remote_root = os.environ.get(
        "SPATIALACC_REMOTE_SEMANTIC_ROOT",
        f"{persistent_remote_artifact_root(host)}/semantic_vcs",
    )
    remote_stage_root = f"{remote_root}/{safe_id(run_dir.name)}/{safe_id(stage_id)}"
    vcs_home = str(Path(executable).parent.parent)
    source_names = [path.name for path in copied_sources]
    compile_jobs = semantic_vcs_compile_jobs()
    compile_command = " ".join(
        [
            "set -euo pipefail;",
            "export LANG=C LC_ALL=C;",
            f"export VCS_HOME={shlex.quote(vcs_home)};",
            f"export VCS_TARGET_ARCH={shlex.quote(target_arch)};",
            f"export PATH={shlex.quote(str(Path(executable).parent))}:/usr/bin:/bin:$PATH;",
            shlex.quote(executable),
            "-full64 -sverilog -timescale=1ns/1ps",
            *(shlex.quote(value) for value in semantic_vcs_parallel_compile_args()),
            *(shlex.quote(value) for value in semantic_vcs_compile_define_args(compile_defines)),
            f"-top {shlex.quote(top_module)} -o simv",
            *(shlex.quote(name) for name in source_names),
            "semantic_tb.sv -l vcs.log",
        ]
    )
    simulate_command = " ".join(
        [
            "set -euo pipefail;",
            "export LANG=C LC_ALL=C;",
            f"export VCS_HOME={shlex.quote(vcs_home)};",
            f"export VCS_TARGET_ARCH={shlex.quote(target_arch)};",
            f"export PATH={shlex.quote(str(Path(executable).parent))}:/usr/bin:/bin:$PATH;",
            "./simv",
            *(shlex.quote(value) for value in plusargs),
            "-l sim.log",
            "2> sim.stderr.log",
        ]
    )
    job_contract, job_payload = semantic_remote_job_contract(
        staging,
        fingerprint=fingerprint,
        stage_id=stage_id,
        top_module=top_module,
        tool_profile={
            "name": tool.get("name"),
            "role": tool.get("role"),
            "scope": tool.get("scope"),
            "host": host,
            "port": port,
            "executable": executable,
            "vcs_target_arch": target_arch,
            "compile_jobs": compile_jobs,
        },
        compile_defines=compile_defines,
        source_names=source_names,
        plusargs=plusargs,
    )
    job_contract_path = staging / REMOTE_SEMANTIC_JOB_CONTRACT
    job_contract_path.write_text(
        json.dumps(job_contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fresh_execution_required = force_fresh_remote_vcs()
    recovered = (
        None
        if fresh_execution_required
        else recover_exact_remote_semantic_job(
            host,
            port,
            remote_stage_root,
            fingerprint,
            work_dir,
            job_contract_path,
            job_payload,
            timeout_sec,
            simulate_command,
            progress_callback,
        )
    )
    require_remote_reuse = os.environ.get("SPATIALACC_REQUIRE_REMOTE_SEMANTIC_REUSE", "0") == "1"
    if recovered is not None and recovered.get("recovery_state") == "indeterminate":
        recovery_summary = str(
            recovered.get("summary")
            or "remote semantic recovery was indeterminate"
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "failure_class": "remote_semantic_recovery_indeterminate",
            "simulator": "vcs",
            "tool_scope": "remote",
            "stage_id": stage_id,
            "top_module": top_module,
            "input_fingerprint_sha256": fingerprint,
            "remote_stage_root": remote_stage_root,
            "remote_workdir": recovered.get("remote_dir"),
            "remote_stage_cleanup": {
                "status": "not_run",
                "summary": "skipped because remote recovery state is indeterminate",
            },
            "remote_job_reuse": recovered,
            "setup": {
                "status": "not_run",
                "summary": "fresh remote setup is prohibited while recovery is indeterminate",
            },
            "upload": {
                "status": "not_run",
                "summary": "fresh upload is prohibited while recovery is indeterminate",
            },
            "compile": {
                "status": "not_run",
                "summary": "fresh VCS compile is prohibited while recovery is indeterminate",
            },
            "run": {
                "status": "not_run",
                "summary": "fresh VCS simulation is prohibited while recovery is indeterminate",
            },
            "blockers": [recovery_summary],
            "summary": recovery_summary,
        }
    if recovered is None and require_remote_reuse and not fresh_execution_required:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "failure_class": "required_remote_semantic_reuse_not_found",
            "simulator": "vcs",
            "stage_id": stage_id,
            "input_fingerprint_sha256": fingerprint,
            "remote_stage_root": remote_stage_root,
            "blockers": [
                "no exact completed or running remote semantic job matched the current full payload; fresh execution was prohibited"
            ],
            "summary": "required exact remote semantic job reuse was not available",
        }
    if recovered is not None:
        remote_dir = str(recovered["remote_dir"])
        remote_stage_cleanup = {
            "status": "not_run",
            "summary": "skipped because an exact-fingerprint detached remote job was recovered",
        }
        setup = {
            "status": "not_run",
            "summary": "reused existing exact-fingerprint remote directory",
        }
        upload = {
            "status": "not_run",
            "summary": "full remote payload identity matched; upload was not repeated",
        }
        compile_result = recovered["compile"]
        simulate_result = recovered["simulate"]
        remote_job_reuse = {
            "status": "pass",
            "real_tool_was_not_relaunched": True,
            "remote_workdir": remote_dir,
            **dict(recovered.get("identity") or {}),
        }
    else:
        run_tag = f"{fingerprint[:12]}_{int(time.time())}"
        remote_dir = f"{remote_stage_root}/{run_tag}"
        remote_stage_cleanup = command_result(
            remote_shell(host, port, remote_stage_cleanup_command(remote_stage_root)),
            work_dir,
            timeout_sec,
        )
        setup = (
            command_result(
                remote_shell(host, port, f"mkdir -p {shlex.quote(remote_dir)}"),
                work_dir,
                timeout_sec,
            )
            if remote_stage_cleanup.get("status") == "pass"
            else {"status": "not_run", "summary": "remote stage single-instance cleanup failed"}
        )
        upload = (
            command_result(
                ["scp", *scp_options(port), "-r", f"{staging}/.", f"{host}:{remote_dir}/"],
                work_dir,
                timeout_sec,
            )
            if setup.get("status") == "pass"
            else {"status": "not_run", "summary": "remote setup failed"}
        )
        compile_result = (
            run_remote_background_command(
                host,
                port,
                compile_command,
                remote_dir,
                work_dir,
                timeout_sec,
                "vcs_compile",
            )
            if upload.get("status") == "pass"
            else {"status": "not_run", "summary": "remote upload failed"}
        )
        simulate_result = (
            run_remote_background_command(
                host,
                port,
                simulate_command,
                remote_dir,
                work_dir,
                timeout_sec,
                "vcs_simulate",
                progress_callback,
            )
            if compile_result.get("status") == "pass"
            else {"status": "not_run", "summary": "remote VCS compile failed"}
        )
        remote_job_reuse = {
            "status": "not_run",
            "real_tool_was_not_relaunched": False,
            "summary": (
                "fresh remote VCS execution was required for this targeted replay"
                if fresh_execution_required
                else "no exact completed or running remote job matched the current full payload"
            ),
        }

    downloads: dict[str, Any] = {}
    for name in ("vcs.log", "sim.log", "sim.stderr.log"):
        downloads[name] = copy_remote_file(
            host,
            port,
            f"{remote_dir}/{name}",
            work_dir / name,
            work_dir,
            timeout_sec,
        )
    if simulate_result.get("status") == "pass":
        output_capture.parent.mkdir(parents=True, exist_ok=True)
        downloads["rtl_output.memh"] = copy_remote_file(
            host,
            port,
            f"{remote_dir}/rtl_output.memh",
            output_capture,
            work_dir,
            timeout_sec,
        )

    semantic_passed = (
        compile_result.get("status") == "pass"
        and simulate_result.get("status") == "pass"
        and downloads.get("sim.stderr.log", {}).get("status") == "pass"
        and downloads.get("rtl_output.memh", {}).get("status") == "pass"
        and output_capture.is_file()
    )
    required_evidence_paths = [work_dir / "vcs.log"]
    if simulate_result.get("status") != "not_run":
        required_evidence_paths.extend(
            [work_dir / "sim.log", work_dir / "sim.stderr.log"]
        )
    if semantic_passed:
        required_evidence_paths.append(output_capture)
    persistence = persist_remote_artifact_receipt(
        host=host,
        port=port,
        run_dir=run_dir,
        namespace=f"semantic_vcs_{safe_id(stage_id)}",
        remote_stage_root=remote_stage_root,
        remote_dir=remote_dir,
        fingerprint=fingerprint,
        job_contract_path=job_contract_path,
        evidence_paths=[
            work_dir / "vcs.log",
            work_dir / "sim.log",
            work_dir / "sim.stderr.log",
            output_capture,
        ],
        required_evidence_paths=required_evidence_paths,
        source_identity_paths=[
            *sources,
            testbench,
            *inputs,
            *([weight] if weight is not None else []),
            *([runtime] if runtime is not None else []),
        ],
        # A future recovery must not depend on retention of a remote workdir to
        # prove whether a generated compile-unit removed from a file list was
        # reachable.  Inputs and weight streams remain content-addressed by the
        # job contract; source/testbench bytes are retained locally for closure
        # reconstruction.
        snapshot_source_paths=[*sources, testbench],
        timeout_sec=timeout_sec,
    )
    passed = semantic_passed and persistence.get("status") == "pass"
    failure_class = None
    if not passed:
        execution_failures = [
            str(row.get("failure_class") or "")
            for row in (compile_result, simulate_result)
            if isinstance(row, dict) and row.get("status") == "fail"
        ]
        failure_class = (
            "remote_artifact_persistence_failure"
            if semantic_passed and persistence.get("status") != "pass"
            else next(
                (
                    value
                    for value in execution_failures
                    if value
                    in {
                        "remote_transport_failure",
                        "remote_tool_poll_budget_exhausted",
                    }
                ),
                "remote_tool_failure",
            )
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if passed else "fail",
        "summary": (
            "remote VCS semantic harness executed with hash-bound real inputs"
            if passed
            else (
                "remote VCS semantic evidence was not durably acknowledged"
                if failure_class == "remote_artifact_persistence_failure"
                else
                "remote VCS transport failed before a hardware verdict was available"
                if failure_class == "remote_transport_failure"
                else "remote VCS semantic harness failed"
            )
        ),
        "failure_class": failure_class,
        "simulator": "vcs",
        "tool_scope": "remote",
        "stage_id": stage_id,
        "top_module": top_module,
        "tool_profile": {
            "name": tool.get("name"),
            "role": tool.get("role"),
            "scope": tool.get("scope"),
            "host": host,
            "port": port,
            "executable": executable,
            "vcs_target_arch": target_arch,
            "compile_jobs": compile_jobs,
            "compile_defines": compile_defines,
        },
        "input_fingerprint_sha256": fingerprint,
        "fresh_remote_vcs_execution_required": fresh_execution_required,
        "python_environment_contract": {
            "group": os.environ.get("SPATIALACC_PYTHON_ENVIRONMENT_GROUP"),
            "fingerprint_sha256": os.environ.get("SPATIALACC_PYTHON_ENVIRONMENT_FINGERPRINT"),
        },
        "memory_initialization": {
            "schema_version": "spatialaccagent.semantic_memory_initialization.v1",
            "compile_defines": compile_defines,
            "dependencies": memory_init_dependencies,
        },
        "source_files": [str(path) for path in sources],
        "testbench": str(testbench),
        "remote_workdir": remote_dir,
        "remote_artifact_persistence": persistence,
        "local_workdir": str(work_dir),
        "remote_stage_cleanup": remote_stage_cleanup,
        "remote_job_reuse": remote_job_reuse,
        "setup": setup,
        "upload": upload,
        "compile": compile_result,
        "run": simulate_result,
        "downloads": downloads,
        "vcs_log": str(work_dir / "vcs.log"),
        "sim_log": str(work_dir / "sim.log"),
        "sim_stderr_log": str(work_dir / "sim.stderr.log"),
        "output_capture": str(output_capture),
        "rtl_output_sha256": sha256_file(output_capture) if passed else None,
        "blockers": blockers,
    }


def run_configured_semantic_harness(
    run_dir: Path,
    stage_id: str,
    contract: dict[str, Any],
    timeout_sec: int,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    tool, errors = configured_vcs(run_dir)
    if errors:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "stage_id": stage_id,
            "summary": "no configured production semantic simulator is available",
            "blockers": errors,
        }
    if tool.get("scope") != "remote":
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "stage_id": stage_id,
            "summary": "current semantic simulator runner requires the configured remote VCS profile",
            "blockers": [f"unsupported configured VCS scope: {tool.get('scope')}"],
        }
    recovered = (
        None
        if force_fresh_remote_vcs()
        else recover_archived_semantic_execution(
            run_dir,
            stage_id,
            contract,
            timeout_sec,
        )
    )
    if recovered is not None:
        return recovered
    return run_remote_vcs_semantic_harness(
        run_dir,
        stage_id,
        contract,
        tool,
        timeout_sec,
        progress_callback,
    )
