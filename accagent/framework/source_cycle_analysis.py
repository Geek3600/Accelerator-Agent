"""Source-schedule latency estimates for synthesis-driven optimization."""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
from pathlib import Path
from typing import Any


PERFORMANCE_MODEL = "single_block_reuse_operator_token_pipeline_v2_no_handoff"
MAX_EMITTED_RTL_SOURCE_BYTES = 16 * 1024


def analysis_path(run_dir: Path) -> Path:
    return run_dir / "backend_board" / "qor" / "source_cycle_analysis.json"


def _synthesis_source_context(run_dir: Path) -> tuple[dict[str, str], str]:
    report_path = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("source-cycle analysis requires a successful current synthesis report") from exc
    if (
        not isinstance(report, dict)
        or report.get("status") != "pass"
        or report.get("mode") != "synth"
        or report.get("measurement_scope") != "generated_kernel_synthesis"
        or report.get("collect_only") is True
    ):
        raise ValueError("source-cycle analysis requires the latest generated-kernel synthesis to pass")
    archive = Path(str(report.get("closure_archive", "")))
    if not archive.is_file():
        raise ValueError("latest synthesis source-closure archive is missing")
    if archive.stat().st_mtime_ns > report_path.stat().st_mtime_ns:
        raise ValueError("a newer synthesis source archive is not covered by the latest synthesis report")
    commands = report.get("commands")
    uploaded = any(
        isinstance(command, dict)
        and isinstance(command.get("argv"), list)
        and bool(command["argv"])
        and Path(str(command["argv"][0])).name == "scp"
        and any(Path(str(argument)).name == archive.name for argument in command["argv"])
        for command in (commands if isinstance(commands, list) else [])
    )
    if not uploaded and not report.get("synthesis_source_archive_sha256"):
        raise ValueError("latest synthesis report does not identify the source archive used by Vivado")
    archive_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    expected_digest = report.get("synthesis_source_archive_sha256")
    if expected_digest and expected_digest != archive_digest:
        raise ValueError("synthesis source archive differs from the one recorded by the latest synthesis")

    sources: dict[str, str] = {}
    try:
        with tarfile.open(archive, "r:gz") as bundle:
            members = bundle.getmembers()
            for member in members:
                if not member.isfile():
                    continue
                name = member.name
                relative = None
                if name.startswith("generated_vivado/"):
                    relative = "generated/chisel/vivado/" + name.removeprefix("generated_vivado/")
                elif name.startswith("analysis_context/"):
                    relative = "generated/chisel/" + name.removeprefix("analysis_context/")
                elif name.startswith("src/main/resources/"):
                    relative = "generated/chisel/" + name
                elif name == "fpga_ip_modules.txt":
                    relative = "generated/chisel/simulation/fpga_ip_modules.txt"
                elif name == "gen_xilinx_fp_ips_23.tcl":
                    relative = "generated/chisel/scripts/gen_xilinx_fp_ips_23.tcl"
                if relative is None:
                    continue
                source_file = bundle.extractfile(member)
                if source_file is not None:
                    sources[relative] = source_file.read().decode("utf-8", errors="ignore")
    except (OSError, tarfile.TarError) as exc:
        raise ValueError("latest synthesis source-closure archive cannot be read") from exc
    if "generated/chisel/vivado/GeneratedAxiDdrTop.sv" not in sources:
        raise ValueError("latest synthesis archive has no GeneratedAxiDdrTop RTL")

    if not any(path.startswith("generated/chisel/src/main/scala/") for path in sources):
        chisel_root = run_dir / "generated" / "chisel"
        fallback_sources = list((chisel_root / "src" / "main" / "scala").glob("**/*.scala"))
        runtime_config = chisel_root / "runtime" / "runtime_config.json"
        if runtime_config.is_file():
            fallback_sources.append(runtime_config)
        if any(path.stat().st_mtime_ns > archive.stat().st_mtime_ns for path in fallback_sources):
            raise ValueError("cycle-analysis context changed after synthesis; rerun synthesis before estimating performance")
        for path in fallback_sources:
            sources[str(path.relative_to(run_dir))] = path.read_text(encoding="utf-8", errors="ignore")
    return sources, archive_digest


