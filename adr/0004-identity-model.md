# 0004 — Identity Model

**ID:** ADR-004  
**Status:** Superseded  
**Date:** 2026-06-10  
**Affects:** CAP-007, THEME-001  
**Supersedes:** N/A  
**Superseded by:** ADR-007

---

## Context

AIOS requires an identity and access control model for Layer 2 (Identity, Security, and Policy). Identity context must be present on all requests at Layer 3 and above, supporting access control policy evaluation and audit trail attribution.

The platform is a personal, single-operator system. It runs locally with no multi-user, multi-tenant, or networked authentication requirements in the current scope. However, the identity model must:

- Provide an authenticated operator identity for all direct interactions
- Provide distinct service identities for platform components (gateway, workflow runtime, ingestion pipelines, etc.) so that audit logs attribute actions to the correct actor
- Support access control policy evaluation at component boundaries (least-privilege)
- Not introduce external identity provider dependencies that violate the local-first principle
- Be extensible: if the platform later exposes local network services, the model must not require a full redesign

---

## Decision

Adopt a **local single-operator identity model** with **service identity tokens for platform components**.

1. **Operator identity:** A single operator principal is defined at platform configuration time. The operator authenticates to the platform using a locally-managed credential (a passphrase-protected key or token stored in the local secrets vault). Once authenticated, the operator session carries a signed identity context for the duration of the session.

2. **Service identities:** Each platform component (model gateway, workflow runtime, knowledge ingestion pipeline, etc.) is assigned a distinct service identity with a minimal set of permissions (least-privilege). Service credentials are stored in the local secrets vault, provisioned at platform setup, and rotated periodically.

3. **Policy evaluation:** Access control policies are defined as structured rules in Layer 2. Policies are evaluated on each cross-layer request using the identity context attached to the request. Policy rules are governance artefacts, version-controlled alongside other platform configuration.

4. **No external identity provider.** The identity model relies entirely on local credentials and local policy evaluation. Integration with an external identity provider (OAuth, LDAP, etc.) is explicitly deferred; it requires a new ADR if the scope changes.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Local single-operator + service identities (this decision)** | Fully local; no external dependencies; least-privilege enforced; audit attribution per component; extensible | Manual credential management; operator must manage key/token lifecycle |
| **No authentication (local-only trust)** | Zero implementation overhead | No audit attribution; no access control enforcement; contradicts governance principles; unextensible if any service is exposed on the local network |
| **External identity provider (OAuth2/OIDC)** | Industry-standard; well-tooled; portable | External service dependency violates local-first principle; overkill for a personal single-operator platform; adds setup complexity |
| **OS-level user identity only** | No additional infrastructure | OS users are coarse-grained; no component-level service identities; policy enforcement is limited to OS-level primitives; not portable across deployments |
| **API key per component (no operator identity)** | Simple; well-understood | Audit trail attributes actions to components, not to the operator intent; no human identity layer; harder to govern |

---

## Rationale

The local single-operator model matches the operational reality of AIOS: one operator, local infrastructure, no network authentication requirements.

Key reasons for this choice:

- **Local-first.** No external identity provider is needed. The operator credential and service credentials are stored in the local secrets vault (Layer 1). The platform can authenticate and authorise all operations without a network connection.
- **Least-privilege by default.** Service identities ensure that a compromised or malfunctioning component cannot exceed its declared permission boundary. This limits blast radius and improves auditability.
- **Audit trail attribution.** With distinct service identities, the audit trail can distinguish between an action taken by the operator directly and one taken by the workflow runtime on behalf of a workflow. This is important for understanding and overriding automated actions.
- **Extensible without redesign.** The session-token model (signed identity context on each request) is compatible with adding a network boundary later. If a future ADR introduces local network exposure, the same identity model applies; only the transport and authentication mechanism changes.

The no-authentication option was rejected because it produces an audit trail that cannot attribute actions to actors, which directly undermines governance requirements.

The external identity provider option was rejected because it introduces an external service dependency that is disproportionate to the scale of the platform and violates the local-first principle.

---

## Consequences

**Positive:**
- All platform actions are attributed to a specific actor (operator or named service) in the audit trail.
- Component boundaries enforce least-privilege without relying on application-level controls.
- No external service dependency; the platform authenticates and authorises entirely locally.
- Credential management is contained within the local secrets vault.

**Negative:**
- The operator must manage the local credential lifecycle (creation, passphrase, rotation).
- Service credential provisioning is a manual setup step; tooling must make this reliable and documented.
- If the platform later exposes a service on the local network, a new ADR will be required to address network-facing authentication.

**Neutral:**
- The secrets vault implementation is a Layer 1 responsibility; this ADR does not mandate a specific vault technology. That decision will be made as part of Phase 4 platform implementation.
- Policy rules are version-controlled in Layer 5; changes to policies follow the governance artefact change process.

---

## Risks

| Risk | Mitigation |
|---|---|
| Operator credential compromise (passphrase-protected key stolen or leaked) | Key is stored in local secrets vault only; never in version control; credential rotation procedure is documented |
| Service credential rotation neglected | Rotation schedule defined in platform operational runbook; rotation is a governed operational procedure |
| Policy rules become inconsistent with capability permissions | Policy rules are version-controlled and reviewed at each roadmap phase transition |
| Identity model insufficient if local network exposure is introduced | New ADR required before any network-facing surface is introduced; this decision explicitly defers that scenario |

---

## Related artifacts

- [`architecture/target-architecture.md`](../architecture/target-architecture.md) — Layer 2 Identity, Security, and Policy
- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP-007 Security and Policy
- [`governance/governance-model.md`](../governance/governance-model.md) — security governance domain
- [`docs/glossary.md`](../docs/glossary.md) — Identity Context, Policy, Audit Trail
