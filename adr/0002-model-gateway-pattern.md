# 0002 — Model Gateway Pattern

**ID:** ADR-002  
**Status:** Accepted  
**Date:** 2026-06-10  
**Affects:** CAP-003, THEME-003  
**Supersedes:** N/A  
**Superseded by:** N/A

---

## Context

AIOS requires AI model inference at multiple points: knowledge enrichment, workflow assistance, document generation, and eventually autonomous agent operations. As the platform evolves, the number of call sites will grow.

Without a consistent mediation layer, each call site would need to:
- Handle provider-specific API differences directly
- Implement its own rate limiting, cost tracking, and logging
- Be updated individually when a model or provider changes
- Potentially bypass safety and policy controls

This creates coupling, duplication, and an ungovernable surface for AI-related risk.

Additionally, the AIOS vision requires that the platform be model-agnostic — no component may have a hard dependency on a specific model or provider. A mediation mechanism is therefore architecturally necessary, not optional.

---

## Decision

Implement a dedicated **Model Gateway** as Layer 3 of the AIOS target architecture. All AI model calls from any layer above Layer 3 must flow through this gateway. No platform component may call an AI model directly, bypassing the gateway.

The gateway exposes a provider-agnostic request interface. Internally it routes to the configured model provider (local or remote), applying rate limiting, cost controls, audit logging, and safety policies before returning the response.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Dedicated gateway service (this decision)** | Single enforcement point; provider abstraction; full audit coverage; policy enforcement in one place; easy to swap providers | Additional component to build and maintain; gateway becomes a critical path dependency |
| **Adapter per call site** | Low initial effort; no new service required | Each adapter must independently implement logging, safety, and rate limiting; provider coupling leaks throughout the codebase; no unified audit trail |
| **Direct model calls with a shared library** | Simpler than a service; shared code reduces duplication | Library must be imported everywhere; still no single enforcement point; rate limiting and audit state are fragmented |
| **No mediation (direct calls)** | Fastest to implement | Violates model-agnostic requirement; no audit trail; no safety enforcement; cannot change providers without touching all call sites |

---

## Rationale

The dedicated gateway pattern best satisfies the AIOS requirements:

- **Model-agnostic by design.** All model-specific details are encapsulated within the gateway. Layers above it interact with a stable, provider-agnostic interface.
- **Single audit and policy enforcement point.** All model calls are logged, rate-limited, and safety-filtered in one place. There is no way to accidentally bypass controls.
- **Supports provider and version changes.** Updating a model or switching providers requires a gateway configuration change, not changes to calling components.
- **Testable and observable.** The gateway can be stubbed in tests and monitored as a single service.

The adapter-per-call-site approach was rejected because it fragments governance and leaves audit coverage dependent on each developer remembering to add logging. The direct-call approach was rejected because it directly violates the model-agnostic principle and produces an ungovernable audit surface.

---

## Consequences

**Positive:**
- All AI model interactions are auditable from a single location.
- Provider and model changes require no modifications to calling components.
- Rate limiting and cost controls are consistently enforced.
- Safety and output filtering policies are applied uniformly.
- The gateway is a natural integration point for model evaluation tooling.

**Negative:**
- The gateway is on the critical path for all AI-assisted operations; it must be robust and well-monitored.
- Request latency increases slightly due to mediation; acceptable for AIOS use cases.
- Initial build effort is higher than direct calls; justified by long-term governance gains.

**Neutral:**
- Application-level prompt engineering remains the responsibility of the calling layer; the gateway does not own prompt content.
- The gateway configuration (provider endpoints, model versions, cost budgets) is a governance artefact managed in Layer 5.

---

## Risks

| Risk | Mitigation |
|---|---|
| Gateway becomes a single point of failure | Health monitoring and circuit-breaker in Layer 1; gateway must be restartable with no data loss |
| Gateway configuration drift — live configuration diverges from governed artefacts | Configuration is version-controlled as a governance artefact; changes require ADR or policy update |
| Rate limiting too restrictive — blocks legitimate workflow execution | Cost and rate budgets are reviewed at each roadmap phase; operators can adjust within policy |
| Safety filters produce false positives and block valid requests | Safety filter policy is a governed artefact; false positives are logged, reviewed, and used to refine policy |

---

## Related artifacts

- [`architecture/target-architecture.md`](../architecture/target-architecture.md) — Layer 3 definition
- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP-003 AI and Model Management
- [`governance/governance-model.md`](../governance/governance-model.md) — model governance domain
- [`docs/vision.md`](../docs/vision.md) — model-agnostic design intent
