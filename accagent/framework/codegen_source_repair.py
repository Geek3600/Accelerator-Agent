"""Execute compiler-localized template repairs before repeating Stage-5 reviews."""

from __future__ import annotations

import fcntl
import hashlib
import os
import re
import subprocess
from pathlib import Path

from accagent.framework.architecture_implementation import ROOT, SCHEMA, apply_edits
from accagent.framework.sacg_utils import read_json, write_json
from accagent.framework.stage_llm import run_stage_agent


def bind_source_anchors(edits: list[dict], sources: dict[str, str]) -> list[dict]:
    """Bind unique identical code when an agent only paraphrased anchor comments."""
    token_pattern = re.compile(
        r'"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])\''
        r'|//[^\n]*|/\*[\s\S]*?\*/|\s+|[A-Za-z_$]\w*|\d+|[!#%&*+\-/:<=>?@\\^|~]+|.',
        re.DOTALL)

    def tokens(text):
        return [(m.group(), m.start(), m.end()) for m in token_pattern.finditer(text)
                if not m.group().isspace() and not m.group().startswith(("//", "/*"))]

    current = dict(sources)
    bound = []
    for edit in edits:
        path, old = edit["path"], edit["old_text"]
        text = current[path]
        if text.count(old) == 0:
            wanted = [row[0] for row in tokens(old)]
            actual = tokens(text)
            values = [row[0] for row in actual]
            candidates = [i for i, value in enumerate(values)
                          if wanted and value == wanted[0] and values[i:i + len(wanted)] == wanted]
            if len(candidates) == 1:
                index = candidates[0]
                old = text[actual[index][1]:actual[index + len(wanted) - 1][2]]
        bound.append({**edit, "old_text": old})
        if text.count(old) == 1:
            current[path] = text.replace(old, edit["new_text"], 1)
    return bound


