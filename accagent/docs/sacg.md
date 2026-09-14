# Spatial Accelerator Constraint Graph

## 0. Document Purpose

This document defines **Spatial Accelerator Constraint Graph (SACG)** as the core technical mechanism of SpatialAccAgent.

SpatialAccAgent solves the **Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design**:

> when an LLM agent transforms a decoder-only LLM block into FPGA accelerator artifacts, the constraints across model semantics, spatial pipeline, Chisel/RTL modules, stream protocol, DDR/AXI layout, runtime configuration, verification traces, backend reports, and board evidence are implicit and fragile. Once these constraints drift, failures become hard to detect, localize, and repair.

SACG is the explicit design state used to prevent that drift.

The key claim is:

> SpatialAccAgent does not trust chat history, local code generation, or raw tool logs as the design state. It maintains a Spatial Accelerator Constraint Graph that binds model semantics, templates, pipeline edges, generated artifacts, checker evidence, and repair decisions into one checkable and repairable state.

This document intentionally uses **Constraint Graph** rather than the older **Contract Graph** terminology. The older word "contract" can still appear inside legacy notes, but the paper and new framework should use **constraint** consistently.

---

## 1. Why SACG Is the Core Method

The problem definition says that a deployable LLM spatial accelerator is not a single RTL artifact. It is a package of mutually dependent objects:

```text
model config
-> operator semantics
-> numeric policy
-> template selection
-> pipeline plan
-> Chisel modules
-> top-level stream connection
-> RTL traces
-> DDR image
-> AXI wrapper
-> host runtime
-> stage/top/system verification
-> synthesis/implementation reports
-> board logs
-> repair history
```

Each object carries assumptions that must remain consistent with the others.

Examples:

- `num_heads`, `num_kv_heads`, and `head_dim` must agree across model config, QKV template parameters, attention stream order, KV-cache layout, DDR packing, and runtime buffer offsets.
- W4/W8 scale layout must agree across quantization policy, DDR image builder, RTL address generator, and numeric checker.
- `valid`, `ready`, `st`, `last`, address, and data must represent the same beat order at producer, consumer, trace parser, top-level harness, and board runtime.
- A timing repair that inserts a register must also update valid delay, residual bypass, output strobe, and checker expectations.

Without SACG, these assumptions live in natural language, code comments, scattered scripts, and human memory. A normal agent sees only local files and latest logs, so it tends to make symptom-driven local patches.

SACG converts hidden assumptions into explicit graph objects.

---

## 2. Formal Definition

SACG is defined as:

```text
G = (V, E, C, I, A)
```

Where:

- `V` is the set of design entities.
- `E` is the set of cross-entity relations.
- `C` is the set of constraints attached to nodes and edges.
- `I` is the set of invariants that must hold across graph transformations.
- `A` is the set of artifacts bound to graph elements.

SpatialAccAgent maintains runtime state:

```text
S_t = (G_t, A_t, R_t)
```

Where:

- `G_t` is the current SACG.
- `A_t` is the current artifact set and freshness state.
- `R_t` is the current checker evidence, reports, repair records, and approvals.

Every meaningful agent action is a transition:

```text
S_t --action--> S_{t+1}
```

An action is valid only if it declares which constraints it touches and is supported by checker or tool evidence.

---

## 3. What SACG Adds Beyond Existing State Forms

SACG is not just another schema. It fills the gap between three incomplete state forms.

### 3.1 Beyond Compiler IR

Compiler IR can represent tensor shapes, layouts, schedules, and sometimes stream/dataflow types. That is useful but not enough for agentic design closure.

SACG extends beyond compiler IR to include:

- model documents and configuration;
- Chisel template specs;
- generated RTL;
- trace formats;
- DDR images;
- runtime buffer maps;
- verification tasks;
- synthesis and implementation reports;
- board logs;
- repair history;
- human approvals.

Thus SACG is not a replacement for compiler IR. It is a design-state layer around heterogeneous accelerator artifacts.

### 3.2 Beyond Natural-Language Agent Context

Agent memory and discussion logs are readable, but not executable. They do not reliably answer:

- which stream edge lost a beat;
- which numeric scale belongs to which memory region;
- which generated file implements a specific model constraint;
- which repair restored which invariant;
- which checker evidence supports the claimed root cause.

SACG gives these facts stable IDs and typed links.

### 3.3 Beyond Raw EDA Reports

EDA reports and simulation logs are evidence, not design state. They show symptoms such as mismatch, timeout, wrong address, or timing violation.

SACG maps these symptoms back to:

- graph nodes;
- graph edges;
- violated constraints;
- affected artifacts;
- allowed repair scopes;
- required regressions.

---

## 4. Graph Objects

### 4.1 Node Types

Nodes represent design entities that carry constraints or produce artifacts.

Initial node types:

| Node type | Meaning | Examples |
| --- | --- | --- |
| `model_op` | model-level operator or semantic block | QKV projection, RoPE, attention, MLP, residual |
| `template` | trusted Chisel template and template spec | Linear, Softmax, FIFO, DDR reader |
| `processing_unit` | instantiated compute unit | QKVLinear, DM1, DM2, FFNUp |
| `pipeline_stage` | spatial pipeline stage | stage 1 LayerNorm, stage 2 QKV |
| `stream_adapter` | reorder, queue, converter, handshake adapter | FIFO, layout converter |
| `memory_task` | DDR or on-chip memory operation | weight preload, KV-cache read |
| `runtime_task` | host/runtime interaction | config load, buffer map, start/done |
| `verification_task` | checker or testbench task | stage test, top test, system test |
| `backend_task` | synthesis/implementation/timing task | Vivado synth, route, report parse |
| `deployment_task` | board-level run and benchmark | bitstream load, board smoke |

Two node types are especially important for the new framework:

- `template` nodes prevent the agent from treating Chisel as free-form code.
- `verification_task` and `backend_task` nodes make evidence first-class graph objects instead of after-the-fact logs.

### 4.2 Edge Types

Edges represent relationships where cross-layer consistency can break.

Initial edge types:

| Edge type | Meaning | Typical failure |
| --- | --- | --- |
| `model_semantic` | semantic dependency between model ops | GQA treated as MHA |
| `shape` | tensor/tile compatibility | hidden/head/tile mismatch |
| `numeric` | dtype, scale, bias, rounding relation | wrong scale stride |
| `stream` | producer-consumer stream order | token/head/beat order mismatch |
| `beat` | valid/ready/st/last transaction count | missing or extra beat |
| `memory_layout` | DDR/on-chip layout and address generation | wrong base/stride/packing |
| `control` | start/done/config/control sequencing | early start or stale config |
| `residual` | residual path alignment | data/control not same beat |
| `kv_cache` | KV storage and reuse relation | wrong KV-head mapping |
| `liveness` | bounded progress and FIFO behavior | deadlock or permanent stall |
| `runtime` | host/runtime field mapping | wrong buffer offset |
| `backend` | timing/resource constraints and RTL assumptions | timing fix breaks valid delay |
| `deployment` | board integration and observable status | board runs but status mapping wrong |

The important design decision is that edges are not only model graph edges. A DDR image to RTL address-generator relationship is also an edge. A runtime config field to AXI register field is also an edge. A timing repair to valid-alignment relation is also an edge.

---

## 5. Constraint Classes

Each node or edge can carry one or more constraints. These constraints are the units that checkers verify and repairs restore.

### 5.1 Model and Shape Constraints

Model constraints preserve architecture semantics:

- block style: OPT/GPT, LLaMA, Qwen, Gemma;
- attention type: MHA, GQA, MQA;
- normalization type: LayerNorm or RMSNorm;
- activation type: GELU, SiLU, SwiGLU;
- residual and attention dependency;
- causal mask and prefill/decode behavior.

Shape constraints preserve dimensions and tiling:

- hidden size;
- FFN size;
- sequence length;
- head count;
- KV-head count;
- head dimension;
- tile size;
- lane count;
- beat count;
- buffer depth required by the schedule.

These constraints answer:

> Does the generated pipeline still implement the intended model structure and dimensions?

### 5.2 Numeric Constraints

Numeric constraints preserve quantization and arithmetic behavior:

- activation dtype;
- weight dtype;
- accumulation dtype;
- output dtype;
- scale layout;
- zero-point;
- bias domain;
- rounding;
- saturation;
- tolerance policy;
- exact-vs-tolerated comparison rule.

These constraints answer:

> Is a mismatch a legal numeric difference or a broken numeric/memory/stream assumption?

### 5.3 Template-Binding Constraints

Template-binding constraints connect model operations to trusted Chisel templates.

They record:

- which template implements which model op;
- supported parameter ranges;
- bound parameters;
- template IO semantics;
- allowed agent edits;
- forbidden agent edits;
- required tests;
- expected latency and initiation behavior.

These constraints are essential because SpatialAccAgent is template-constrained. The agent should not freely rewrite hardware. It should select templates, bind parameters, generate glue code, and only perform bounded repairs.

### 5.4 Stream and Beat Constraints

Stream constraints preserve producer-consumer order:

- token order;
- head order;
- tile order;
- lane order;
- beat order;
- data/address/strobe alignment;
- reorder/converter semantics.

Beat constraints preserve valid transaction count and boundaries:

- expected number of fired beats;
- `st` rule;
- `last` rule;
- `ready/valid` fire condition;
- valid delay across pipeline registers;
- output window size.

These constraints answer:

> Are the same logical tokens, heads, lanes, and beats seen by producer, consumer, trace, checker, and runtime?

### 5.5 Memory and Runtime Constraints

Memory constraints preserve storage layout:

- DDR base address;
- region size;
- stride;
- bank;
- burst length;
- packing;
- alignment;
- address coverage;
- disjointness.

Runtime constraints preserve host/hardware agreement:

- runtime buffer map;
- config register layout;
- input/output window offsets;
- start/done/status semantics;
- board-visible counter/status mapping.

These constraints answer:

> Does system-level execution read and write the same data that stage/top-level verification assumed?

### 5.6 Liveness Constraints

Liveness constraints preserve bounded progress:

- max cycles per stage/token/layer;
- max stall cycles per stream edge;
- FIFO occupancy range;
- producer-consumer rate envelope;
- no permanent ready/valid deadlock.

These constraints answer:

> Can the pipeline continue to make progress under legal inputs?

### 5.7 Backend and QoR Constraints

Backend constraints preserve implementation assumptions:

- timing target;
- resource budget;
- clock domain;
- false-path assumptions;
- synthesis/implementation script assumptions;
- allowed backend-only fix scope;
- RTL changes required by timing repair.

QoR constraints record measurable performance/resource targets:

- latency cycles;
- throughput;
- DSP count;
- BRAM/URAM usage;
- LUT/FF usage;
- Fmax/timing slack;
- DDR bandwidth.

These constraints answer:

> Did a local optimization or timing repair preserve functional semantics and produce credible QoR?

---

## 6. SACG and Template-Based Design

The new framework is template-constrained, so SACG must represent template binding explicitly.

The flow is:

```text
model op
-> candidate templates
-> selected template
-> bound parameters
-> generated Chisel instance
-> top-level connection
-> verification artifacts
```

At each step, SACG records a constraint update.

Example:

```text
model_op.qkv
  requires: hidden=768, heads=12, q/k/v output shapes

template.linear_qkv_int8
  supports: hidden divisible by lane, int8 weights, int32 accumulation

binding.qkv
  binds: hidden=768, lane=12, row/col/tile parameters, q/k/v scale artifacts

artifact.QKVLinear.scala
  implements: binding.qkv

edge.qkv_to_attention
  requires: token-head-beat stream order and exact beat count
```

This makes the agent's generation step checkable. The framework can ask:

- Is every model op covered by an approved template?
- Are all template parameters derived from model/numeric/platform constraints?
- Did generated Chisel preserve the template spec?
- Did top-level integration preserve template stream and control assumptions?
- Did verification artifacts use the same shape, scale, and layout assumptions?