def source_context(run_dir: Path) -> dict[str, Any]:
    sources, archive_digest = _synthesis_source_context(run_dir)
    workload: dict[str, Any] = {}
    runtime_config_path = run_dir / "generated" / "chisel" / "runtime" / "runtime_config.json"
    if runtime_config_path.is_file():
        report_path = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
        if runtime_config_path.stat().st_mtime_ns > report_path.stat().st_mtime_ns:
            raise ValueError("runtime workload configuration is newer than the latest synthesis")
        try:
            runtime_config = json.loads(runtime_config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("runtime workload configuration is invalid") from exc
        layout = runtime_config.get("memory_layout", {}) if isinstance(runtime_config, dict) else {}
        shape = layout.get("tensor_shape", {}) if isinstance(layout, dict) else {}
        tokens = shape.get("seq_len") if isinstance(shape, dict) else None
        batch_size = shape.get("batch_size", 1) if isinstance(shape, dict) else None
        layers = layout.get("num_layers") if isinstance(layout, dict) else None
        if type(tokens) is int and tokens > 0 and type(batch_size) is int and batch_size > 0:
            workload["processed_tokens"] = tokens * batch_size
            workload["sequence_length"] = tokens
            workload["batch_size"] = batch_size
        for key in ("hidden_size", "intermediate_size"):
            value = shape.get(key) if isinstance(shape, dict) else None
            if type(value) is int and value > 0:
                workload[key] = value
        axi_data_width_bits = layout.get("axi_data_width_bits") if isinstance(layout, dict) else None
        if type(axi_data_width_bits) is int and axi_data_width_bits > 0:
            workload["axi_data_width_bits"] = axi_data_width_bits
        params = runtime_config.get("params", {}) if isinstance(runtime_config, dict) else {}
        lanes = params.get("lanes") if isinstance(params, dict) else None
        if type(lanes) is int and lanes > 0:
            workload["lanes"] = lanes
        if type(layers) is int and layers > 0:
            workload["model_layers"] = layers
        transfer_rules = layout.get("transfer_rules", []) if isinstance(layout, dict) else []
        run_sequence = runtime_config.get("run_sequence", []) if isinstance(runtime_config, dict) else []
        if transfer_rules:
            workload["weight_transfer_rules"] = transfer_rules
        if run_sequence:
            workload["runtime_sequence"] = run_sequence
    return {
        "sources": sources,
        "synthesis_source_archive_sha256": archive_digest,
        "workload": workload,
        "schedule_policy": {
            "mode": "nominal_no_stall",
            "performance_model": PERFORMANCE_MODEL,
            "physical_transformer_blocks": 1,
            "model_layer_execution": "sequential_reuse_of_the_same_block",
            "initial_layer_weights_preloaded": True,
            "runtime_constants_preloaded": True,
            "next_layer_weight_prefetch": "overlapped_with_current_layer_compute",
            "external_backpressure_cycles": 0,
            "operator_initiation_interval_source": "synthesized_ip_configuration_and_rtl",
        },
    }


def _cycle_analysis_prompt_sources(sources: dict[str, str]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    prompt_sources: dict[str, str] = {}
    omitted_rtl: list[dict[str, Any]] = []
    for path, source in sources.items():
        source_bytes = len(source.encode("utf-8"))
        if (
            path.endswith(".scala")
            or path.endswith("/runtime_config.json")
            or path.endswith("/gen_xilinx_fp_ips_23.tcl")
            or path.endswith("/fpga_ip_modules.txt")
        ):
            prompt_sources[path] = source
        elif path.endswith(".sv"):
            modules = re.findall(r"(?m)^\s*module\s+(\w+)", source)
            filename = Path(path).name
            topology_rtl = filename in {"GeneratedAcceleratorTop.sv", "GeneratedAxiDdrTop.sv"} or filename.endswith("Block.sv")
            memory_wrapper = filename.startswith("PhysicalSimpleDualPortMemory")
            if not memory_wrapper and source_bytes <= MAX_EMITTED_RTL_SOURCE_BYTES:
                prompt_sources[path] = source
            else:
                reason = "expanded_memory_wrapper" if memory_wrapper else (
                    "expanded_hierarchy_use_complete_chisel" if topology_rtl else "expanded_module_size"
                )
                omitted_rtl.append({"path": path, "bytes": source_bytes, "modules": modules, "reason": reason})
    if not prompt_sources:
        raise ValueError("source-cycle analysis has no compact RTL or design-source context")
    return prompt_sources, omitted_rtl


def source_fingerprint(run_dir: Path) -> str:
    return hashlib.sha256(json.dumps(source_context(run_dir), sort_keys=True).encode()).hexdigest()


def pipeline_cycle_total(schedule: Any, processed_tokens: int, model_layers: int = 1) -> int:
    """Count one streamed block pass per model layer on one reused block."""

    if not isinstance(schedule, dict) or schedule.get("mode") != "single_block_reuse":
        raise ValueError("source-cycle analysis requires a single reused transformer block")
    if schedule.get("operator_token_overlap") is not True:
        raise ValueError("source-cycle analysis lacks operator token overlap")
    if type(processed_tokens) is not int or processed_tokens <= 0:
        raise ValueError("source-cycle analysis requires positive processed_tokens")
    if type(model_layers) is not int or model_layers <= 0:
        raise ValueError("source-cycle analysis requires positive model_layers")
    startup = schedule.get("start_to_first_input_cycles")
    interval = schedule.get("steady_state_ii_cycles")
    completion = schedule.get("last_token_start_to_completion_cycles")
    if type(startup) is not int or startup < 0 or type(interval) is not int or interval <= 0:
        raise ValueError("startup cycles must be non-negative and steady-state II must be positive")
    if type(completion) is not int or completion <= 0:
        raise ValueError("last-input completion latency must be positive")
    intervals = schedule.get("token_start_intervals")
    interval_cycles = (processed_tokens - 1) * interval
    if intervals is not None:
        if not isinstance(intervals, list) or any(
            not isinstance(term, dict)
            or type(term.get("cycles")) is not int or term["cycles"] <= 0
            or type(term.get("repetitions")) is not int or term["repetitions"] <= 0
            for term in intervals
        ):
            raise ValueError("token start intervals require positive integer cycles and repetitions")
        if sum(term["repetitions"] for term in intervals) != processed_tokens - 1:
            raise ValueError("token start intervals must cover exactly processed_tokens minus one gaps")
        interval_cycles = sum(term["cycles"] * term["repetitions"] for term in intervals)
    block_cycles = startup + interval_cycles + completion
    return model_layers * block_cycles


def _pipeline_source_evidence(context: dict[str, Any], output: dict[str, Any]) -> None:
    """Require source evidence for one reused block and its token stream."""

    references = output.get("source_refs")
    sources = context.get("sources", {})
    if not isinstance(references, list) or not references:
        raise ValueError("source-cycle analysis requires source references for pipeline evidence")
    selected = "\n".join(str(source) for source in sources.values())
    if not re.search(r"(?:ready|valid|Decoupled|io_in_ready|io_out_valid)", selected, re.I):
        raise ValueError("source-cycle analysis has no ready/valid pipeline evidence")
    if not re.search(r"\.io\.(?:in|out)\s*<>\s*\w+\.io\.(?:in|out)", selected):
        raise ValueError("source-cycle analysis has no connected operator stream evidence")
    top_sources = [
        str(source)
        for reference, source in sources.items()
        if "GeneratedAcceleratorTop" in Path(reference).name
    ]
    block_instances = [
        instance
        for source in top_sources
        for instance in re.findall(r"Module\s*\(\s*new\s+([A-Za-z_]\w*Block)\s*\(", source)
    ]
    if len(block_instances) != 1:
        raise ValueError("source-cycle analysis must cite the top with exactly one physical transformer block")
    if output.get("pipeline_schedule", {}).get("mode") != "single_block_reuse":
        raise ValueError("model layers must reuse one physical transformer block sequentially")


def ensure_source_cycle_analysis(run_dir: Path, *, context_override: dict[str, Any] | None = None) -> Path:
    from accagent.framework.stage_llm import run_stage_agent

    context = context_override or source_context(run_dir)
    fingerprint = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
    path = analysis_path(run_dir)
    if context_override is not None:
        path = path.with_name("compiled_source_cycle_analysis.json")
    if path.is_file():
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, AttributeError):
            cached = {}
        try:
            cache_valid = (
                isinstance(cached, dict)
                and cached.get("status") == "pass"
                and cached.get("performance_model") == PERFORMANCE_MODEL
                and cached.get("source_fingerprint") == fingerprint
                and all(type(cached.get(key)) is int and cached[key] > 0 for key in ("latency_cycles", "processed_tokens", "model_layers"))
                and cached.get("derivation") and cached.get("assumptions") and cached.get("source_refs")
                and pipeline_cycle_total(cached.get("pipeline_schedule"), cached["processed_tokens"], cached["model_layers"]) == cached["latency_cycles"]
            )
        except (TypeError, ValueError):
            cache_valid = False
        if cache_valid:
            return path
    synthesis_report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
    synthesis = (json.loads(synthesis_report.read_text(encoding="utf-8"))
                 if context_override is None else {
                     "status": "not_yet_synthesized", "mode": "compile_verified_source_analysis",
                     "measurement_scope": "analytical_schedule_only", "synthesis_top": "GeneratedAxiDdrTop"})
    analysis_dir = path.parent / ("cycle_analysis" if context_override is None else "compiled_cycle_analysis")
    previous_result = analysis_dir / "llm" / "source_cycle_analysis_agent_result.json"
    try:
        previous_attempt = json.loads(previous_result.read_text(encoding="utf-8")).get("output")
    except (OSError, ValueError):
        previous_attempt = None
    repair_feedback = None
    repairs = list((run_dir / "backend_board/timing_optimization").glob("**/application.json"))
    if repairs:
        latest_repair = max(repairs, key=lambda item: item.stat().st_mtime_ns)
        try:
            repair = json.loads(latest_repair.read_text(encoding="utf-8"))
            repair_feedback = {
                "report_path": str(latest_repair),
                "status": repair.get("status"),
                "implementation_summary": repair.get("implementation_summary"),
                "changed_sources": repair.get("changed_sources", []),
            }
        except (OSError, ValueError):
            pass
    prompt_sources, omitted_rtl = _cycle_analysis_prompt_sources(context["sources"])
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["ready", "blocked"]},
            "blocker_kind": {"type": "string", "enum": ["none", "noncompleting_hardware_schedule", "insufficient_source_context"]},
            "pipeline_schedule": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["single_block_reuse"]},
                    "operator_token_overlap": {"type": "boolean", "const": True},
                    "start_to_first_input_cycles": {"type": "integer", "minimum": 0},
                    "steady_state_ii_cycles": {"type": "integer", "minimum": 1},
                    "last_token_start_to_completion_cycles": {"type": "integer", "minimum": 1},
                    "token_start_intervals": {
                        "type": "array", "items": {
                            "type": "object",
                            "properties": {"cycles": {"type": "integer", "minimum": 1}, "repetitions": {"type": "integer", "minimum": 1}},
                            "required": ["cycles", "repetitions"],
                        },
                    },
                },
                "required": ["mode", "operator_token_overlap", "start_to_first_input_cycles", "steady_state_ii_cycles", "last_token_start_to_completion_cycles"],
            },
            "processed_tokens": {"type": "integer", "minimum": 1},
            "model_layers": {"type": "integer", "minimum": 1},
            "derivation": {"type": "string"},
            "assumptions": {"type": "array", "items": {"type": "string"}},
            "source_refs": {"type": "array", "minItems": 1, "items": {"type": "string", "enum": list(prompt_sources)}},
        },
        "required": ["status", "derivation", "blocker_kind"],
        "additionalProperties": True,
    }
    record = run_stage_agent(
        agent="source_cycle_analysis_agent",
        stage="backend_board",
        task="Derive the no-stall source-schedule latency for the declared full-model workload on the supplied build-verified single-block accelerator. Do not edit hardware or execute simulation.",
        inputs={
            **context,
            "sources": prompt_sources,
            "omitted_emitted_rtl": omitted_rtl,
            "source_context_summary": {
                "archive_source_count": len(context["sources"]),
                "archive_source_bytes": sum(len(source.encode("utf-8")) for source in context["sources"].values()),
                "provided_source_count": len(prompt_sources),
                "provided_source_bytes": sum(len(source.encode("utf-8")) for source in prompt_sources.values()),
                "omitted_emitted_rtl_count": len(omitted_rtl),
            },
            "synthesis_evidence": {
                "report_path": str(synthesis_report),
                "status": synthesis["status"], "mode": synthesis["mode"],
                "measurement_scope": synthesis["measurement_scope"],
                "synthesis_top": synthesis.get("synthesis_top"),
                "verified_source_archive_sha256": context["synthesis_source_archive_sha256"],
                "framework_verified_source_binding": context_override is None,
            },
            "previous_attempt_for_correction_only": previous_attempt,
            "latest_repair_feedback_for_source_recheck": repair_feedback,
        },
        out_dir=analysis_dir,
        fallback_summary="Source-cycle estimation needs the current sources and an LLM analysis.",
        output_schema=schema,
        prompt_rules=[
            "Historical diagnoses and repair summaries are fallible feedback, not source evidence. Reconcile latest_repair_feedback_for_source_recheck with previous_attempt_for_correction_only against the supplied current sources. For every alleged non-completing FSM or stream dependency, cite the exact current branch and guard and check its alternative progress paths, independent feed/drain counters, and the actually instantiated numeric-mode implementation. If a previous dependency has been repaired, explicitly retract it and derive the current finite schedule or identify a different source-grounded blocker; do not repeat the old diagnosis from memory. A repair summary alone also cannot prove completion.",
            "Use only the supplied RTL, workload configuration, and matching analysis context. For a synthesized source the archive SHA-256 is supplied; for a compile-verified source compile_evidence and compiled_source_snapshot_sha256 identify current VCS-compiled hardware awaiting synthesis. In the latter case derive cycles only; no achieved clock or synthesis result is claimed. Do not use board-integration testbench RTL or an older cycle report. Cite the generated accelerator top and operator-pipeline source paths.",
            "All matching Chisel sources, design parameters, runtime configuration, and small emitted arithmetic RTL are included. omitted_emitted_rtl indexes mechanically expanded RTL omitted from this exact synthesis archive projection, including large flattened top/block modules. Derive their loop, counter, memory behavior and complete connectivity from the matching Chisel top/block/operator sources and parameter bindings. The archive digest binds both included and omitted files; omission of expanded RTL is not missing hardware context.",
            "Treat the supplied synthesis_evidence or compile_evidence as the already-validated source/build provenance. A source-schedule derivation needs no extra attestation or synthesis run. Compile-only evidence does not establish functional correctness or measured performance; it supplies the current source for analysis and diagnosis.",
            "The architecture has exactly one physical Transformer block. The same block executes model layers sequentially with layer-specific weights. For this nominal estimate assume next-layer prefetch adds zero handoff cycles; do not try to prove the assumption from the single-block RTL and do not add another check. Never treat layers as parallel hardware stages, and never multiply token count by model_layers.",
            "processed_tokens is the input sequence length times batch size for one complete model inference, not tokens multiplied by layers. One token means one full sequence position/hidden vector, not one StreamBeat; derive how many beats form a token from the configured hidden size, lane width, and RTL framing. Prefer dimensions supplied from runtime_config. The framework rejects token/layer counts that disagree with that configuration.",
            "Within each block pass, operator stages may overlap different tokens through connected ready/valid streams. Do not sum every operator's latency for every token. Derive steady_state_ii_cycles from the actual bottleneck stage's source loop bounds, stream handshakes, operator initiation intervals, and any sequence-wide barriers. If the RTL has a sequence barrier or a stage that serializes work, include its actual effect; do not assume one token per cycle.",
            "Trace the complete connected path from the block input through the driver of the block's final io_out port. Account for every downstream stage and join, including post-attention normalization, MLP/FFN, activation, and final residual when present. Ending the tail calculation at attention output instead of the actual block output is invalid. Include a concise per-stage service/fill/drain table in the derivation and check that the chosen bottleneck includes the entire path. Read actual nested FSM counter/reset conditions rather than assuming ideal matrix-operation counts. Recheck any previous attempt against these rules; its numbers are not evidence.",
            "Timing optimization can add requant pipeline registers, multi-cycle normalization output states, iterative reciprocal/division loops, and attention reduction states. Derive their current latency AND actual initiation interval from the archived source. An added pipeline stage with II=1 is not a per-element stall; a serialized FSM loop must be charged for every affected beat or token. Do not reuse the original DSE compute cycles or infer cycles from Fmax. Analyze compute with weights available: the framework separately combines this schedule with the existing DSE initial-refill and overlapped-prefetch terms, so do not include DDR transfer cycles here.",
            "The compute-only contract supplies resident weights and nominal cache service: assume a requested tile is available, honor the cache RTL's fixed read/capture latency, and exclude miss/refill waiting from this analysis. Cache readReady waiting caused solely by DDR availability is not missing timing evidence: the DSE DDR service model separately accounts for it. This assumption never removes arithmetic/control FSM states or token/chunk dependencies. If there is a proven non-completing state or cyclic stream dependency even under this resident-tile contract, return blocked with blocker_kind=noncompleting_hardware_schedule and cite the exact source dependency. Use insufficient_source_context only for genuinely absent source/dimension facts; use none when ready. An uncertainty about external memory service alone is not a hardware defect to repair.",
            "schedule_policy.runtime_constants_preloaded explicitly places required runtime lookup tables, positional/rotary constants, quantization scales and other immutable setup data before accepted compute start. Assume their documented initialization transaction has completed, including its loaded/ready flag, just as initial-layer weights are resident. Exclude this setup transfer from compute cycles; missing external preload timing is not insufficient_source_context or a hardware deadlock under this contract. Still count all in-run arithmetic, control, stream and repeated-layer reset/start dependencies. State this assumption and the excluded setup cost in the derivation; this is a nominal analytical precondition, not evidence that board initialization or its numerical values have been validated.",
            "For serialized IP use (issue followed by waiting for that result before issuing the next request), use the matching generated Tcl C_Latency and RTL state transitions to bound the service time. Under nominal_no_stall, operands are accepted when the issue handshake is asserted and result-ready remains high. Such a single-outstanding call does not require an independently measured streaming IP initiation interval; do not assume II=1 for a continuously issuing stream, and do not block single-outstanding analysis just because CONFIG.C_Rate is not explicitly set.",
            "Distinguish serialized calls from tagged, decoupled arithmetic pipelines with multiple operations in flight. When the actual source interleaves independent partial-sum contexts and the generated IP has C_Rate=1, pipeline latency is fill/drain overhead, not a per-MAC issue interval. Count the actual request handshakes, context reuse hazards, reduction levels and partial-sum folding/bias phases; do not multiply every request by the full multiplier/reduction/adder latency. Account for overlapping input fill, computation and output drain when the source has separate ping-pong buffers. Count reachable row/group transitions, not an intended matrix loop that the RTL does not execute, and identify skipped work separately from legitimate throughput improvement.",
            "Report start_to_first_input_cycles as cycles from accepted run start to the first beat of the first complete token, steady_state_ii_cycles as cycles between starts of complete tokens in the no-stall steady state (including all beats per hidden vector), and last_token_start_to_completion_cycles as cycles from the first beat of the final token through the final output transfer. This counts pipeline fill and drain exactly once.",
            "Use mode=single_block_reuse and operator_token_overlap=true. The framework computes model_layers * (start_to_first_input_cycles + (processed_tokens - 1) * steady_state_ii_cycles + last_token_start_to_completion_cycles), with zero inter-layer handoff by assumption.",
            "If warm-up, a sequence barrier, or backpressure makes ingress token intervals nonuniform, return pipeline_schedule.token_start_intervals as run-length encoded {cycles, repetitions} terms covering exactly processed_tokens-1 actual ingress gaps. The framework sums these gaps instead of repeating steady_state_ii_cycles. Keep last_token_start_to_completion_cycles relative to the actual final-token start; never return ready with a known representation overcount or silently replace the actual final-token start by an idealized one.",
            "For the nominal compute-only estimate, assume inter-layer weight handoff is zero and memory-transfer stalls are excluded. This is an ideal no-stall projection, not a measured whole-system result. Do not block because the single-block RTL does not contain the whole-model weight scheduler.",
            "Do not invent dimensions or unexplained cycle constants. Derive operator initiation intervals and token schedule from the synthesized RTL and IP configuration; if those finite source-grounded bounds or connected operator-stream evidence are missing, return blocked rather than reverting to serial per-operator latency sums. Board runtime and numerical validation are not required for this analytical estimate.",
        ],
    )
    output = record.get("output") or {}
    return save_source_cycle_analysis(run_dir, context, output, context_override=context_override)


