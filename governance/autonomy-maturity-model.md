# Autonomy Maturity Model

**ID:** DOC-007  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

Define the stages through which AIOS progresses toward autonomous operation. Each stage has explicit allowed behaviours, prohibited behaviours, required controls, and exit criteria. No stage may be skipped. Stage transitions require an ADR and operator approval.

## Principles

- Autonomy is earned, not assumed.
- Every stage transition increases both capability and governance rigor.
- Human override capability is never removed; it may only change form.
- Rollback to a lower stage must be possible at any point.

---

## Stage 0 — Knowledge-Assisted Workspace

**Description:** The platform is a governed documentation and knowledge system. There is no AI inference at runtime. All content is human-authored.

**Allowed behaviours:**
- Human-authored knowledge ingestion
- Manual query and retrieval of knowledge assets
- Human-authored workflow definitions (not yet executed)

**Prohibited behaviours:**
- Any AI model inference
- Any automated action or workflow execution

**Required controls:**
- Version control for all artefacts
- Backup and restore capability
- Access control for knowledge assets

**Exit criteria:**
- Architecture baseline complete (Phase 1 and Phase 2 roadmap exit criteria met)
- Knowledge store operational with at least one populated domain
- All required controls verified

---

## Stage 1 — AI Assistant

**Description:** AI models are available to assist the operator with knowledge enrichment, document drafting, and information retrieval. All AI outputs are suggestions; no automated action occurs without explicit operator approval.

**Allowed behaviours:**
- AI-assisted document drafting and summarisation
- AI-assisted knowledge retrieval and synthesis
- AI-suggested workflow steps (presented for human review)
- Model gateway operational with audit logging

**Prohibited behaviours:**
- Automated execution of any workflow step without operator approval
- AI-initiated changes to canonical knowledge
- Autonomous scheduling or triggering

**Required controls:**
- Model gateway with full audit logging
- All AI outputs labelled as derived
- Human approval required before any AI-suggested content becomes canonical
- Observability dashboard operational

**Exit criteria:**
- Model gateway fully operational and audited
- At least 30 days of AI-assisted operation with no uncontrolled outcomes
- Human approval rate and AI output quality metrics established and within acceptable range
- Observability coverage complete

---

## Stage 2 — AI Contributor

**Description:** AI may execute defined, bounded workflow steps autonomously, within a narrowly scoped and human-approved workflow definition. Human approval gates remain at defined checkpoints.

**Allowed behaviours:**
- Autonomous execution of approved, bounded workflow steps
- AI-generated draft pull requests and documentation (with human review gate before merge)
- Autonomous knowledge ingestion within approved sources and schemas

**Prohibited behaviours:**
- Autonomous execution of multi-step workflows without defined human checkpoints
- AI-initiated changes to the governance or architecture artefacts
- Autonomous external integrations outside approved scope
- Autonomous changes to model gateway configuration

**Required controls:**
- Human approval gates at defined workflow checkpoints (not removable at this stage)
- Circuit-breaker policies defined and tested
- Full workflow execution audit trail
- Boundary violation alerting operational
- Rollback procedures tested

**Exit criteria:**
- At least 90 days of Stage 2 operation with no boundary violations
- Human approval override exercised and functioning correctly
- Circuit-breaker triggered and recovered successfully at least once in testing
- Workflow audit trail complete and queryable

---

## Stage 3 — AI Reviewer

**Description:** AI may review code, documents, and workflow outputs and provide structured feedback. AI-suggested approvals require human confirmation at this stage.

**Allowed behaviours:**
- Autonomous code review with structured findings
- Autonomous document quality assessment
- AI-suggested workflow approvals (human confirms)
- AI-initiated knowledge quality review (human confirms lifecycle change)

**Prohibited behaviours:**
- AI-approved merges or deployments without human confirmation
- Autonomous changes to production configurations
- Autonomous stage transitions

**Required controls:**
- All AI review findings retained and linked to artefacts
- Human confirmation required for all AI-suggested approvals
- Evaluation metrics for review quality defined and monitored

**Exit criteria:**
- AI review quality metrics demonstrate sustained acceptable precision and recall
- At least 60 days of Stage 3 operation with no uncontrolled approvals
- Evaluation framework operational

---

## Stage 4 — AI Developer

**Description:** AI may autonomously implement bounded, pre-approved work items within a defined scope. Implementation is subject to AI Reviewer assessment and human final approval before merging.

**Allowed behaviours:**
- Autonomous implementation of scoped, pre-approved work items
- Autonomous test generation and execution
- Autonomous documentation updates for implemented changes
- Submission of implementation for AI and human review

**Prohibited behaviours:**
- Autonomous merge without human final approval
- Autonomous scope expansion beyond the pre-approved work item
- Autonomous changes to governance, security, or policy artefacts

**Required controls:**
- Pre-approval of work item scope by human operator
- AI and human review gates before merge
- Implementation audit trail from work item to merged change
- Automated test coverage thresholds enforced

**Exit criteria:**
- Demonstrated implementation quality over at least 30 work items
- Human final approval rate is well-understood and stable
- No scope expansion incidents

---

## Stage 5 — AI Team Member

**Description:** AI may participate in planning, estimation, and prioritisation of work within a governed scope. Autonomous execution of multi-step workflows within approved scope is permitted with lightweight checkpoints.

**Allowed behaviours:**
- Autonomous participation in planning and scoping discussions
- Multi-step workflow execution with automated checkpoints (human spot-check model)
- Autonomous knowledge base maintenance within approved domains

**Prohibited behaviours:**
- Autonomous changes to architecture, governance, or policy artefacts
- Autonomous external communications or integrations beyond approved scope
- Autonomous budget or resource allocation

**Required controls:**
- Spot-check review model with defined sampling rate
- Automated anomaly detection on workflow outputs
- Escalation to full human review on anomaly detection
- Quarterly governance review of Stage 5 behaviour

**Exit criteria:**
- At least 180 days of Stage 5 operation with sustained quality and no significant incidents
- Governance review completed and signed off

---

## Stage 6 — Limited Autonomous Operator

**Description:** AI may operate certain bounded, well-understood operational domains with minimal human interaction. Strategic decisions, governance changes, and high-impact actions always require human approval.

**Allowed behaviours:**
- Autonomous routine operational workflows (backups, monitoring responses, scheduled maintenance)
- Autonomous knowledge lifecycle maintenance within approved policy
- Autonomous delivery of pre-approved release artefacts

**Prohibited behaviours:**
- Autonomous changes to governance, architecture, security, or policy artefacts
- Autonomous external communications beyond defined scope
- Autonomous stage transitions (these always require human approval)
- Autonomous high-impact or difficult-to-reverse actions

**Required controls:**
- Comprehensive observability for all autonomous actions
- Automated circuit-breaker on any anomalous pattern
- Monthly governance review
- Human operator retains override capability at all times
- Formal incident review process

**Exit criteria:**
- TBD — this stage is not yet planned for near-term activation. Exit criteria will be defined in a future ADR.

---

## Stage transition checklist

For any stage transition:

1. Confirm all exit criteria for the current stage are documented and met
2. Author an ADR recording the transition decision and rationale
3. Verify rollback to prior stage is tested and possible
4. Confirm all required controls for the new stage are operational
5. Obtain operator approval
6. Monitor closely for the first 30 days at the new stage

## Related artifacts

- [`governance/governance-model.md`](governance-model.md) — autonomy governance domain
- [`docs/roadmap.md`](../docs/roadmap.md) — phases that introduce autonomy stages
- [`architecture/principles.md`](../architecture/principles.md) — governance before autonomy principle
