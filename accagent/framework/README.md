# SpatialAccAgent Framework

Executable framework code lives here. Research notes live in `accagent/docs`.

This is an independent, reusable multi-agent framework for designing LLM
spatial accelerators from scratch. The existing OPT accelerator and historical
context documents are development references only; they are not runtime inputs
or framework dependencies.

The framework is SACG-centered. It is not a free-form RTL generator.
`TopAgent` coordinates LLM-facing stage agents, deterministic tools, tool logs,
and SACG as the shared design state.

Python framework files are intentionally flat under `accagent/framework/`.
`templates/operator_chisel/` remains a separate hardware template library.

## Run

Edit run settings in:

```text
accagent/framework/config.py
```

Then run:

```bash
python3 -m accagent.framework.agent
```

The default run writes:

```text
accagent/runs/spatialacc_qwen_agent_fast_run/agent/agent_run_report.json
accagent/runs/spatialacc_qwen_agent_fast_run/backend_board/sacg_state.json
```

Run artifacts are intentionally stored under `accagent/runs/` instead of
`/tmp`, so LLM results, stage reports, SACG states, and checkpoints survive
session interruptions. The top-level agent resumes from passed stage
checkpoints when the stage code hash, report status, and SACG state are still
valid. Failed or stale artifacts are never promoted as successful evidence.

Remote real-tool jobs use the persistent root
`/home/<remote-user>/workspace/spatialaccagent_artifacts/` by default. Override
it with `SPATIALACC_REMOTE_ARTIFACT_ROOT` only when another persistent volume is
required. Each recoverable VCS job has a content-addressed directory. A remote
job becomes eligible for pruning only after its required logs/results have been
copied into `verification/remote_artifacts/<kind>/<fingerprint>/` and a local
evidence receipt has been acknowledged in that remote directory. Active,
current, and unacknowledged jobs are never pruned; the newest two acknowledged
completed jobs are retained by default. Set
`SPATIALACC_REMOTE_ARTIFACT_KEEP_COMPLETED` to adjust that bounded retention.

`/tmp` is reserved for reconstructable process coordination such as locks,
SSH known-host caches, and short-lived transfer staging. It is not a valid
default location for LLM records, checkpoints, real-tool work directories, or
verification evidence.

## Repair Experience

Stage 6 archives each verification/repair intervention together with its
current evidence context, atomic file transaction, requested validation, and
post-intervention real-tool result. Compact episodes are shared across runs in:

```text
accagent/runs/_shared_experience/repair_experience.jsonl
```

Set `SPATIALACC_REPAIR_EXPERIENCE_DB` to place this ledger on another persistent
volume. The ledger uses file locking and exact episode hashes to deduplicate
replayed repair-loop iterations. Outcomes are classified as
`validated_success`, `falsified`, or `inconclusive`. Only real-tool-backed
successes and failures are retrieved for later repair Agents; inconclusive
hypotheses remain archived but are never promoted as positive experience.

Retrieval matches structured failure class, violated contract, CCTG frontier,
pipeline stage role, verification scope, and repair gate. It supplies a small
relevant set rather than the full history. Experience is a hypothesis prior
only: it never expands editable files, overrides current SACG/source contracts,
or replaces same-layer real-tool validation. A falsified intervention cannot be
repeated without new distinguishing current-run evidence.

## Current Flow

```text
Stage 0  objective_and_input_preparation
Stage 1  sacg_extraction
Stage 2  trusted_templates_and_fpga_ip_binding
Stage 3  model_derived_spatial_pipeline
Stage 4  dse_and_parameter_binding
Stage 5  hardware_implementation_and_verification_preparation
Stage 6  hierarchical_real_verification_and_repair
Stage 7  vivado_implementation_and_qor
```

