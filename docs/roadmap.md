# Roadmap

**ID:** DOC-002  
**Status:** Active  
**Last reviewed:** 2026-06-12

---

## Purpose

Define the phased delivery plan for AIOS. Each phase has explicit outcomes, deliverables, and exit criteria. Phases are sequential; later phases should not begin until exit criteria for the current phase are met.

## Phase status summary

| Phase | Title | Status |
|---|---|---|---|
| Phase 1 | Repository Bootstrap | ✅ Complete |
| Phase 2 | Architecture Baseline | ✅ Complete |
| Phase 3 | Knowledge Baseline | ✅ Complete |
| Phase 4 | Runtime and Workflow Baseline | ✅ Complete |
| Phase 5 | Identity Foundation | ✅ Complete |
| Phase 6 | Wyrd Foundation + Conductor MVP | ✅ Complete |
| Phase 7 | AI-Assisted Inference | ✅ Complete |
| Phase 8 | Governed Autonomy | ✅ Complete |

## Phases

### Phase 1 — Repository Bootstrap ✅ Complete

**Objective:** Establish a governed, navigable repository structure with a documented architecture baseline.

**Outcomes:**
- The repository communicates clear intent and structure to any future contributor or tool.
- All top-level governance artifacts are present and interlinked.
- The ADR process is active and used for significant decisions.

**Deliverables:**
- `README.md` — repository overview
- `docs/vision.md` — long-term vision
- `docs/roadmap.md` — this document
- `architecture/principles.md` — guiding principles
- `architecture/target-architecture.md` — layered architecture
- `architecture/capability-map.md` — capability domains
- `governance/governance-model.md` — governance framework
- `governance/autonomy-maturity-model.md` — autonomy stages
- `governance/traceability-standard.md` — traceability IDs and linking guidance
- `knowledge/knowledge-architecture.md` — knowledge strategy
- `ontology/minimal-viable-ontology.md` — core ontology
- `adr/README.md` — ADR process
- `adr/0001-bootstrap-repository-structure.md` — bootstrap decision record

**Exit criteria:**
- All deliverables present, internally consistent, and interlinked.
- At least one ADR exists and follows the defined format.
- No placeholder sections remain without explicit "TBD" markers and tracking issues.

---

### Phase 2 — Architecture Baseline ✅ Complete

**Objective:** Produce a complete, stable architecture baseline that is sufficient to govern near-term implementation decisions.

**Outcomes:**
- All major capability areas are defined with clear boundaries.
- Traceability IDs are assigned consistently across the baseline.
- A glossary of core terms is established.

**Deliverables:**
- ✅ Expanded `architecture/capability-map.md` with capability-to-layer mapping
- ✅ `docs/glossary.md` — core terminology (DOC-011)
- ✅ ADR-002: model gateway pattern
- ✅ ADR-003: knowledge persistence approach
- ✅ ADR-004: identity model
- ✅ Reviewed and updated `architecture/target-architecture.md`

**Exit criteria:**
- All architecture documents are cross-referenced and internally consistent.
- At least three ADRs exist covering decisions in different domains.
- No open "needs decision" items in the architecture baseline.

---

### Phase 3 — Knowledge Baseline ✅ Complete

**Objective:** Establish the knowledge platform with ingestion, storage, retrieval, and lifecycle governance.

**Outcomes:**
- A working local knowledge store exists.
- Knowledge assets can be created, versioned, and retrieved with provenance.
- The minimal viable ontology is implemented in the knowledge store schema.

**Deliverables:**
- ✅ `platform/knowledge/` — knowledge platform implementation
- ✅ Ingestion pipeline for at least one document format
- ✅ Retrieval interface (not necessarily AI-powered at this stage)
- ✅ Backup and restore capability for the knowledge store
- *(ADR-003 — knowledge persistence approach already accepted in Phase 2)*

**Exit criteria:**
- ✅ Knowledge assets can be created, stored, retrieved, and versioned.
- ✅ Provenance metadata is captured for all ingested assets.
- ✅ Backup and restore procedures are documented and tested.

---

### Phase 4 — Runtime and Workflow Baseline 🔄 Active

**Objective:** Introduce a governed workflow runtime capable of executing bounded, inspectable workflows.

**Outcomes:**
- Workflows can be defined, triggered, executed, and audited.
- All workflow actions are traceable to a documented capability.
- The model gateway mediates all AI model access.