def repair_timing_sources(
    run_dir: Path, out_dir: Path, qor: dict, *, analysis_context_run_dir: Path | None = None,
    analysis_context: dict | None = None,
) -> dict:
    """Optimize only this run's existing hardware; shared templates stay read-only."""
    from accagent.framework.source_cycle_analysis import source_context
    from accagent.framework.stage_repair_execute import apply_agent_file_edits

    timing = qor.get("critical_timing_path") or {}
    if not timing.get("source") or not timing.get("destination"):
        return {"status": "blocked", "blockers": ["current synthesis critical path is missing"]}
    if analysis_context is not None:
        context = analysis_context
    else:
        try:
            context = source_context(analysis_context_run_dir or run_dir)
        except ValueError as exc:
            if (analysis_context_run_dir is not None
                    or "a newer synthesis source archive is not covered by the latest synthesis report" not in str(exc)):
                raise
            from accagent.framework.dse_timing_calibration import compiled_source_context

            context = compiled_source_context(run_dir)
    fingerprint = context.get("synthesis_source_archive_sha256") or context["compiled_source_snapshot_sha256"]
    attempt_dir = out_dir / "timing_optimization" / fingerprint[:20]
    if analysis_context_run_dir is not None:
        # A retained measurement supplies read-only dimensions/timing while
        # the agent rechecks its schedule diagnosis against current sources.
        attempt_dir = attempt_dir / "schedule_repair"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    application = attempt_dir / "application.json"
    prior = {}
    if application.exists():
        prior = read_json(application)
        if prior.get("status") == "compiled_pending_vcs":
            from accagent.framework.stage_repair_execute import stage2_compile_only_authority

            if stage2_compile_only_authority(run_dir).get("status") != "ready":
                return prior
        if prior.get("status") == "applied_pending_validation":
            return compile_timing_sources(run_dir, attempt_dir, prior)
        if prior.get("status") in {"compile_failed", "blocked"}:
            log_path = Path(prior.get("incremental_compile", {}).get("log_path") or attempt_dir / "incremental_compile.log")
            if log_path.is_file():
                prior["compiler_diagnostics"] = log_path.read_text(errors="replace")[-64000:]
            patch_path = attempt_dir / "agent_patch_application.json"
            if prior.get("status") == "blocked" and patch_path.is_file():
                rejection = read_json(patch_path).get("agent_transaction_rejection", {})
                prior["patch_rejection_feedback"] = {
                    "blockers": rejection.get("blockers", []),
                    "rejected_file_edits": rejection.get("rejected_file_edits", []),
                }
    template_dir = run_dir / "generated/chisel/src/main/scala/spatialaccagent/templates"
    sources = {str(path.resolve()): path.read_text() for path in sorted(template_dir.glob("*.scala"))}
    if not sources:
        return {"status": "blocked", "blockers": ["current run operator sources are missing"]}
    parameter_context = {name: source for name, source in context["sources"].items()
                         if Path(name).name in {"GeneratedDesignParams.scala", "GeneratedAcceleratorTop.scala"}}
    diagnoses = list((out_dir / "qor").glob("*/llm/source_cycle_analysis_agent_result.json"))
    schedule_feedback = None
    if diagnoses:
        diagnosis_path = max(diagnoses, key=lambda path: path.stat().st_mtime_ns)
        schedule_feedback = {"report_path": str(diagnosis_path),
                             "diagnosis": read_json(diagnosis_path).get("output", {})}
    record = run_stage_agent(
        agent="codegen_source_repair_agent", stage="timing_optimization",
        task=(
            "Optimize the critical path in THIS EXISTING accelerator design. Use the actual Vivado "
            "path and the complete current-run operator sources. Return actual bounded file_edits, "
            "not an audit or a plan. Pipeline or restructure the long combinational cone and align "
            "its control/valid signals where needed. Do not change clock constraints, false paths or "
            "multicycle declarations to hide the delay. Preserve arithmetic semantics, W/A precision, "
            "DSE parameters, ready/valid backpressure, token overlap, DDR weights and active/shadow "
            "prefetch, external ABI and reset behavior. ONLY the supplied current-run Scala source "
            "paths are writable. Never edit shared framework templates or any other run. Do not "
            "regenerate a design/package or restart Stage5. Use exact old_text/new_text anchors. "
            "Optimize toward the explicit supplied clock target; the synthesis constraint itself "
            "is not the stopping goal. Meeting a throughput target alone does not satisfy a "
            "separate requested clock target. Report any added pipeline latency or initiation-interval "
            "change so throughput estimates cannot silently assume an unchanged schedule. "
            "If measured_qor.source_schedule_diagnosis reports a non-completing state or stream dependency, "
            "repair that current-source defect first, then continue critical-path optimization. "
            "On compiler/patch retries also recheck latest_schedule_feedback_for_source_recheck: "
            "a previous schedule blocker can remain unresolved even when measured_qor lacks it. "
            "Treat that diagnosis as fallible prior feedback; confirm its guards and progress paths "
            "against source_snapshots, then repair any still-present completion defect first. "
            "Preserve parallelism, token-chunk reuse and the selected array; do not bypass an operator, "
            "discard tokens, or reduce reuse/precision to manufacture a finite cycle estimate. "
            "Prefer pipelining that retains throughput; do not replace parallel computation with "
            "a long serialized loop merely to raise Fmax. On retry use previous_repair_feedback, "
            "especially rejected_file_edits; replace each rejected anchor with enough surrounding "
            "source lines to make it unique, copied literally from source_snapshots. "
            "The executor incrementally compiles/elaborates this existing project, reruns needed "
            "VCS compilation and obtains fresh Vivado timing; your response cannot grant a pass."
        ),
        inputs={"measured_qor": qor, "critical_timing_path": timing,
                "source_snapshots": sources, "read_only_synthesized_parameters": parameter_context,
                "previous_repair_feedback": prior,
                "latest_schedule_feedback_for_source_recheck": schedule_feedback,
                "workload": context["workload"], "synthesis_source_archive_sha256": fingerprint},
        out_dir=attempt_dir, output_schema=SCHEMA,
        fallback_summary="Current-design critical path requires a bounded implementation repair.",
    )
    output = record.get("output", {})
    edits = output.get("file_edits", [])
    if output.get("status") != "ready_to_apply" or not edits:
        report = {"status": "blocked", "blockers": output.get("blocked_reasons", []), "changed_sources": []}
    else:
        if any(edit.get("path") not in sources for edit in edits):
            raise ValueError("timing repair attempted to edit outside this run's supplied operator sources")
        edits = bind_source_anchors(edits, sources)
        patches = [{"path": edit["path"], "operation": "replace_text", "content": "",
                    "expected_sha256": hashlib.sha256(sources[edit["path"]].encode()).hexdigest(),
                    "text_replacements": [{"old_text": edit["old_text"], "new_text": edit["new_text"]}],
                    "rationale": output.get("summary") or "Agent critical-path optimization"} for edit in edits]
        # Group multiple exact replacements on the same file into one atomic edit.
        grouped = {}
        for patch in patches:
            if patch["path"] in grouped:
                grouped[patch["path"]]["text_replacements"].extend(patch["text_replacements"])
            else:
                grouped[patch["path"]] = patch
        targets = {Path(name) for name in sources}
        with (attempt_dir / ".timing_source_repair.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = apply_agent_file_edits(
                {"status": "ready_to_apply", "file_edits": list(grouped.values())}, run_dir, attempt_dir,
                allowed_exact_files=targets, allowed_semantic_rtl_files=targets,
                allow_template_repair=False, require_exact_source_hash=True)
        changed = [row["path"] for row in result.get("files", [])]
        report = {"status": "applied_pending_validation" if result.get("status") == "pass" else "blocked",
                  "changed_sources": changed, "blockers": result.get("blockers", []),
                  "implementation_summary": output.get("summary"),
                  "synthesis_source_archive_sha256": fingerprint, "critical_timing_path": timing,
                  "shared_templates_modified": False}
    write_json(application, report)
    if report["status"] == "applied_pending_validation":
        return compile_timing_sources(run_dir, attempt_dir, report)
    return report