Stage 5 combines RTL/board-shell generation with real-weight, runtime-image,
testbench, CCTG, and three-layer verification preparation. Stage 6 owns all
three verification layers, repair, adaptive observation, and execution-only
fast replay. Stage 7 reports only `resources`, `power_w`,
`clock_frequency_mhz`, and `performance_tokens_per_second`; a small QoR miss
loops from Stage 7 to Stage 5, while a material architecture miss loops to
Stage 4. Every generated accelerator binds Vivado floating-point IP and XPM
physical memories, and VCS uses the matching generated IP timing models.

`config.py` sets the task spec, model source, current-run input material
directories, output directory, design id, LLM settings, and real-tool execution
policy directly in code.

Stage 0 is `input_preparation`. It is not a file-copy stage. It runs
LLM-facing sub-agents:

```text
model_config_agent
task_card_agent
numeric_policy_agent
board_profile_agent
design_space_agent
```

Those agents convert human documents, HuggingFace/local model configuration,
board/tool/quantization materials, and template metadata into structured
framework inputs. The current-run materials are read from:

```text
accagent/framework/input_materials/board/
accagent/framework/input_materials/quantization/
accagent/framework/input_materials/tools/
```

These directories are not persistent libraries. They are the board, numeric,
and tool inputs for this run. Normal agent experiments require an LLM; any
missing, disabled, or failed LLM call stops the run. Endpoint, model, and API
key are resolved from `SPATIALACC_LLM_*` environment variables first, then
from `~/.codex/config.toml` plus `~/.codex/auth.json` when present. The
framework reads OpenAI-compatible provider settings such as `model`,
`model_provider`, `base_url`, `wire_api = "responses"`, and `model_reasoning_effort`
and turns them into the request endpoint and payload used by Stage 0 and later
LLM stages.

Before each deterministic command, the framework writes a local, non-blocking
execution audit. It records the intended command for debugging but never calls
an LLM, vetoes a Stage tool, or becomes repair evidence.

Each major stage also runs its stage-local LLM worker that reviews the candidate
artifact produced by the deterministic stage tool:

```text
constraint_extraction   sacg_builder_agent
template_selection      template_selection_agent
pipeline_planning       pipeline_architect_agent
parameter_binding       dse_parameter_agent
code_generation         code_generation_agent
verification_artifacts  verification_planner_agent
verification            evidence_classifier_agent
repair                  repair_agent
backend_board           backend_closure_agent
```

Those workers write `<stage>/llm/<agent>_result.json` and their structured
outputs are embedded in the stage report as `llm_agent`. In formal LLM mode
with `enforce = True`, failure to run these workers stops the stage. In
deterministic smoke mode with `enforce = False`, they record fallback outputs
that are explicitly marked invalid for formal multi-agent experiments.

## Adaptive Design Team

Every stage now also has a chip-design-team subtask layer:

```text
<stage>/team/decomposer_prompt.md
<stage>/team/decomposer_result.json
<stage>/team/subtask_plan.json
<stage>/team/team_aggregate.json
<stage>/team/event_log.jsonl
```

The `team_decomposer` first decides whether the stage should be split into
parallel specialist subtasks. If splitting is useful, it creates a small set of
role-specific sub-agents such as model graph engineer, template risk engineer,
stream protocol engineer, memory/runtime engineer, verification harness
engineer, synthesis engineer, board runtime engineer, or evidence-gate auditor.
If splitting is not useful, it records `split_required = false`.

Each subtask carries a minimal SACG-controlled handoff protocol:

```text
role_profile
action_type
expected_artifacts
acceptance_checkers
handoff_to
handoff_rule
parallel_group
```

Subtasks in the same `parallel_group` run concurrently. Later groups run after
earlier groups, which allows independent specialists to run first and
auditor/evidence-gate roles to run after their inputs exist. The JSONL event
log records plan creation, group start/end, subtask start/end/failure, and
aggregate write events so each stage has a replayable team trajectory.

When the LLM is unavailable, formal framework runs stop. Any deterministic
candidate code path is only for local developer diagnostics and is not valid
agent output for experiments.

The team layer is deliberately scoped to the paper story:

