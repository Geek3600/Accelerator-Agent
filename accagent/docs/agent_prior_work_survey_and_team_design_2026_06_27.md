# Agent Prior Work Survey and SpatialAccAgent Team Design Update

Date: 2026-06-27

This note records the agent-framework survey used to refine the current
SpatialAccAgent implementation. It is written as an engineering design note:
which mechanisms from prior work are useful, which mechanisms should not be
copied, and what minimal implementation has been added to our framework.

## 1. Positioning

The goal is not to build a generic software-company agent. The target system is
a chip-design-team style agent for LLM FPGA spatial accelerators:

```text
model semantics
-> spatial pipeline
-> template-bound Chisel/RTL
-> stream / beat / memory / runtime contracts
-> verification evidence
-> backend / board handoff
```

The paper problem remains:

```text
Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design
```

So the useful agent mechanisms are those that improve:

- adaptive task decomposition;
- role-specialized parallel work;
- typed handoff between specialists;
- tool/checker evidence binding;
- reproducible event trajectories;
- bounded repair under SACG constraints.

The mechanisms that are not appropriate as core design choices are:

- unconstrained free-form RTL generation;
- multi-agent debate without executable evidence;
- natural-language memory as the only design state;
- claiming backend or board success from script generation alone.

## 2. General Agent Systems

### MetaGPT

Sources:

- Paper: https://openreview.net/forum?id=VtmBAGCN7o
- arXiv: https://arxiv.org/abs/2308.00352
- Code: https://github.com/geekan/MetaGPT
- Inspected code: `metagpt/roles/role.py`

Relevant implementation pattern:

- A `Role` has profile, goal, constraints, actions, state, memory, and an
  environment-facing message interface.
- The system encodes human workflow/SOP into stage-like prompt/action
  sequences.
- The useful unit is not just "another LLM call"; it is role + action +
  state + message boundary.

What we borrow:

- Explicit role identity and role capability.
- SOP-like stage order.
- Specialist roles that verify intermediate outputs.

What we do not borrow directly:

- A broad software-engineering assembly line. Our stages must stay tied to
  SACG transitions and accelerator artifacts.

SpatialAccAgent impact:

- `stage_team.py` now has a `ROLE_CATALOG` and each subtask records a
  `role_profile`.

### AutoGen

Sources:

- Paper: https://arxiv.org/abs/2308.08155
- Code: https://github.com/microsoft/autogen
- Inspected code:
  `python/packages/autogen-agentchat/src/autogen_agentchat/agents/_assistant_agent.py`

Relevant implementation pattern:

- Agents are customizable, conversable, and can use tools.
- AssistantAgent supports structured messages, handoff, tool execution, and
  bounded tool iterations.
- Tool calls can be parallel; handoff carries context to the target agent.

What we borrow:

- Explicit handoff contract rather than relying on chat history.
- Bounded action types and structured output.
- Parallel execution when subtasks are independent.

What we do not borrow directly:

- Fully generic chat orchestration. In hardware design, the shared state must
  be SACG + artifacts + evidence, not a conversation transcript.

SpatialAccAgent impact:

- Each subtask now declares `action_type`, `expected_artifacts`,
  `acceptance_checkers`, `handoff_to`, and `handoff_contract`.

### SWE-agent

Sources:

- Paper: https://arxiv.org/abs/2405.15793
- Code: https://github.com/SWE-agent/SWE-agent
- Inspected code: `sweagent/agent/agents.py`

Relevant implementation pattern:

- The agent uses a carefully designed agent-computer interface.
- Each step records action, observation, response, thought, execution time,
  state, and trajectory.
- The runtime saves trajectory files so failures can be replayed.

What we borrow:

- Event trajectory as a first-class artifact.
- Action/observation style logging for agent/tool interactions.
- Error handling and requery loops should be recorded, not hidden.

What we do not borrow directly:

- A software patch loop. Our loop must reason about stream, beat, memory,
  numeric, timing, and board evidence, not only repository edits.

SpatialAccAgent impact:

- Each team run now writes `<stage>/team/event_log.jsonl` with plan,
  parallel-group, subtask start/finish, failure, and aggregate events.

### ChatDev

Sources:

- Paper/code: https://github.com/OpenBMB/ChatDev
- Inspected code:
  `workflow/graph.py`, `workflow/runtime/execution_strategy.py`,
  `schema_registry/registry.py`

Relevant implementation pattern:

- Workflows are represented as explicit graphs/runtimes rather than a single
  monolithic prompt.
- Schema registry and runtime strategies separate workflow definition from
  execution.

What we borrow:

- Stage graph / workflow runtime thinking.
- Structured schema boundaries.

What we do not borrow directly:

- Software-company role metaphors as a paper contribution. Our metaphor is a
  chip design team, and the concrete contribution is constraint-state design
  closure.

SpatialAccAgent impact:

- Existing top-level stages remain unchanged, but `stage_team.py` now executes
  subagents by `parallel_group`: independent specialists first, auditor/gate
  roles after them when needed.

### Agentless

Sources:

- Code: https://github.com/OpenAutoCoder/Agentless
- Inspected code directories:
  `agentless/fl/`, `agentless/repair/`

Relevant implementation pattern:

- A relatively simple pipeline with localization and repair can be competitive
  with heavier agent loops.
- Deterministic retrieval/localization and patch reranking are useful controls
  against agent drift.

What we borrow:

- Keep deterministic checkers and structured localization central.
- Do not add more agents where a checker or static contract is enough.

What we do not borrow directly:

- "Agentless" as a philosophy. Our framework is agentic, but agents are
  constrained by SACG and checker evidence.

SpatialAccAgent impact:

- The implementation deliberately remains a small extension of the existing
  team layer instead of adopting a large external runtime.

### OpenHands

Sources:

- Code: https://github.com/OpenHands/OpenHands
- Inspected directories: `openhands/server/`

Relevant implementation pattern:

- Modern coding agents separate server/runtime concerns from agent logic and
  persist runtime events.

What we borrow:

- Event-sourced runtime thinking and reproducible handoff records.

What we do not borrow directly:

- A full interactive software-agent server. It would be too heavy for the
  current minimal SpatialAccAgent prototype.

SpatialAccAgent impact:

- We add local JSONL event logs, not a new service.

### Voyager

Sources:

- Code: https://github.com/MineDojo/Voyager
- Inspected directories: `voyager/agents`, `voyager/prompts`,
  `voyager/voyager.py`

Relevant implementation pattern:

- Long-horizon agents benefit from skill libraries and self-improving
  curricula.

What we borrow later, not now:

- A reusable skill/template library for verified accelerator transformations.

Current decision:

- Do not add an auto-growing skill library yet. The current trusted Chisel
  template library and SACG constraints are the safer minimal substrate.

## 3. Hardware and EDA Agent Systems

### MAGE

Sources:

- Local paper:
  `docs/papers/Zhao 等 - 2024 - MAGE A Multi-Agent Engine for Automated RTL Code Generation.pdf`
- Code link from paper:
  https://github.com/stable-lab/MAGE-A-Multi-Agent-Engine-for-Automated-RTL-Code-Generation

Relevant pattern:

- Multi-agent division among RTL generation, testbench generation, judge, and
  debug agents.
- Simulation-based scoring and Verilog-state checkpoint feedback provide more
  precise repair evidence than final output mismatch.

What we borrow:

- Hardware agent teams need role specialization.
- State/evidence checkpoints are more useful than raw logs.

What we do not borrow directly:

- High-temperature RTL candidate sampling is risky for a resource-constrained
  FPGA spatial accelerator flow. We need template-bound generation.

SpatialAccAgent design implication:

- Our equivalent of a Verilog-state checkpoint is SACG-bound evidence:
  stream traces, beat counts, DDR layout checks, numeric comparisons, liveness
  checks, and backend reports.

### RTLSquad

Sources:

- Local paper:
  `docs/papers/Wang 等 - 2025 - RTLSquad Multi-Agent Based Interpretable RTL Design.pdf`

Relevant pattern:

- Exploration, implementation, and verification/evaluation squads.
- Inner loop for functional fixes and outer loop for PPA exploration.
- Decision paths are an explicit output for engineer trust.

What we borrow:

- Team roles should produce structured decision paths.
- Verification/evaluation must feed back into the next stage.

What we do not borrow directly:

- Natural-language decision paths alone are insufficient for our paper claim.
  We need machine-checkable SACG constraints and evidence.

SpatialAccAgent design implication:

- `event_log.jsonl`, `team_aggregate.json`, and stage reports form the decision
  path, but final trust comes from checkers/tool evidence.

### GPT4AIGChip

Sources:

- Local paper:
  `docs/papers/Fu 等 - 2025 - GPT4AIGChip Towards Next-Generation AI Accelerator Design Automation via Large Language Models.pdf`

Relevant pattern:

- AI accelerator design requires decomposition, templates, and hardware-aware
  prompting because LLMs lose long dependencies and hardware details.

What we borrow:

- Decompose accelerator generation around reusable templates and hardware
  design constraints.

What we do not borrow directly:

- One-shot prompt-to-design. Our method is stage-gated and evidence-bound.

SpatialAccAgent design implication:

- Code generation remains template-bound Chisel package generation, not free
  RTL generation.

### Design Conductor 2.0