**Deliverables:**
- ✅ `platform/model-gateway/` — model gateway implementation
- ✅ `platform/workflow-runtime/` — workflow runtime implementation
- ✅ `workflows/` — initial workflow definitions (WF-001, WF-002)
- ✅ Workflow audit log (run records in `platform/workflow-runtime/runs/`)
- ✅ ADR-005 — workflow engine technology selection
- ✅ ADR-006 — model gateway technology selection

**Exit criteria:**
- At least two end-to-end workflows execute successfully and are auditable.
- All model calls flow through the gateway.
- Workflow definitions are validated against capability map.

---

### Phase 5 — Identity Foundation ✅ Complete

**Objective:** Establish the persistent identity and observation infrastructure that underpins all executive function capabilities.

**Outcomes:**
- A persistent Persona store exists with declared operator facts, preferences, and values.
- Observations are captured through automatic, manual, and scheduled mechanisms.
- Projects, commitments, goals, and focus areas are first-class entities with lifecycles.
- The naming collision between PROJ (platform delivery) and PRJ (personal project) is resolved.
- Personal data governance domain is defined, including retention, access, and canonical/derived policies.

**Deliverables:**
- `platform/knowledge/persona/` — Persona store (file-based, ADR-003 pattern)
- `platform/knowledge/observations/` — Observation store with multi-layer capture (ADR-008)
- `platform/knowledge/projects/` — Project and commitment stores
- `platform/knowledge/goals/` — Goal and focus area stores
- Personal data governance policy (extends DOC-006)
- ADR-007 (Identity as Domain Object), ADR-008 (Observation Store Architecture)

**Exit criteria:**
- ✅ Persona store is populated with operator-declared facts.
- ✅ Observations are flowing from at least one automatic capture source (git).
- ✅ Projects and commitments have defined lifecycles and are queryable.
- ✅ Personal data governance policy is documented and reviewed.
- ✅ ADR-007 and ADR-008 are accepted and referenced in the capability map.

---

### Phase 6 — Wyrd Foundation + Conductor MVP ✅ Complete

**Objective:** Two parallel tracks. Track A closes the Wyrd structural work defined in ADR-012. Track B delivers the Conductor (ADR-013) — the interactive layer that gives AIOS immediate daily utility.

**Why two tracks in one phase:** Wyrd provides the identity context that makes the Conductor genuinely useful. Both are needed for Phase 6 to be complete. The Wyrd structural work is smaller (~days); the Conductor is the primary effort.

---

#### Track A — Wyrd Foundation

**Objective:** Establish `wyrd/` as a named, explicitly bounded subsystem. Reorganise identity and capture code. Build goal and focus area stores.

**Outcomes:**
- The `wyrd/` subsystem exists with a clear README and boundary definition (ADR-012)
- All identity, persona, observation, project, commitment, goal, and focus area code lives under `wyrd/`
- `platform/executive-daemon/` contains only inference engine and daemon lifecycle code
- GoalStore and FocusAreaStore are operational and CLI-queryable

**Deliverables:**
- `wyrd/` directory scaffold and README (DOC-019)
- `wyrd/src/project_store.py` — moved from `platform/executive-daemon/`
- `wyrd/src/goal_store.py` — GoalStore (GL-NNN) and FocusAreaStore (FCA-NNN)
- `wyrd/src/capture/` — moved from `platform/executive-daemon/`
- `wyrd/schema/` — moved and extended schemas
- CLI: `aios goal add/list/show`, `aios focus add/list`

**Track A exit criteria:**
- `wyrd/` directory exists; all tests pass after moves
- GoalStore and FocusAreaStore built and queryable
- `platform/executive-daemon/` contains no identity store code

---

#### Track B — Conductor MVP

**Objective:** Build a local, conversational interface that the operator can use today to research, plan, and get assistance — with context from Wyrd injected into every call.

**Outcomes:**
- The operator can open a browser, type a question or instruction, and receive a useful response
- The conductor has context about the operator's persona, active projects, and recent observations
- Conductor sessions are persisted as YAML and session turns become observations
- Research, plan, and summarise tools are functional

**Deliverables:**
- `platform/conductor/` — new module (DOC-020)
- `src/session.py` — conversation session management (YAML persistence, ADR-003)
- `src/context.py` — Wyrd context assembly for every model call
- `src/dispatch.py` — intent classification and tool routing
- `src/tools/` — research, plan, summarise tools
- `src/api.py` — FastAPI HTTP endpoint (localhost)
- `web/index.html` — minimal chat UI
- ADR-013 accepted and referenced