```text
Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design
SACG-guided, template-constrained, checker-verified design closure
```

Sub-agents are asked to map observations to model, shape, numeric, stream,
order, memory, runtime, backend, deployment, or human-boundary constraints. They
must not propose free-form RTL rewrites, bypass checkers, modify golden outputs,
loosen tolerances, or claim final hardware pass without tool evidence.

The prior-work survey and design note for this team protocol is:

```text
accagent/docs/agent_prior_work_survey_and_team_design_2026_06_27.md
```

## Generated Code Package

`code_generation` now produces a run-local template-bound code package:

```text
<run_dir>/generated/chisel/
  build.sbt
  project/build.properties
  scripts/elaborate.sh
  src/main/scala/spatialaccagent/templates/*.scala
  src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala
  src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala
  src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala
  src/main/scala/spatialaccagent/generated/GeneratedContractCheck.scala
  src/main/scala/spatialaccagent/generated/GeneratedSACGMetadata.scala
  memory/memory_layout.json
  runtime/runtime_config.json
  logs/compile_check.json
  logs/codegen_contract_check.json
```

This is not free-form RTL generation. The generated package copies trusted Chisel
templates and emits binding/glue files from SACG model, pipeline, parameter,
numeric, and board facts. It includes the accelerator compute top and a
FPGA-facing AXI/DDR top boundary. Stage 5 is not considered passed by a smoke
run: it must pass deterministic code-generation contract checks covering
upstream promoted transitions, template provenance hashes, model/shape/numeric
binding, memory/runtime layout consistency, warning-free Chisel compile, and
top-level elaboration. Real DDR images, runtime scripts, testbenches,
synthesis, implementation, and board evidence are handled by later verification
and backend stages before any design pass can be claimed.

`verification_artifacts` now also emits:

```text
<run_dir>/verification_artifacts/verification_artifact_contract.json
```

This contract is a production gate, not a plan-only placeholder. It checks that
the upstream Stage 3/4/5 transitions were promoted, the Stage 5 codegen contract
passed, and the run has configured protocols for real weight artifacts, AXI/DDR
runtime checks, functional simulation, runtime bitstream, and board runtime
evidence. Missing or rejected upstream evidence makes Stage 6 incomplete.

`backend_board` now produces a declarative backend/app-shell contract package:

```text
<run_dir>/generated/backend/constraints/backend_handoff.json
<run_dir>/generated/backend/constraints/board_shell_contract.json
<run_dir>/generated/backend/constraints/app_shell_integration_contract.json
```

The package contains no placeholder executable. The current case adapter's
exact app-shell Vivado tool is the only backend execution authority. Pending or
failed real tools still block `final_design_pass`.

## LLM I/O Protocol

All framework LLM calls use the same prompt and output protocol:

```text
spatialaccagent.llm_io.v0
```

The shared implementation is:

```text
accagent/framework/llm_io.py
```

Each prompt is built from fixed blocks:

```text
<agent>
<task>
<rules>
<input blocks>
<output_schema>
```

The model must return exactly one top-level JSON object matching the supplied
schema. The framework then extracts response text, parses JSON, validates
required schema fields, and uses a schema-bound repair prompt only for malformed
LLM formatting. Stage 0 sub-agents and later pre-stage safety gates both use this same
protocol, so stage behavior is not allowed to depend on free-form markdown or
ad-hoc JSON wrappers.

Even in LLM mode, deterministic tools, checker evidence, and SACG validation
remain the source of truth.

Real EDA/board tools are registered in Stage 0 and written into SACG evidence
by Stage 7. Production framework runs use real tools by default:

```text
run_real_tools = True
```

Set `run_real_tools = False` only for local developer diagnostics that are not
valid formal agent-system results. Pending, skipped, dry-run, smoke-only, or
failed real tools block `final_design_pass`.

## Key Rule

```text
No touched constraints, no transition.
No required checker evidence, no promotion.
No approval, no boundary-changing transition.
```