Sources:

- arXiv: https://arxiv.org/abs/2605.05170
- Local paper:
  `docs/papers/Team 等 - 2026 - Design Conductor 2.0 An agent builds a TurboQuant inference accelerator in 80 hours.pdf`

Relevant pattern:

- Long-horizon multi-agent chip design is becoming feasible.
- The paper reports a frontier-model harness building several designs,
  including an LLM inference accelerator mapped to FPGA, with verification,
  system simulation, and backend considerations.
- It also highlights that chips differ from software because verification and
  physical implementation risk dominate.

What we borrow:

- The chip-design-team framing is credible.
- Backend and board closure must be part of the story.

What we do not claim:

- We are not claiming "first agent to build an accelerator" or broad
  autonomous chip construction.

SpatialAccAgent design implication:

- Our novelty should be domain-specific: SACG-controlled, checker-verified
  design closure for LLM spatial accelerators.

## 4. Method Update: SACG-Controlled Design Team

The updated method can be described as:

```text
SACG-Controlled Design Team (SCDT)
```

It adds a team layer to each stage:

```text
stage artifact + SACG state
-> team_decomposer
-> role-specialized subtasks
-> grouped parallel execution
-> typed handoff contracts
-> event trajectory
-> aggregate observations/risks/actions
-> stage report / SACG validation
```

The important distinction from generic multi-agent systems:

```text
Agents do not own the design state.
SACG owns the design state.
Agents propose bounded observations/actions over SACG constraints.
Checkers and tool evidence decide promotion.
```

## 5. Minimal Implementation Added

The current framework update is intentionally small and contained in
`accagent/framework/stage_team.py`.

New mechanisms:

- `ROLE_CATALOG`: maps chip-design roles to capabilities and constraint focus.
- `role_profile`: each subtask records a role family and capabilities.
- `action_type`: each subtask states what kind of design action it performs.
- `handoff_contract`: each subtask declares consumed constraints/artifacts,
  produced fields, handoff targets, and evidence rule.
- `acceptance_checkers`: each subtask is linked to checker classes such as
  `sacg_static_check`, `template_binding_static_check`,
  `stream_trace_check`, `beat_count_check`, `addr_map_check`,
  `numeric_compare`, `codegen_package_static_check`,
  `backend_package_static`, or `real_tool_evidence_check`.
- `parallel_group`: subagents in the same group run in parallel; later groups
  run after earlier groups. This supports independent specialists followed by
  auditors/evidence gates.
- `event_log.jsonl`: each team run records plan creation, group execution,
  subtask start/finish/failure, and aggregate write events.

Files generated per stage now include:

```text
<stage>/team/decomposer_prompt.md
<stage>/team/decomposer_result.json
<stage>/team/subtask_plan.json
<stage>/team/team_aggregate.json
<stage>/team/event_log.jsonl
```

This is enough to support the user's requested behavior:

- automatic subtask recognition and decomposition;
- adaptive use of multi-agent execution when useful;
- multiple role-specialized subagents;
- parallel execution when subtasks are independent;
- stage-wide coverage, because every stage calls the team layer;
- tight alignment with the paper problem definition.

## 6. Why This Is the Right Minimal Step

This update is smaller than importing MetaGPT, AutoGen, OpenHands, or ChatDev,
but it keeps the proven patterns that matter:

- MetaGPT-like roles/SOP;
- AutoGen-like handoff contracts;
- SWE-agent/OpenHands-like event trajectory;
- ChatDev-like workflow structure;
- MAGE/RTLSquad-like hardware team specialization;
- Agentless-like restraint: keep deterministic checkers central.

It avoids the main risks:

- no new heavyweight runtime;
- no uncontrolled agent-to-agent chat memory;
- no free-form RTL generation;
- no unverified backend/board pass claim;
- no drift from the SACG-centered paper story.

## 7. Next Research/Implementation Steps

Near-term:

- Run a formal `mode=gpt,enforce=true` experiment and archive all team
  decomposer/subagent outputs.
- Add checker-specific evidence IDs into `acceptance_checkers`, so each
  subtask can point to exact SACG invariants.
- Add a small paper table showing which stages split and which stayed atomic.

Medium-term:

- Extend the trusted template library for Qwen/LLaMA-style GQA/RoPE/gated MLP.
- Add fault-injection experiments for stream order, beat count, DDR layout,
  valid-delay, numeric-scale, and backend timing-fix bugs.
- Compare against no-team, no-SACG, template-only, and stage-local-verification
  baselines.

Non-goals for now:

- Do not build an independent multi-agent chat server.
- Do not add automatic prompt-evolved workflow search.
- Do not let agents write arbitrary RTL outside trusted templates.