def compile_timing_sources(run_dir: Path, attempt_dir: Path, report: dict) -> dict:
    # Recompile the existing design in place; do not regenerate its package,
    # rerun Stage5 reviews or discard any already generated artifacts.
    root = run_dir / "generated/chisel"
    argv = ["sbt", "--no-server", "--batch", "--supershell=false", "Compile/compile",
            "runMain spatialaccagent.generated.GeneratedContractCheck",
            "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop",
            "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado"]
    env = os.environ.copy()
    env["JDK_JAVA_OPTIONS"] = "-Xmx1800m -XX:ActiveProcessorCount=2"
    with (attempt_dir / "incremental_compile.log").open("w") as log:
        result = subprocess.run(argv, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    report["incremental_compile"] = {"argv": argv, "returncode": result.returncode,
                                     "log_path": str(attempt_dir / "incremental_compile.log")}
    report["status"] = "compiled_pending_vcs" if result.returncode == 0 else "compile_failed"
    write_json(attempt_dir / "application.json", report)
    return report


def repair_compile_sources(compile_gate: dict, out_dir: Path) -> bool:
    """Ask the implementation agent for an actual patch, retaining all tool gates.

    Trusted templates named by compiler/stack diagnostics are editable. Generated
    source failures also expose their producer and directly referenced templates.
    A concurrent source update causes regeneration rather than a stale patch apply.
    """
    diagnostics = "\n".join(
        str(step.get(key, ""))
        for step in compile_gate.get("steps", [])
        for key in ("stdout_tail", "stderr_tail")
    )
    names = set(re.findall(r"\b([\w-]+\.scala)(?::|\s+)\d+", diagnostics))
    template_dir = ROOT / "accagent/framework/templates/operator_chisel"
    generated_evidence = {}
    generated_dir = Path(str(compile_gate.get("cwd") or "")) / "src/main/scala/spatialaccagent/generated"
    for name in sorted(names):
        path = generated_dir / name
        if path.is_file():
            generated_evidence[name] = path.read_text()
    if generated_evidence:
        referenced_types = set(re.findall(
            r"\b(?:new\s+)?([A-Z]\w*)\s*\(", "\n".join(generated_evidence.values())
        ))
        for path in template_dir.glob("*.scala"):
            declared_types = set(re.findall(r"\b(?:class|object|trait)\s+(\w+)", path.read_text()))
            if referenced_types & declared_types:
                names.add(path.name)
    sources = {
        str(path.relative_to(ROOT)): path.read_text()
        for name in sorted(names)
        if (path := template_dir / name).is_file()
    }
    if generated_evidence:
        producer = ROOT / "accagent/framework/stage_artifacts.py"
        if producer.is_file():
            sources[str(producer.relative_to(ROOT))] = producer.read_text()
    if not sources:
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    record = run_stage_agent(
        agent="codegen_source_repair_agent",
        stage="code_generation_repair",
        task=(
            "Implement the compiler-localized bounded source repair NOW. Return actual file_edits, "
            "not an executable_actions plan or another audit. The user authorized implementation "
            "bug fixes to advance the accelerator flow. Only supplied source paths are editable. "
            "Use the real compiler diagnostic and complete current sources to establish the cause. "
            "Preserve model geometry, legal DSE parameters, operator semantics, numeric policy, "
            "active/shadow DDR cache and prefetch behavior, pipeline overlap and external ABI. "
            "Do not suppress warnings, alter checkers or substitute hardware. Fix the source cause "
            "generically across legal parameter values, including singleton dimensions. Exact old_text "
            "must match supplied source; new_text is the minimal correction. If evidence is inadequate, "
            "return needs_context or blocked with concrete missing evidence. Fresh compile, elaboration, "
            "contract and package checks run after application; your response cannot grant a pass."
        ),
        inputs={"compile_gate": compile_gate, "source_snapshots": sources,
                "generated_diagnostic_sources_read_only": generated_evidence},
        out_dir=out_dir,
        output_schema=SCHEMA,
        fallback_summary="Compiler-localized source repair requires an actual implementation patch.",
    )
    output = record["output"]
    edits = output.get("file_edits", [])
    if output.get("status") != "ready_to_apply" or not edits:
        write_json(out_dir / "application.json", {"status": "no_patch", "changed_sources": []})
        return False
    for edit in edits:
        if edit.get("path") not in sources:
            raise ValueError(f"repair outside compiler-localized sources: {edit.get('path')}")
    with (template_dir / ".source_repair.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if any((ROOT / name).read_text() != source for name, source in sources.items()):
            write_json(out_dir / "application.json", {"status": "source_changed_regenerate", "changed_sources": []})
            return True
        changed = apply_edits(edits, out_dir / "original_sources", expected_sources=sources)
    write_json(out_dir / "application.json", {"status": "applied_pending_validation", "changed_sources": changed})
    return bool(changed)