**Track B exit criteria:**
- Conductor HTTP server starts and serves the web UI
- Operator can send a message and receive a model-backed response
- Context injection is verified: persona and active projects appear in model call context
- Session is persisted after conversation
- Session turns are recorded as observations in the Wyrd store
- At least 25 tests passing

---

**Phase 6 combined exit criteria (✅ met):**
- All Track A and Track B exit criteria met
- ADR-012 and ADR-013 both accepted
- All documentation consistent (capability map, target architecture, traceability, glossary)
- No broken traceability links

---

### Phase 7 — AI-Assisted Inference ✅ Complete

**Objective:** Activate the scheduled AI inference layer (ADR-009 Layer 2, ADR-011) and complete the feedback loop between operator review and the learning engine. Move the system from pattern detection to genuine operator understanding.

**Outcomes:**
- The learning engine runs on a scheduled cycle, calling the model gateway (ADR-002) to analyse aggregated observations.
- Detected patterns, contradictions, and predictions are surfaced via the Wyrd review interface (built in Phase 6).
- Operator feedback flows back into confidence scoring and adjusts pattern type weighting.
- The reconciliation engine surfaces tensions between declared values and observed behaviour.
- Predictions self-evaluate when their window closes, and source pattern confidence is updated.
- No learning engine output modifies the canonical persona without operator review and approval.

**Deliverables:**
- ✅ `platform/executive-daemon/src/learning_engine.py` — `LearningEngine`: aggregated observation analysis, pattern type evaluation, contradiction/prediction generation, feedback confidence adjustment
- ✅ `platform/executive-daemon/src/daemon.py` — `AiInferenceRunner`: scheduled cycle (configurable interval), calls model gateway, governed by ADR-009 Layer 2 rules
- ✅ `platform/executive-daemon/src/stores.py` — `PredictionStore`, `FeedbackHistoryStore`, `ObservationStore.observations_in_range()` for temporal queries
- ✅ `platform/executive-daemon/src/daemon_state.py` — `PredictionScheduler`: tick-based TTL expiry evaluation, self-evaluation at prediction window close
- ✅ `platform/conductor/src/dispatch.py` — reduced redundancy, shared path resolution
- ✅ CLI (`platform/executive-daemon/src/cli.py`) — inspect patterns, predictions, feedback per session
- ✅ 83 new tests across daemon_state, learning_engine, stores modules (123 exec-daemon tests total)
- ADR-011 is fully reflected in the target architecture and capability map.

**Exit criteria (✅ met):**
- At least one pattern type is detected, surfaced, reviewed by the operator, and confidence updated from feedback.
- At least one prediction has been generated and self-evaluated (confirmed or refuted).
- Confidence scoring is deterministic and auditable: any pattern's score is reproducible from the same inputs.
- No learning engine output has modified the canonical persona without operator approval.
- ADR-011 is fully reflected in the target architecture and capability map.

---

### Phase 8 — Governed Autonomy ✅ Complete

**Objective:** Deliver agentic task execution with role-based tool access, governed by operator review at defined checkpoints. Progress through autonomy maturity stages (Stage 1 → Stage 2) under explicit governance.

Phase 8 is structured as six sequential steps, each delivering a discrete capability increment:

---

#### Step 1 — Agent Tool Interface ✅ Complete (ADR-014)

**Objective:** Define and implement a governed tool interface protocol for agent actions.

**Outcomes:**
- Four action primitives: read_file, write_file, run_shell, web_search
- All tool calls flow through a deterministic rules check (ADR-009 two-layer model)
- Write_file requires operator confirmation gate (Principle 8)
- All tool actions are logged to observations with source_mechanism: "tool"