Without these links, a template-based framework still risks becoming a collection of independent generated files.

---

## 7. SACG and Checker Evidence

SACG is useful only if it is executable. Each invariant must have at least one checker hook.

| Invariant | Checker hook | Evidence |
| --- | --- | --- |
| model/shape preserved | `shape-check` or `sacc-lint` | propagated dimensions and template parameters |
| numeric policy preserved | `numeric-check` | golden compare, scale/bias metadata |
| template binding valid | `template-spec-check` | template spec, bound parameters, generated module IO |
| stream order preserved | `stream-trace-check` | producer/consumer trace |
| beat count preserved | `beat-count-check` | valid/ready fire count, st/last trace |
| memory layout preserved | `addr-map-check` | DDR image metadata, RTL address trace |
| runtime map preserved | `runtime-map-check` | config/register/buffer map |
| bounded liveness | `deadlock-check` | timeout, FIFO occupancy, stall counters |
| backend assumptions preserved | `backend-report-check` | timing/resource reports |
| regression preserved | `regression-check` | stage/top/system pass matrix |

Checker reports must be bound back to graph elements:

```text
checker report
-> invariant
-> constraint
-> node/edge
-> artifact
-> repair candidate
```

This mapping is the key to violated-constraint localization.

---

## 8. SACG and Repair

A valid repair is not "change code until the test passes." It is:

```text
symptom
-> evidence
-> violated constraint
-> bounded patch
-> checker rerun
-> regression
-> state promotion
```

Repair records must distinguish:

- symptom;
- suspected root cause;
- confirmed root cause;
- violated constraint;
- affected nodes/edges;
- affected artifacts;
- patch;
- approval requirement;
- regression result;
- keep/revert decision.

### 8.1 Allowed Repair Scope

SACG determines whether a repair is local or requires human approval.

Usually auto-allowed:

- parameter synchronization;
- signal connection;
- script path;
- trace parser;
- wrapper/runtime field synchronization;
- valid delay correction;
- obvious address offset;
- DDR image regeneration;
- small FIFO depth adjustment;
- regression rerun.

Approval-required:

- pipeline stage change;
- tile size change;
- parallelism change;
- memory layout change;
- data packing change;
- numeric policy change;
- major template rewrite;
- adding pipeline stage for timing;
- AXI/DDR access plan change;
- major buffer structure change.

Forbidden:

- delete failing tests;
- modify golden output to pass;
- loosen tolerance without approval;
- change model semantics;
- treat GQA as MHA;
- bypass checker;
- mark failed regression as pass;
- claim confirmed root cause without evidence.

### 8.2 Why SACG Reduces Wrong-Layer Repair

Without SACG, the agent sees an output mismatch and may patch the nearest code.

With SACG, the agent must classify the failure through evidence:

| Symptom | SACG-guided question | Possible violated constraint |
| --- | --- | --- |
| stage pass, top fail | Which edge between passing stages changed semantics? | stream, beat, residual, numeric |
| top pass, system fail | Which memory/runtime edge is absent from stage/top tests? | memory layout, runtime map |
| output missing one beat | Which beat-count invariant failed? | beat count, valid delay, last rule |
| timing fix causes mismatch | Which backend transition touched stream alignment? | backend, pipeline alignment |
| numeric systematic bias | Which scale/bias/memory constraint changed? | numeric, memory layout |

This is how SACG directly addresses the paper problem.

---

## 9. SACG State Transition Protocol

Every framework action should follow this sequence:

```text
1. declare intent
2. identify touched nodes/edges/constraints
3. update or generate artifacts
4. mark dependent artifacts stale
5. run required checkers
6. collect typed evidence
7. localize violated constraints if failed
8. repair or request approval
9. rerun regression
10. promote or reject state
```

The minimum transition record should contain:

```yaml
transition_id:
action_type:
input_state:
output_state:
touched_nodes:
touched_edges:
touched_constraints:
artifacts_read:
artifacts_changed:
artifacts_generated:
stale_artifacts:
checker_runs:
evidence:
failures:
repair_record:
approval_required:
approval_id:
status:
```

