"""LLM implementation loop for a shared, explicitly requested architecture change.

The LLM owns hardware and generator edits. This runner only bounds file edits,
preserves the previous sources, and returns actual compiler/VCS feedback.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from accagent.framework.stage_llm import run_stage_agent
from accagent.framework.sacg_utils import write_json


ROOT = Path(__file__).resolve().parents[2]
SHARED_HANDOFF_STATUSES = {"leaf_regression_pass", "leaf_compile_pass", "shared_leaf_handoff"}
SCHEMA = {
    "type": "object",
    "properties": {
        "agent": {"type": "string"},
        "status": {"type": "string", "enum": ["ready_to_apply", "needs_context", "blocked"]},
        "summary": {"type": "string"},
        "implementation_complete": {"type": "boolean"},
        "pending_work": {"type": "array", "items": {"type": "string"}},
        "file_edits": {"type": "array", "items": {
            "type": "object", "properties": {
                "path": {"type": "string"}, "old_text": {"type": "string"},
                "new_text": {"type": "string"},
            }, "required": ["path", "old_text", "new_text"],
        }},
        "context_requests": {"type": "array", "items": {"type": "string"}},
        "blocked_reasons": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["agent", "status", "summary", "implementation_complete", "pending_work",
                 "file_edits", "context_requests", "blocked_reasons"],
}


def initial_sources() -> list[Path]:
    return [
        *sorted((ROOT / "accagent/framework/templates/operator_chisel").glob("*.scala")),
        ROOT / "accagent/framework/templates/operator_chisel/template_metadata.json",
        ROOT / "accagent/framework/stage_artifacts.py",
        ROOT / "accagent/framework/stage_params.py",
        ROOT / "accagent/framework/dse_estimator.py",
        ROOT / "scripts/synthesis/compute_slot_adapter_generator.py",
        ROOT / "tests/fixtures/linear_pipeline/src/main/scala/GenerateLinearPipeline.scala",
        ROOT / "tests/fixtures/linear_pipeline/prepare.py",
        ROOT / "tests/fixtures/linear_pipeline/run_vcs.sh",
        ROOT / "tests/fixtures/linear_pipeline/build.sbt",
        ROOT / "accagent/framework/stage_pipeline.py",
        ROOT / "accagent/framework/stage_backend.py",
        ROOT / "accagent/framework/stage_verification.py",
        ROOT / "accagent/framework/stage_input.py",
        ROOT / "accagent/framework/weight_layout.py",
        ROOT / "accagent/framework/board_weight_image.py",
        ROOT / "accagent/framework/case_adapter.py",
        ROOT / "scripts/synthesis/board_shell_wrapper_generator.py",
        ROOT / "scripts/synthesis/case_app_shell_vivado.py",
        ROOT / "scripts/synthesis/app_shell_runtime_vivado.py",
        ROOT / "scripts/verification/case_tb_generator.py",
        ROOT / "scripts/verification/case_board_vcs_functional.py",
        ROOT / "accagent/diagnostics/ddr_alignment_20261017/ddr_tile_service_contract.json",
        ROOT / "accagent/diagnostics/ddr_alignment_20261017/board_scheduler_contract.json",
        ROOT / "verification/rtl/cnn_core.sv",
    ]


def compiled_port_width_coverage(rtl: Path, requirements: dict) -> dict:
    """Check requested interface variants in actual elaborated fixture RTL."""
    from scripts.synthesis.compute_slot_adapter_generator import _module_port_widths

    observed = {name: set() for name in requirements}
    for source in rtl.rglob("*.sv"):
        ports = _module_port_widths(source.read_text(errors="replace"))
        for name in observed:
            if name in ports:
                observed[name].add(ports[name])
    missing = {name: sorted(set(widths) - observed[name])
               for name, widths in requirements.items() if set(widths) - observed[name]}
    return {"returncode": 1 if missing else 0,
            "required_compiled_port_widths": requirements,
            "observed_compiled_port_widths": {k: sorted(v) for k, v in observed.items()},
            "missing_compiled_port_widths": missing}



def compiled_case_coverage(rtl: Path, requirements: dict, integer_cases: list[str]) -> list[dict]:
    """Bind interface and backend evidence to the requested case itself."""
    from accagent.framework.fpga_ip_contract import discover_fp_modules

    checks = [dict(compiled_port_width_coverage(rtl / case, widths), case=case)
              for case, widths in requirements.items()]
    for case in integer_cases:
        root = rtl / case
        modules = discover_fp_modules(root)
        checks.append({"returncode": 1 if not root.is_dir() or modules else 0,
                       "case": case, "floating_point_modules": modules,
                       "requirement": "Integer case must exist and use no floating-point IP"})
    return checks


def editable(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return (
        rel.startswith("accagent/framework/templates/operator_chisel/")
        or rel.startswith("tests/fixtures/linear_pipeline/") and path.suffix in {".py", ".scala"}
        or rel == "tests/fixtures/linear_pipeline/run_vcs.sh"
        or rel in {
            "accagent/framework/stage_artifacts.py", "accagent/framework/stage_params.py",
            "accagent/framework/dse_estimator.py", "accagent/framework/stage_pipeline.py",
            "accagent/framework/stage_backend.py", "accagent/framework/weight_layout.py",
            "accagent/framework/board_weight_image.py", "accagent/framework/board_memory_runtime.py",
            "accagent/framework/stage_input.py", "accagent/framework/stage_templates.py",
            "accagent/framework/fpga_ip_contract.py", "accagent/framework/fpga_ip_runtime.py",
            "accagent/framework/fpga_ip_vcs_plan.py",
            "accagent/framework/case_adapter.py",
            "scripts/synthesis/compute_slot_adapter_generator.py",
            "scripts/synthesis/board_shell_wrapper_generator.py",
            "scripts/synthesis/case_app_shell_vivado.py",
            "scripts/synthesis/app_shell_runtime_vivado.py",
            "scripts/verification/semantic_testbench_generator.py",
            "scripts/verification/case_single_layer_stream_sim.py",
            "scripts/verification/case_board_vcs_functional.py",
            "scripts/verification/case_tb_generator.py",
        }
    )


def repository_edit_path(name: str) -> Path:
    """Ground a repository source path even when it names the remote checkout."""

    raw = Path(name)
    path = (ROOT / raw).resolve()
    if path.is_relative_to(ROOT):
        return path
    if raw.is_absolute() and ".." not in raw.parts:
        for index in range(len(raw.parts)):
            candidate = ROOT.joinpath(*raw.parts[index:]).resolve()
            if candidate.is_relative_to(ROOT) and editable(candidate):
                return candidate
    raise ValueError(f"edit outside architecture implementation scope: {name}")


def align_edit_indentation(before: str, old: str, new: str) -> tuple[str, str]:
    """Allow a uniform indentation difference only when the content is unique."""

    lines = old.splitlines(keepends=True)
    first = next((line for line in lines if line.strip()), "")
    if not first:
        return old, new
    prefix = re.match(r"[ \t]*", first).group(0)
    if any(line.strip() and not line.startswith(prefix)
           for line in lines + new.splitlines(keepends=True)):
        return old, new
    matches = set()
    pattern = r"(?m)^([ \t]*)" + re.escape(first[len(prefix):].rstrip("\r\n")) + r"(?:\r?\n|$)"
    for indent in re.findall(pattern, before):
        def shifted(text: str) -> str:
            return "".join(indent + line[len(prefix):] if line.strip() else line
                           for line in text.splitlines(keepends=True))
        candidate = shifted(old), shifted(new)
        if before.count(candidate[0]) == 1:
            matches.add(candidate)
    return next(iter(matches)) if len(matches) == 1 else (old, new)


def apply_edits(edits: list[dict], backup: Path, oracle_fragments: list[str] | None = None,
                expected_sources: dict[str, str] | None = None,
                rejected_edits: list[dict] | None = None) -> list[str]:
    candidates: dict[Path, set[str]] = {}
    for edit_index, edit in enumerate(edits, start=1):
        path = repository_edit_path(edit["path"])
        if not path.is_relative_to(ROOT) or not editable(path):
            raise ValueError(f"edit outside architecture implementation scope: {edit['path']}")
        befores = candidates.get(path, {path.read_text() if path.is_file() else ""})
        old, new = edit["old_text"], edit["new_text"]
        afters = set()
        already_applied = set()
        for before in befores:
            if old:
                matched_old, matched_new = old, new
                if before.count(old) == 0:
                    matched_old, matched_new = align_edit_indentation(before, old, new)
                # A compact retry can resend an edit whose replacement was
                # already applied by an earlier iteration. Treat that exact
                # state as an idempotent no-op, but keep rejecting a genuinely
                # missing anchor so stale patches cannot mutate nearby code.
                if before.count(matched_old) == 0 and new and before.count(new) > 0:
                    already_applied.add(before)
                    continue
                for match in re.finditer(re.escape(matched_old), before):
                    afters.add(before[:match.start()] + matched_new + before[match.end():])
            else:
                if before:
                    expected = (expected_sources or {}).get(str(path.relative_to(ROOT)))
                    if expected is None or path.read_text() != expected:
                        raise ValueError(f"full-file replacement requires the unchanged supplied source: {edit['path']}")
                afters.add(new)
        # Prefer a real application over an idempotent retry on another
        # candidate. Otherwise an earlier ambiguous match survives even when
        # a later exact anchor disambiguates the authored patch.
        if not afters:
            afters = already_applied
        if not afters or len(afters) > 64:
            error = (
                f"old_text has no bounded exact application: {edit['path']} "
                f"(edit {edit_index}, anchor={old[:240]!r})"
            )
            if rejected_edits is not None and not afters:
                rejected_edits.append({"path": edit["path"], "error": error})
                continue
            raise ValueError(error)
        candidates[path] = afters
    # Repeated anchors may be disambiguated by later, more specific edits.
    # Apply only when the entire authored patch has one exact final result.
    if any(len(values) != 1 for values in candidates.values()):
        raise ValueError("source patch has multiple distinct exact results; supply more context")
    staged = {path: next(iter(values)) for path, values in candidates.items()}
    vcs_driver = ROOT / "tests/fixtures/linear_pipeline/run_vcs.sh"
    if vcs_driver in staged:
        driver = staged[vcs_driver]
        required_markers = ("vcs -full64", "SPATIALACC_COMPILE_ONLY", "timeout 120 ./simv", "grep '^PASS ' simulation.log")
        if any(marker not in driver for marker in required_markers) or "simulation not invoked" in driver:
            raise ValueError("VCS compile gate must preserve the default simulation path and explicit compile-only branch")
    oracle_path = ROOT / "tests/fixtures/linear_pipeline/prepare.py"
    if oracle_path in staged:
        for fragment in oracle_fragments or []:
            if fragment not in staged[oracle_path]:
                raise ValueError("Regression edit changes the immutable numerical oracle, token workload or output assertions")
    for path, source in staged.items():
        saved = backup / path.relative_to(ROOT)
        if path.is_file() and not saved.exists():
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, saved)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    return [str(path.relative_to(ROOT)) for path in staged]


def execute(argv: list[str], cwd: Path, log: Path, timeout: int = 1800) -> dict:
    print("[architecture tool] " + " ".join(argv), flush=True)
    env = os.environ.copy()
    env["JDK_JAVA_OPTIONS"] = "-Xmx1800m -XX:ActiveProcessorCount=2"
    with log.open("w") as output:
        try:
            code = subprocess.run(argv, cwd=cwd, env=env, stdout=output,
                                  stderr=subprocess.STDOUT, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            code = 124
    text = log.read_text(errors="replace")
    return {"argv": argv, "returncode": code, "log": str(log), "output_tail": text[-24000:]}


def apply_incremental_edits(edits: list[dict], backup: Path, oracle_fragments: list[str],
                            expected_sources: dict[str, str] | None = None) -> tuple[list[str], list[dict]]:
    grouped: dict[Path, list[dict]] = {}
    changed, rejected = [], []
    for edit in edits:
        try:
            grouped.setdefault(repository_edit_path(edit["path"]), []).append(edit)
        except (OSError, ValueError, KeyError) as exc:
            rejected.append({"path": edit.get("path"), "error": str(exc)})
    for path, file_edits in grouped.items():
        file_rejected = []
        try:
            changed.extend(apply_edits(
                file_edits, backup, oracle_fragments, expected_sources,
                rejected_edits=file_rejected,
            ))
            rejected.extend(file_rejected)
        except (OSError, ValueError, KeyError) as exc:
            if len(file_edits) == 1:
                rejected.append({"path": str(path.relative_to(ROOT)), "error": str(exc)})
                continue
            # Keep independent exact edits even if another edit in the file
            # remains ambiguous. Individual application still rejects every
            # non-unique anchor and preserves the oracle/snapshot checks.
            for index, edit in enumerate(file_edits, start=1):
                try:
                    changed.extend(apply_edits([edit], backup, oracle_fragments, expected_sources))
                except (OSError, ValueError, KeyError) as error:
                    rejected.append({"path": str(path.relative_to(ROOT)),
                                     "edit_index": index, "error": str(error)})
    return list(dict.fromkeys(changed)), rejected


def validate_python_sources(changed: list[str], request: dict, attempt: Path) -> list[dict]:
    """Return executable Python feedback before spending time on RTL compilation."""

    checks = []
    python_sources = [name for name in changed if Path(name).suffix == ".py"]
    if python_sources:
        checks.append(execute(["python3", "-m", "py_compile", *python_sources],
                              ROOT, attempt / "python_compile.log"))
    modules = request.get("focused_test_modules", [])
    if modules and all(check["returncode"] == 0 for check in checks):
        checks.append(execute(["python3", "-m", "unittest", *modules, "-q"],
                              ROOT, attempt / "focused_tests.log"))
    return checks


def implement(args: argparse.Namespace) -> None:
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    request = json.loads(args.request.read_text())
    requested_sources = request.get("implementation_source_files")
    if requested_sources is None:
        sources = initial_sources()
    else:
        if not isinstance(requested_sources, list) or not requested_sources:
            raise ValueError("implementation_source_files must be a nonempty list")
        sources = []
        for name in requested_sources:
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                raise ValueError(f"implementation source missing or outside repository: {name}")
            if path not in sources:
                sources.append(path)
    for name in request.get("read_only_context_files", []):
        path = (ROOT / name).resolve()
        if path.is_relative_to(ROOT) and path.is_file() and path not in sources:
            sources.append(path)
    # Recover files already requested by this agent from their existing records.
    # Always read current sources, never restore an old source snapshot.
    for validation_path in sorted(out.glob("iteration_*/validation.json")):
        validation = json.loads(validation_path.read_text())
        for item in validation.get("context_request_results", []):
            if item.get("status") != "source_supplied":
                continue
            path = (ROOT / item["requested"]).resolve()
            if path.is_relative_to(ROOT) and path.is_file() and path not in sources:
                sources.append(path)
    source_index = sorted({
        str(p.relative_to(ROOT))
        for directory in [ROOT / "accagent/framework", ROOT / "scripts/synthesis", ROOT / "tests/fixtures/linear_pipeline"]
        for p in directory.rglob("*")
        if p.is_file() and p.suffix in {".py", ".scala", ".sv", ".v", ".sh", ".sbt", ".json"}
        and not any(part in {"target", ".sbt", ".cache", "__pycache__", "node_modules"} for part in p.parts)
    })
    oracle_path = out / "regression_oracle_contract.json"
    if not oracle_path.is_file():
        reference = (ROOT / "tests/fixtures/linear_pipeline/prepare.py").read_text()
        fragments = [
            reference[reference.index("def fp_bits"):reference.index("def prepare")],
            reference[reference.index("    inputs = [["):reference.index("    images = {")],
        ]
        fragments.extend(line for line in reference.splitlines() if (
            "tokens = 36" in line or "if (io_out_bits_" in line or
            "if (received >=" in line or "if (sent !=" in line
        ))
        write_json(oracle_path, {"immutable_fragments": fragments})
    oracle_fragments = json.loads(oracle_path.read_text())["immutable_fragments"]
    feedback: dict = {}
    status_path = out / "implementation_status.json"
    previous = json.loads(status_path.read_text()) if status_path.is_file() else {}
    index = int(previous.get("iteration", 0))
    if previous.get("status") in SHARED_HANDOFF_STATUSES:
        return
    old_feedback = out / f"iteration_{index:04d}" / "validation.json"
    if not old_feedback.is_file():
        completed = [p for p in out.glob("iteration_*/validation.json")
                     if int(p.parent.name.split("_")[-1]) <= index]
        if completed:
            old_feedback = max(completed, key=lambda p: int(p.parent.name.split("_")[-1]))
    if old_feedback.is_file():
        feedback = json.loads(old_feedback.read_text())
    if not feedback and args.validation_feedback:
        feedback = json.loads(args.validation_feedback.read_text())
    last_tool_feedback = feedback
    while True:
        # A running shared repair loop must pick up user constraint updates
        # before constructing the next LLM request or applying its gates.
        request = json.loads(args.request.read_text())
        index += 1
        attempt = out / f"iteration_{index:04d}"
        attempt.mkdir()
        write_json(status_path, {"status": "implementing", "iteration": index, "request": str(args.request)})
        snapshots = {str(p.relative_to(ROOT)): p.read_text() for p in sources if p.is_file()}
        if args.replay_candidate:
            record = json.loads(args.replay_candidate.read_text())
            write_json(attempt / "replayed_candidate.json", {
                "source_result": str(args.replay_candidate), "output": record["output"],
            })
            args.replay_candidate = None
            snapshots = {}
        else:
            external_feedback = (
                json.loads(args.validation_feedback.read_text())
                if args.validation_feedback else {}
            )
            next_priority = external_feedback.get("next_increment_priority") or request.get("next_increment_priority", "")
            record = run_stage_agent(
                agent="shared_architecture_implementation_agent", stage="architecture_implementation",
                task="Complete the explicitly authorized connected accelerator architecture. Execute this current priority first: " + next_priority + " You own all missing kernel/cache/loader/top/generator/board-DDR interfaces. Return a coherent source patch closing the requested boundary, not another isolated refinement of already compile-passing leaf logic. The shared pass must implement and source-validate the generic exact-board generator and ABI; model-specific loader/full-image contracts are created only after handoff by the three model supervisors. Once the shared kernel/cache/loader/top/generator/board-DDR path and DSE bindings are connected and the real Chisel plus remote VCS gates pass, set implementation_complete=true and return pending_work=[]; the supervisor then generates each model's exact adapter from its current contract and runs its connected-top VCS and Vivado gates. Full numerical simulation is waived for this shared pass; real Chisel and remote VCS compile/elaboration/link are required.",
                inputs={"user_architecture_request": request,
                        "current_repair_sources": {
                            name: snapshots[name]
                            for name in dict.fromkeys([
                                *feedback.get("changed_sources", []),
                                *(item.get("path") for item in feedback.get("rejected_edits", [])),
                            ]) if name in snapshots
                        },
                        "source_snapshots": snapshots,
                        "repository_source_index": source_index,
                        "available_real_validation": {
                            "compiler": "sbt --no-server --batch runMain GenerateLinearPipeline <iteration>/rtl",
                            "fixture": "tests/fixtures/linear_pipeline",
                            "testbench_preparation": "python3 tests/fixtures/linear_pipeline/prepare.py <iteration>/rtl",
                            "vcs_runner": "tests/fixtures/linear_pipeline/run_vcs.sh",
                            "remote_host": args.remote_host, "ip_context": args.ip_context,
                            "simlib_setup": args.simlib_setup, "ip_models": args.ip_models,
                            "vcs_home": args.vcs_home,
                            "execution_owner": "Framework executes the real commands immediately after your source edits, then returns compiler and simulator logs. You do not need to run tools inside this JSON response.",
                        },
                        "previous_real_tool_feedback": feedback,
                        "external_validation_feedback": external_feedback,
                        "edit_scope": "Shared operator templates, numeric/backend contracts, code generator, parameter and cost bindings, compute-slot adapter generator, and linear regression driver. Do not waive verification or alter existing numerical oracles. Precision-dependent physical implementation contracts may be extended for explicitly authorized backends, preserving strict checks for each backend."},
                out_dir=attempt, fallback_summary="Architecture implementation requires the configured LLM.",
                output_schema=SCHEMA,
                prompt_rules=[
                    "The user has explicitly authorized DDR backing storage, active/shadow working caches, safe switching and weight prefetch overlapping compute. No extra approval is needed for this architecture implementation.",
                    "Implement actual behavior across the kernel and generator boundaries. Do not merely add metadata, documentation, a contract, unused ports or an unsupported DSE parameter.",
                    "Prefer complete file edits for coordinated interface changes: use empty old_text and provide the entire new_text file. The framework checks the current file against its supplied source snapshot before replacing it, so no hash or anchor matching is needed. Exact unique old_text/new_text edits remain supported. Preserve unrelated behavior and all numeric policies; never omit computations or use ellipses in a complete file.",
                    "Return a concrete incremental source patch even when the complete change is too large for one response. The framework keeps partial edits and returns actual compiler errors for the next repair. Set implementation_complete=true with pending_work=[] only after kernel caches, all generic loader/top interfaces, the exact-board DDR adapter generator/ABI and DSE bindings are connected and the current generated design passes the real Chisel/VCS gates. The supervisor owns model-specific loader contract materialization, connected-top adapter VCS, three-model regeneration and Vivado synthesis after handoff. A runner-only edit is not architecture completion.",
                    "Preserve complete model computations, every weight/input/output, numeric-policy-required arithmetic and physical XPM/DSP or FP resources, ready/valid backpressure and token/operator overlap. An explicitly requested precision change must be implemented throughout the design; never reduce the requested precision further, truncate work or serialize complete sequences to resolve a resource miss.",
                    "The numerical oracle and output/metadata/work-count assertions in prepare.py must remain intact. Adapt its loader and stimulus scheduling for real request-driven DDR service, multiple tiles, changed consecutive-layer weights and active/shadow ownership; do not weaken checks to make a regression pass.",
                    "For this urgent run the user explicitly requires Chisel elaboration and real remote VCS compile/elaboration/link; full simulation is waived. Preserve the default simulation path for later use, but the compile-only gate is accepted. Downstream three-model flow must run real Vivado synthesis and reject designs optimized away or outside resource budgets.",
                    "The bounded cache and loader must work for arbitrary admitted matrix dimensions and numeric policies; no Qwen/GPT/TinyLlama shapes or current sample values may be hard-coded. OPT files are read-only architectural references.",
                    "All files named in source_snapshots and every path previously returned as source_supplied are already complete. Do not request them again or request a path merely to postpone edits; return anchored implementation edits now. Only request a genuinely missing repository file.",
                    "The exact-board scheduler and loader boundary is part of this authorized shared change. If a supplied shared generator/adapter needs edits, edit that shared file with unique anchors; do not leave request ports disconnected.",
                    "The generic DDR tile-service contract is supplied as ddr_tile_service_contract.json and the current adapter/generator sources are in source_snapshots. Do not ask for another prose description of that contract; implement against it and return edits.",
                ],
            )
        output = record["output"]
        context_results = []
        read_only_files = set(request.get("read_only_context_files", []))
        context_requests = []
        for requested in output.get("context_requests", []):
            paths = re.findall(r"(?:accagent|scripts|tests|verification)/[A-Za-z0-9_./-]+", str(requested))
            context_requests.extend(paths or [requested])
        for name in context_requests:
            # Prefer an explicit repository path embedded in a prose request.
            # This prevents a generic word such as "scheduler" from shadowing
            # the actual requested backend source with the DDR contract.
            requested_name = str(name)
            matches = re.findall(r"(?:accagent|scripts|tests|verification)/[A-Za-z0-9_./-]+", requested_name)
            if matches:
                name = matches[-1].rstrip(".,:;`'\")")
            # The implementation owner sometimes describes a missing contract in prose
            # instead of naming a path. The generic DDR transaction contract is already
            # supplied in the request; do not let prose-only requests create an endless
            # context loop.
            if not matches and isinstance(name, str) and any(token in name.lower() for token in ("ddr", "scheduler", "loader_route_contract", "tile request", "tile-request")):
                contract_path = ROOT / "accagent/diagnostics/ddr_alignment_20261017/ddr_tile_service_contract.json"
                if contract_path not in sources:
                    sources.append(contract_path)
                context_results.append({"requested": name, "status": "contract_supplied", "source": str(contract_path.relative_to(ROOT))})
                continue
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT):
                context_results.append({"requested": name, "status": "outside_repository"})
                continue
            if path.is_dir():
                context_results.append({"requested": name, "status": "directory_index_provided",
                                        "files": [value for value in source_index if value.startswith(name.rstrip("/") + "/")]})
            elif (path.is_file() and path.suffix in {".py", ".scala", ".sv", ".v", ".json", ".md", ".sh", ".sbt"}
                  and (not path.is_relative_to(ROOT / "accagent/runs") or name in read_only_files)):
                if path not in sources:
                    sources.append(path)
                context_results.append({"requested": name, "status": "source_supplied"})
            else:
                context_results.append({"requested": name, "status": "not_available", "use_repository_source_index": True})
        if not output.get("file_edits"):
            # A completed shared handoff may legitimately contain no new source
            # edits.  The previous iteration already ran the real compiler gates;
            # do not turn that handoff into an endless empty repair loop.
            prior_record = last_tool_feedback if isinstance(last_tool_feedback, dict) else {}
            prior_checks = prior_record.get("checks", []) or (
                prior_record.get("last_real_tool_feedback", {}).get("checks", [])
                if isinstance(prior_record.get("last_real_tool_feedback", {}), dict) else []
            )
            prior_compile_pass = bool(prior_checks) and all(
                check.get("returncode") == 0
                for check in prior_checks
                if check.get("error") != "Compiler gate passed but requested architecture is incomplete"
            ) and not any(
                check.get("returncode") not in (0, None)
                and check.get("error") != "Compiler gate passed but requested architecture is incomplete"
                for check in prior_checks
            )
            current_source_gate = (
                all(token in (ROOT / "scripts/synthesis/compute_slot_adapter_generator.py").read_text()
                    for token in ("exact_board_ddr_tile_service", "io_ddrTileRequest_valid", "c0_ddr4_s_axi_rready"))
                and "materialized_refill_rate_bits_per_cycle" in
                (ROOT / "accagent/framework/dse_estimator.py").read_text()
            )
            if (output.get("implementation_complete") is True
                    and not output.get("pending_work")
                    and prior_compile_pass and current_source_gate):
                focused_checks = validate_python_sources([], request, attempt)
                if any(check["returncode"] != 0 for check in focused_checks):
                    feedback = {"status": "fail", "checks": focused_checks,
                                "last_real_tool_feedback": last_tool_feedback}
                    write_json(attempt / "validation.json", feedback)
                    continue
                write_json(attempt / "validation.json", {
                    "status": "pass", "changed_sources": [], "rejected_edits": [],
                    "checks": focused_checks,
                    "implementation_plan": {"summary": output.get("summary", ""), "pending_work": []},
                    "context_request_results": context_results,
                    "handoff": "completed_without_new_edits",
                    "prior_real_tool_feedback": last_tool_feedback,
                })
                write_json(status_path, {
                    "status": "shared_leaf_handoff" if request.get("shared_validation_scope") == "leaf_handoff_then_per_model_full_top" else "leaf_compile_pass",
                    "iteration": index,
                    "validation": str(attempt / "validation.json"),
                    "remaining": "Each model run must compile/elaborate its generated complete top and validate its exact-board adapter/connected-top VCS before synthesis or completion.",
                })
                return
            if output.get("status") != "ready_to_apply" or context_results:
                feedback = {"status": "implementation_required", "agent_report": output,
                            "last_real_tool_feedback": last_tool_feedback,
                            "context_request_results": context_results,
                            "reason": "Resolve the requested implementation context before validating current sources."}
                write_json(attempt / "validation.json", feedback)
                continue
            # A repair may already be present in current sources. Run its
            # requested validation rather than forcing a dummy source patch.
        changed, rejected = apply_incremental_edits(output["file_edits"], out / "original_sources", oracle_fragments, snapshots)
        if not changed and (output.get("file_edits") or rejected):
            feedback = {
                "status": "edit_rejected", "rejected_edits": rejected,
                "last_real_tool_feedback": last_tool_feedback,
                "implementation_plan": {
                    "summary": output.get("summary", ""),
                    "pending_work": output.get("pending_work", []),
                },
                "rejected_file_sources": {
                    name: (ROOT / name).read_text()
                    for item in rejected
                    if (name := item.get("path")) in snapshots
                },
                "context_request_results": context_results,
            }
            write_json(attempt / "validation.json", feedback)
            continue
        for name in changed:
            path = ROOT / name
            if path not in sources:
                sources.append(path)
        fixture = ROOT / "tests/fixtures/linear_pipeline"
        rtl = attempt / "rtl"
        checks = validate_python_sources(changed, request, attempt)
        if all(c["returncode"] == 0 for c in checks):
            checks.append(execute(["sbt", "--no-server", "--batch", "--supershell=false",
                                   f"runMain GenerateLinearPipeline {rtl}"], fixture, attempt / "elaboration.log"))
        if all(c["returncode"] == 0 for c in checks):
            checks.append(execute(["python3", str(fixture / "prepare.py"), str(rtl)], ROOT, attempt / "prepare.log"))
        cases = {p.parent.name for p in rtl.glob("*/params.json")}
        if all(c["returncode"] == 0 for c in checks) and request.get("required_compiled_port_widths"):
            checks.append(compiled_port_width_coverage(rtl, request["required_compiled_port_widths"]))
        if all(c["returncode"] == 0 for c in checks):
            checks.extend(compiled_case_coverage(
                rtl, request.get("required_compiled_port_widths_by_case", {}),
                request.get("required_integer_cases", [])))
        required_cases = set(request.get("required_regression_cases", []))
        if all(c["returncode"] == 0 for c in checks) and (not cases or not required_cases.issubset(cases)):
            checks.append({"returncode": 1, "error": "Regression generator omitted required workloads",
                           "required_cases": sorted(required_cases), "actual_cases": sorted(cases)})
        if all(c["returncode"] == 0 for c in checks):
            remote = args.remote_dir.rstrip("/") + f"/iteration_{index:04d}"
            checks.append(execute(["ssh", args.remote_host, "mkdir", "-p", remote], ROOT, attempt / "remote_mkdir.log"))
            checks.append(execute(["rsync", "-a", str(rtl) + "/", f"{args.remote_host}:{remote}/rtl/"], ROOT, attempt / "sync.log"))
            checks.append(execute(["rsync", "-a", str(fixture / "run_vcs.sh"), f"{args.remote_host}:{remote}/"], ROOT, attempt / "sync_driver.log"))
            if all(c["returncode"] == 0 for c in checks):
                import shlex
                environment = ["SPATIALACC_COMPILE_ONLY=1"]
                if args.vcs_home:
                    environment.append("SPATIALACC_VCS_HOME=" + args.vcs_home)
                command = " ".join(shlex.quote(x) for x in ["env", *environment, "bash", remote + "/run_vcs.sh", args.ip_context,
                                    remote + "/rtl", args.simlib_setup, args.ip_models])
                checks.append(execute(["ssh", args.remote_host, command], ROOT, attempt / "vcs.log"))
                checks.append(execute(["rsync", "-a", "--prune-empty-dirs", "--include=*/",
                                       "--include=*.log", "--exclude=*",
                                       f"{args.remote_host}:{remote}/rtl/", str(rtl) + "/"],
                                      ROOT, attempt / "collect.log"))
        if all(c["returncode"] == 0 for c in checks):
            for case in sorted(cases):
                log = rtl / case / "simulation.log"
                if not log.is_file() or not any(line.startswith("PASS ") for line in log.read_text(errors="replace").splitlines()):
                    checks.append({"returncode": 1, "error": f"No VCS compile/elaboration/link PASS for {case}"})
        template_backup = out / "original_sources/accagent/framework/templates/operator_chisel"
        template_changed = any(
            (ROOT / saved.relative_to(out / "original_sources")).read_text() != saved.read_text()
            for saved in template_backup.glob("*.scala")
        )
        source_gate = {
            "generator_exact_board_service": all(token in (ROOT / "scripts/synthesis/compute_slot_adapter_generator.py").read_text()
                                                 for token in ("exact_board_ddr_tile_service", "io_ddrTileRequest_valid",
                                                               "c0_ddr4_s_axi_rready")),
            "dse_materialized_rate_binding": "materialized_refill_rate_bits_per_cycle" in
            (ROOT / "accagent/framework/dse_estimator.py").read_text(),
        }
        shared_handoff = request.get("shared_validation_scope") == "leaf_handoff_then_per_model_full_top"
        if (shared_handoff and all(c.get("returncode") == 0 for c in checks)
                and all(source_gate.values()) and template_changed and not rejected
                and (not request.get("require_shared_implementation_complete")
                     or (output.get("implementation_complete") is True
                         and not output.get("pending_work")))):
            feedback = {"status": "pass", "changed_sources": changed, "rejected_edits": [],
                        "checks": checks, "source_gate": source_gate,
                        "implementation_plan": {"summary": output.get("summary", ""),
                                                "pending_work": output.get("pending_work", [])},
                        "handoff": "shared_leaf_gate_passed_per_model_full_top_required",
                        "context_request_results": context_results}
            write_json(attempt / "validation.json", feedback)
            write_json(status_path, {
                "status": "shared_leaf_handoff", "iteration": index,
                "validation": str(attempt / "validation.json"),
                "leaf_gate": "512-bit compiled interface and all required remote VCS compile/elaboration/link cases passed",
                "remaining": "Run each model's generated complete-top Chisel compile/elaboration and exact-board adapter/connected-top VCS. This handoff does not claim those gates passed.",
            })
            return
        if all(c["returncode"] == 0 for c in checks) and not all(source_gate.values()):
            checks.append({"returncode": 1, "error": "Generic exact-board source gate is incomplete",
                           "source_gate": source_gate})
        if all(c["returncode"] == 0 for c in checks) and (
            not output.get("implementation_complete") or output.get("pending_work") or not template_changed
        ):
            checks.append({"returncode": 1, "error": "Compiler gate passed but requested architecture is incomplete",
                           "pending_work": output.get("pending_work", []), "operator_template_changed": template_changed})
        if rejected:
            checks.append({"returncode": 1, "error": "Some source edits require repair", "rejected_edits": rejected})
        feedback = {"status": "pass" if all(c["returncode"] == 0 for c in checks) else "fail",
                    "changed_sources": changed, "rejected_edits": rejected, "checks": checks,
                    "implementation_plan": {"summary": output.get("summary", ""),
                                            "pending_work": output.get("pending_work", [])},
                    "context_request_results": context_results}
        feedback["rejected_file_sources"] = {
            name: (ROOT / name).read_text()
            for item in rejected if (name := item.get("path")) in snapshots
        }
        # Include the actual failed VCS compile, elaboration or simulation log.
        if rtl.exists():
            feedback["vcs_case_feedback"] = {
                str(p.relative_to(rtl)): p.read_text(errors="replace")[-16000:]
                for p in rtl.glob("*/*.log")
            }
        write_json(attempt / "validation.json", feedback)
        last_tool_feedback = feedback
        if feedback["status"] == "pass":
            write_json(status_path, {"status": "shared_leaf_handoff" if shared_handoff else "leaf_compile_pass", "iteration": index,
                                    "validation": str(attempt / "validation.json"),
                                    "remaining": "Run each model's generated complete-top Chisel compile/elaboration and exact-board adapter/connected-top VCS before synthesis or completion."})
            return


def ensure_requested_architecture(run_dir: Path) -> None:
    """Execute an authorized shared repair before binding the template library."""

    path = run_dir / "input" / "architecture_implementation_request.json"
    if not path.is_file():
        return
    request = json.loads(path.read_text())
    status_path = Path(request["out"]) / "implementation_status.json"
    if status_path.is_file():
        status = json.loads(status_path.read_text())
        if status.get("status") in SHARED_HANDOFF_STATUSES:
            # Recheck explicit request requirements after a supervisor reload:
            # an older in-flight worker may not have loaded the new gate code.
            specification = json.loads(Path(request["request"]).read_text()) if request.get("request") else {}
            needs_case_checks = (specification.get("required_compiled_port_widths_by_case")
                                 or specification.get("required_integer_cases"))
            needs_complete = specification.get("require_shared_implementation_complete")
            if not needs_case_checks and not needs_complete:
                return
            validation_path = Path(status.get("validation", ""))
            rtl = validation_path.parent / "rtl"
            validation = json.loads(validation_path.read_text()) if validation_path.is_file() else {}
            if validation.get("handoff") == "completed_without_new_edits" and not rtl.is_dir():
                # A declaration-only completion reuses the last real compile.
                # It must not require a new RTL directory in the no-edit round.
                previous = sorted(path for path in Path(request["out"]).glob("iteration_*/rtl")
                                  if path.parent.name < validation_path.parent.name)
                if previous:
                    rtl = previous[-1]
            checks = compiled_case_coverage(
                rtl, specification.get("required_compiled_port_widths_by_case", {}),
                specification.get("required_integer_cases", []))
            result_path = validation_path.parent / "llm/shared_architecture_implementation_agent_result.json"
            output = json.loads(result_path.read_text()).get("output", {}) if result_path.is_file() else {}
            complete = (not needs_complete or (output.get("implementation_complete") is True
                                               and not output.get("pending_work")))
            if complete and all(check["returncode"] == 0 for check in checks):
                return
            status.update(status="implementing", handoff_recheck={
                "checks": checks, "implementation_complete": complete})
            write_json(status_path, status)
    import sys

    argv = [sys.executable, "-u", "-m", "accagent.framework.architecture_implementation"]
    for key in ["request", "out", "remote-host", "remote-dir", "ip-context", "simlib-setup", "ip-models"]:
        argv.extend(["--" + key, str(request[key])])
    if request.get("vcs-home"):
        argv.extend(["--vcs-home", str(request["vcs-home"])])
    # The shared worker can outlive the caller during supervisor recovery.
    # Keep its output independent of a caller-owned pipe that may be closed.
    shared_log = Path(request["out"]) / "implementation.log"
    shared_log.parent.mkdir(parents=True, exist_ok=True)
    with shared_log.open("a") as output:
        subprocess.run(argv, cwd=ROOT, check=True, stdout=output, stderr=subprocess.STDOUT)


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ["request", "out"]:
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ["remote-host", "remote-dir", "ip-context", "simlib-setup", "ip-models"]:
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--vcs-home", default=os.environ.get("SPATIALACC_VCS_HOME", ""))
    parser.add_argument("--validation-feedback", type=Path)
    parser.add_argument("--replay-candidate", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    import fcntl

    with (args.out / "implementation.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        status_path = args.out / "implementation_status.json"
        if status_path.is_file() and json.loads(status_path.read_text()).get("status") in SHARED_HANDOFF_STATUSES:
            return
        implement(args)


if __name__ == "__main__":
    main()