**Deliverables:**
- ✅ `platform/conductor/src/tools/base.py` — `BaseTool` abstract class, `ToolResult` + `ToolCall` dataclasses
- ✅ `platform/conductor/src/tools/read_file.py` — path-restricted file reader (blocks `../` traversal)
- ✅ `platform/conductor/src/tools/write_file.py` — path-restricted writer; `REQUIRES_CONFIRMATION = True`
- ✅ `platform/conductor/src/tools/run_shell.py` — output-only; blocks interactive commands; configurable timeout
- ✅ `platform/conductor/src/tools/web_search.py` — DuckDuckGo search via `duckduckgo_search` library; read-only
- ✅ `platform/conductor/src/tools/registry.py` — `ToolRegistry` + `ToolExecutor`: param validation (JSON Schema), role enforcement, confirmation gate, audit logging
- ✅ `platform/conductor/src/tools/execute.py` — single-step execute: model selects tool+params, executor runs it
- ✅ ADR-014 accepted and referenced

---

#### Step 2 — Single-Agent ReAct Loop ✅ Complete

**Objective:** Implement a governed reasoning-observing-acting loop for single-goal task pursuit.

**Outcomes:**
- Agent pursues a goal through repeated reasoning and tool use (max 20 steps)
- Step history is tracked and fed back into each model call
- Role-based tool descriptions are filtered per agent role
- Parse errors and tool failures are recovered without crashing the loop

**Deliverables:**
- ✅ `platform/conductor/src/react.py` — `ReactRunner`: ReAct loop with `_find_json_object()`, `_parse_react_response()`, role-filtered tool descriptions, step history formatting
- ✅ 12 tests covering tool_call/final/parse_error/failure/unknown action/max steps/role enforcement

---

#### Step 3 — Task State Persistence ✅ Complete

**Objective:** Persist task lifecycle — creation, steps, status transitions, results — as durable derived state.

**Outcomes:**
- Tasks are stored as YAML-per-entity at `platform/knowledge/tasks/TSK-*.yaml`
- Each task tracks its goal, role, session_id, status, steps (action + tool + params + observation), and result
- ID format: `TSK-YYYY-MMDD-NNN` (same pattern as SES, OBS, PRD)

**Deliverables:**
- ✅ `platform/conductor/src/task_store.py` — `TaskStore`: CRUD, `next_id()`, `add_step()`, `update_status()`, `set_result()`
- ✅ `make_task()` and `make_step()` factory functions
- ✅ 21 tests covering ID generation, create/get/list/add_step/update_status/set_result

---

#### Step 4 — Agent Role Definitions ✅ Complete (ADR-015)

**Objective:** Define declarative agent roles with explicit tool access boundaries.

**Outcomes:**
- Three roles: researcher (read + web), coder (read + write + shell), synthesizer (read only)
- Role definitions are YAML files — inspectable, versionable, addable without Python changes
- Tool executor double-checks role allowlist + forbidden list on every call

**Deliverables:**
- ✅ `platform/conductor/agents/researcher.yaml` — allowed: read_file, web_search
- ✅ `platform/conductor/agents/coder.yaml` — allowed: read_file, write_file, run_shell
- ✅ `platform/conductor/agents/synthesizer.yaml` — allowed: read_file only
- ✅ `platform/conductor/src/agents.py` — `RoleRegistry`: `reload()`, `get()`, `list_roles()`, `validate_tool_access()`
- ✅ ADR-015 accepted and referenced

---

#### Step 5 — Conductor as Orchestrator ✅ Complete (ADR-016)

**Objective:** Decompose multi-part goals into steps and route each to the appropriate agent role.

**Outcomes:**
- Complex goals are decomposed into a plan (sequence of step + role pairs)
- Each step is executed sequentially via the Step 2 ReAct loop
- If a step fails, the plan enters a blocked state for operator review
- All step results are accumulated into a final outcome

**Deliverables:**
- ✅ `platform/conductor/src/orchestrator.py` — `PlanOrchestrator`: `decompose()`, `create_plan()`, `execute_plan()`, `get_plan()`, `list_plans()`
- ✅ `PlanStore` — YAML-per-entity at `platform/knowledge/plans/PLN-*.yaml`
- ✅ `conductor.py` — `create_plan()`, `execute_plan()`, `get_plan()`, `list_plans()` methods
- ✅ ADR-016 accepted and referenced
- ✅ 21 orchestrator tests + 1 full-pipeline smoke test
- ✅ 211 unit tests across conductor module (212 as of parser fix)

---

#### Step 6 — End-to-End Agent Task Execution ✅ Complete

**Objective:** Validate the full agent tool chain against a real model on actual work — not just in tests.

**Outcomes:**
- A real multi-role task executes end-to-end: researcher gathers sources, coder writes output
- Context from earlier steps flows into later steps (step result injection)
- All model reliability issues with structured output are identified and handled