The key rule:

> A file edit is not a design update until SACG knows which constraints it touched and which checker evidence validates it.

---

## 10. SACG in the Full SpatialAccAgent Flow

SACG is present from the beginning of the flow, not only after verification fails.

| Framework stage | SACG role |
| --- | --- |
| Task card | create task boundary and fixed design assumptions |
| Model extraction | create model, shape, numeric constraints |
| Template selection | bind model ops to approved template specs |
| Pipeline planning | create stream, residual, control, memory, liveness edges |
| Parameter binding | bind concrete Chisel parameters to constraints |
| Module generation | bind generated artifacts to nodes and constraints |
| Top integration | check edge-level stream, beat, residual, control constraints |
| Verification artifact generation | bind golden, trace, DDR image, runtime config to same constraints |
| Stage verification | check local node correctness |
| Top verification | check edge composition correctness |
| System verification | check memory/runtime/deployment consistency |
| Backend closure | check timing/resource repairs against pipeline semantics |
| Board run | bind deployment evidence back to system constraints |
| Repair | update touched constraints and rerun required regression |

This is the main difference between SpatialAccAgent and a debug assistant. The graph exists before failures, guides generation, receives evidence, and constrains repairs.

---

## 11. Failure Taxonomy Mapping

SACG should support the following failure taxonomy.

| Failure class | Typical violated constraints | Example |
| --- | --- | --- |
| `shape_model` | model, shape, template binding | GQA head mapping wrong |
| `numeric` | numeric, memory layout | scale stride or bias domain wrong |
| `stream_order` | stream, residual, KV-cache | producer tile order mismatches consumer |
| `beat_count` | beat, valid alignment | missing final beat |
| `memory_layout` | DDR layout, address generator, runtime map | DDR image packing differs from RTL address |
| `liveness` | FIFO, ready/valid, bounded progress | token stalls forever |
| `runtime_harness` | runtime, config, deployment | board config field wrong |
| `backend_repair` | backend, pipeline alignment | timing register breaks valid delay |

This mapping should be used by the evidence classifier and repair planner.

---

## 12. Minimum SACG v1 Scope

SACG v1 should be small enough to implement but strong enough to support the paper claim.

It must support:

- one target task card;
- template specs;
- model/shape/numeric constraints;
- stream/beat/memory/runtime/liveness/backend constraints;
- nodes and edges with stable IDs;
- artifact binding;
- checker report binding;
- repair record binding;
- approval record binding;
- stale artifact tracking;
- pass/fail/unknown status for invariants;
- transition records.

It should not initially attempt:

- full theorem proving;
- unrestricted tensor layout algebra;
- multi-model generalization;
- fully automatic architecture redesign;
- autonomous timing closure without approval;
- replacing EDA tools.

The first executable SACG should be YAML or JSON. A Python runtime can load it, validate it, append reports, and reject transitions that violate approval or evidence rules.

---

## 13. Paper-Level Contribution

The paper should present SACG as the central method contribution:

> SACG is an explicit, executable design state for agentic LLM spatial accelerator design. It links model semantics, template bindings, spatial pipeline edges, generated Chisel/RTL, verification artifacts, memory/runtime layout, backend evidence, and repair history. By forcing each agent action to declare touched constraints and by binding checker evidence back to graph invariants, SACG enables violated-constraint localization, invariant-directed minimal repair, hierarchical regression, and quantitative ablation.

The strongest novelty statement is:

> SACG moves LLM hardware agents from local artifact generation to constraint-guided design closure.

---

## 14. Next Documents

This document is the conceptual method design. It should be followed by:

```text
accagent/docs/sacg_schema_v1.md
accagent/docs/template_spec_v1.md
accagent/docs/checker_binding_v1.md
accagent/docs/transition_protocol_v1.md
accagent/docs/repair_protocol_v1.md
```

Then the executable framework code should be implemented under:

```text
accagent/framework
```

No framework implementation should rely on hidden chat memory. The runtime should operate on SACG files, artifacts, checker reports, and transition records.

