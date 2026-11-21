# Aurelis architecture

Aurelis is a vendor-neutral AI authority and assurance control plane. It records what an AI asset is, what it may do, what evidence supports its state, which policies apply, and why a requested action was allowed or denied. It is not a model, agent framework, runtime sandbox, or safety certification.

## Integrated control loop

1. **Identity** — tenant-owned assets and API credentials.
2. **Authority** — explicit per-asset grants, denials and human-gated actions.
3. **Evidence** — source records bound to assets and content-addressed with SHA-256.
4. **Policy** — deterministic metric rules with blocking or warning effects.
5. **Decision** — assessment verdicts and action authorization outcomes.
6. **Audit** — per-tenant hash-linked event history.

## Trust semantics

- ASSURED: all supplied policy rules passed and referenced evidence passed integrity checks. Not a universal safety claim.
- DEGRADED: warnings exist but no blocking finding.
- BLOCKED: a blocking rule or evidence-integrity finding exists.
- UNKNOWN: no policy was applied. Unknown is never promoted to assured.

## Data isolation and persistence

Every tenant-owned read is scoped by organization ID. API keys use salted PBKDF2-HMAC-SHA256 hashes; raw keys are returned only on creation. Bootstrap is one-time. SQLite is the embedded, single-instance persistence layer. Multi-instance HA and PostgreSQL migrations are not part of this release.

## Enforcement boundary

Aurelis returns decisions; it does not automatically intercept agent tools. Integrate it at the actual tool gateway and fail closed if it is unavailable. The current human_approved field is a caller-supplied boolean, not an authenticated approval ceremony. High-impact actions require an independently authenticated approver and binding to the exact action and context.