**Deliverables:**
- ✅ Context passing: prior step results injected into subsequent step's ReAct prompt
- ✅ Confirmation gate wired through `Conductor.__init__()` as a callable
- ✅ Real end-to-end task executed and verified: researcher searches web for "Python history", coder saves findings to file (qwen2.5:7b, 2 steps, 2 minutes)
- ✅ Model reliability fix: multiline JSON answers with literal newlines now parse correctly via `_escape_newlines_in_strings()` fallback
- ✅ Web search switched from DDG Instant Answer API to `duckduckgo_search` library — returns real web results instead of empty infoboxes
- [Deferred] Confirmation gate in `Conductor.chat()` web flow — exists as `__init__` parameter, not wired into web UI
- [Deferred] Operator review gate UI in conductor web interface — deferred to future frontend work

**Exit criteria:**
- ✅ A multi-role task (researcher → coder) executes to completion with a real model
- ✅ Prior step results are visible in later step context
- ✅ All failures are graceful (blocked plan, operator notified)
- ✅ Model reliability issues documented: models produce literal newlines in JSON `answer` strings, DDG search sometimes returns empty for specific queries
- [Deferred] Operator review and approve plan before execution via web UI — exists at API level, pending frontend

**Findings:**
- qwen2.5:7b reliably produces structured JSON with `{"action": "..."}` format. llama3.2:3b is less reliable (more parse errors).
- The most common model failure mode is multiline answers with unescaped newlines in JSON string values — fixed with `_escape_newlines_in_strings()`.
- The second most common failure is the model looping without producing a final answer — mitigated with prompt instructions to stop after one successful tool call.
- duckduckgo_search library returns real web results but can return empty for some queries (DDG-side limitation, not our code).
- Full researcher → coder orchestration (2 steps) completes in ~2 minutes with qwen2.5:7b on a local machine.

---

#### Future Phase 8 Steps (Post-Stage-2 Transition)

Step 6 exit criteria are met for the core agent pipeline. The following items are deferred to future work:

- Confirmation gate wired through the web chat flow (currently available at the API level via `Conductor.__init__(confirmation_gate=...)`)
- Operator review gate UI in the conductor web interface
- Autonomy governance controls for executive function (attention, prioritization bounds)

**Exit criteria (Phase 8 overall):**
- All exit criteria from the autonomy maturity model are satisfied for each stage reached.
- Executive function autonomy operates within defined bounds without exceeding thresholds.
- No autonomous operation has caused an uncontrolled, irreversible outcome.
- Observability and override capability remain intact at all stages.

---

## Dependencies

- Each phase depends on all prior phases reaching their exit criteria.
- The roadmap is reviewed and updated at the end of each phase.
- Significant scope changes require a new ADR.

## Related artifacts

- [`docs/vision.md`](vision.md) — strategic intent this roadmap implements
- [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md) — autonomy stages referenced in Phases 7–8
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — traceability applied throughout
- [`adr/README.md`](../adr/README.md) — ADR process used at each phase
- [ADR-007 — Identity as Domain Object](../adr/0007-identity-as-domain-object.md) — foundation for Phase 5
- [ADR-008 — Observation Store Architecture](../adr/0008-observation-store-architecture.md) — foundation for Phase 5
- [ADR-009 — Executive Reasoning Engine Pattern](../adr/0009-executive-reasoning-engine-pattern.md) — design for Phase 6–7
- [ADR-010 — Runtime Model Evolution](../adr/0010-runtime-model-evolution.md) — infrastructure for Phase 6
- [ADR-011 — Learning Architecture](../adr/0011-learning-architecture.md) — foundation for Phase 7
- [ADR-012 — Wyrd Subsystem Boundary](../adr/0012-wyrd-subsystem-boundary.md) — defining decision for Phase 6 Track A
- [ADR-013 — Conductor Agent Design](../adr/0013-conductor-agent-design.md) — defining decision for Phase 6 Track B
- [ADR-014 — Agent Tool Interface](../adr/0014-agent-tool-interface.md) — tool protocol for Phase 8 Step 1
- [ADR-015 — Agent Role Model](../adr/0015-agent-role-model.md) — role definitions for Phase 8 Step 4
- [ADR-016 — Orchestration Pattern](../adr/0016-orchestration-pattern.md) — multi-step planning for Phase 8 Step 5