def save_source_cycle_analysis(
    run_dir: Path, context: dict[str, Any], output: dict[str, Any], *,
    context_override: dict[str, Any] | None = None,
) -> Path:
    fingerprint = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
    path = analysis_path(run_dir)
    if context_override is not None:
        path = path.with_name("compiled_source_cycle_analysis.json")
    if output.get("status") != "ready":
        raise ValueError(f"source-cycle analysis is incomplete: {output.get('derivation', 'no derivation')}")
    if not isinstance(output.get("pipeline_schedule"), dict):
        raise ValueError("source-cycle analysis is missing its one-block pipeline schedule")
    output["pipeline_schedule"]["exposed_layer_handoff_cycles"] = 0
    for key in ("processed_tokens", "model_layers"):
        if type(output.get(key)) is not int or output[key] <= 0:
            raise ValueError(f"source-cycle analysis has invalid {key}")
        if context["workload"].get(key) is not None and output[key] != context["workload"][key]:
            raise ValueError(f"source-cycle analysis {key} disagrees with the synthesized runtime workload")
    if not output.get("derivation") or not output.get("assumptions") or not output.get("source_refs"):
        raise ValueError("source-cycle analysis must retain its derivation, assumptions, and source references")
    if any(reference not in context["sources"] for reference in output["source_refs"]):
        raise ValueError("source-cycle analysis cites an unavailable source")
    _pipeline_source_evidence(context, output)
    output["latency_cycles"] = pipeline_cycle_total(
        output.get("pipeline_schedule"), output["processed_tokens"], output["model_layers"]
    )
    if context_override is None:
        current_fingerprint = source_fingerprint(run_dir)
    else:
        from accagent.framework.dse_timing_calibration import compiled_source_context

        current_fingerprint = hashlib.sha256(json.dumps(compiled_source_context(run_dir), sort_keys=True).encode()).hexdigest()
    if current_fingerprint != fingerprint:
        raise ValueError("hardware sources changed during source-cycle analysis; retry the current sources")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        **output,
        "status": "pass",
        "counter_source": "source_schedule_analysis",
        "source_fingerprint": fingerprint,
        "synthesis_source_archive_sha256": context["synthesis_source_archive_sha256"],
        "schedule_policy": context["schedule_policy"],
        "measurement_kind": "analytical_estimate",
        "performance_model": PERFORMANCE_MODEL,
        "estimate_scope": "generated_pipeline_schedule",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
