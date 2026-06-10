# 0006 — Model Gateway Technology Selection

**ID:** ADR-006  
**Status:** Accepted  
**Date:** 2026-06-10  
**Affects:** CAP-003, THEME-003  
**Supersedes:** N/A  
**Superseded by:** N/A

---

## Context

ADR-002 established the **Model Gateway pattern**: all AI model calls must flow through a single mediation layer. ADR-002 decided *what* the gateway is; this ADR decides *how* to implement it.

The gateway must:

- Provide a provider-agnostic completion interface (text, structured output)
- Support local models (Ollama) and remote providers (OpenAI, Anthropic) through the same interface
- Log every request and response for audit
- Enforce configurable rate limits and cost budgets
- Apply basic safety pre- and post-filtering
- Be local-first: the platform must function with a local model and no internet connection
- Be simple enough to deploy as a Python module at Phase 4 without requiring a running server
- Be extensible to a network service in Phase 5 when AI assistance becomes interactive

The platform is single-operator and local. At Phase 4, all calls originate from workflow steps running on the same machine. A network service is not required until Phase 5.

---

## Decision

Implement the model gateway as a **Python library module** using **LiteLLM** as the provider abstraction layer, with **Ollama** as the default local provider.

- **LiteLLM** provides a unified `completion()` interface across OpenAI, Anthropic, Ollama, and 100+ other providers with a single consistent API.
- The gateway wraps LiteLLM with AIOS-specific concerns: audit logging, rate limiting, cost tracking, safety filtering, and configuration loading.
- The gateway is a Python module (`platform/model-gateway/src/gateway.py`), not a network service. Callers import and call it directly at Phase 4.
- Audit entries are written to `platform/model-gateway/audit/audit.jsonl` (JSONL format — one JSON object per call).
- Configuration is loaded from `platform/model-gateway/config/gateway-config.yaml`.
- A CLI (`platform/model-gateway/src/cli.py`) provides `query` and `audit` commands for operator use.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **LiteLLM + Python module (this decision)** | Unified interface across 100+ providers; supports Ollama natively; actively maintained; no server required at Phase 4; simple to wrap | Adds an external dependency; LiteLLM API surface is large; must track LiteLLM breaking changes |
| **Direct provider SDKs (openai, anthropic, etc.)** | No extra abstraction layer | Provider-specific code must be written per provider; violates ADR-002 model-agnostic principle; significant duplication |
| **LangChain** | Rich tooling; many integrations | Extremely large dependency surface; opinionated architecture; complex to trace and audit; over-engineered for Phase 4 |
| **Llamaindex** | Good knowledge retrieval integration | Primarily focused on retrieval pipelines; not a general model gateway; heavy for Phase 4 |
| **Custom provider abstraction (no LiteLLM)** | Zero new dependencies; full control | Significant implementation effort to match LiteLLM's provider coverage; reinvents existing solved problem |
| **FastAPI service** | Clear network boundary; process isolation | Requires a running server; deployment complexity; not needed at Phase 4 scale; premature |

---

## Rationale

LiteLLM provides the most direct path to a model-agnostic gateway without requiring custom provider adapters.

Key reasons:

- **Model-agnostic by design.** LiteLLM's `completion()` interface is identical regardless of whether the call goes to Ollama, OpenAI, or Anthropic. Switching providers requires only a configuration change.
- **Local-first.** Ollama is a supported provider in LiteLLM. The gateway can operate entirely offline with a locally-running Ollama instance.
- **Simply founded.** The gateway is a thin wrapper around LiteLLM. The added complexity (audit logging, rate limiting, config loading) is small and contained.
- **Extensible to a service.** The gateway module exposes a clean function interface (`complete()`). Promoting it to a FastAPI service in Phase 5 means wrapping the same module in an HTTP handler — no logic changes required.

Direct provider SDKs were rejected because they would scatter provider-specific code across the codebase, violating ADR-002. LangChain was rejected because its dependency surface and architectural opinions would introduce uncontrolled complexity for a single-purpose gateway.

---

## Consequences

**Positive:**
- Provider changes require only a configuration update, not code changes.
- The audit log provides a complete record of all AI calls, enabling cost analysis and compliance review.
- Local-first: the platform works fully offline with Ollama.
- Rate limiting and cost controls are enforced consistently for all callers.

**Negative:**
- LiteLLM is an external dependency that must be version-pinned and updated carefully.
- The gateway is not a network service at Phase 4; callers must import the Python module. A service boundary requires a new ADR.
- LiteLLM's API surface is large; only the `completion()` and `embedding()` interfaces are used at Phase 4.

**Neutral:**
- The gateway configuration (`config/gateway-config.yaml`) is a governance artefact; changes require documented justification.
- The audit log schema is defined in `schema/audit-log-schema.yaml`; schema changes follow the ADR process.
- Provider-specific API keys are not stored in version control; they are loaded from environment variables or the local secrets vault per ADR-004.

---

## Risks

| Risk | Mitigation |
|---|---|
| LiteLLM introduces a breaking API change | Gateway is pinned to a tested LiteLLM version in `requirements.txt`; upgrades are tested before adoption |
| Provider API key leaked into audit log | Audit log sanitisation strips credentials from recorded request metadata before writing |
| Gateway called directly (bypassing audit) | Code review policy prohibits direct provider calls; the pattern is enforced by convention and checked in code review |
| Cost budget exceeded by runaway workflow | Budget tracking in the gateway emits a warning and optionally blocks further calls when the threshold is reached |

---

## Related artifacts

- [`adr/0002-model-gateway-pattern.md`](0002-model-gateway-pattern.md) — gateway pattern this ADR implements
- [`adr/0004-identity-model.md`](0004-identity-model.md) — credential storage for provider API keys
- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP-003 AI and Model Management
- [`architecture/target-architecture.md`](../architecture/target-architecture.md) — Layer 3 Model Gateway
- [`governance/governance-model.md`](../governance/governance-model.md) — AI and model governance domain
- [`docs/roadmap.md`](../docs/roadmap.md) — Phase 4 deliverables
