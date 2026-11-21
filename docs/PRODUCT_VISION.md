# Aurelis — product vision

## Mission

Make the authority of AI systems explicit, enforceable, inspectable and revocable across their full operational lifecycle. Aurelis is the independent control plane between AI systems and the real-world tools, data and decisions they can affect.

## The problem

Organizations deploy models and agents across vendors, frameworks and business units. Their identities, permissions, evaluations, operational evidence and incident records live in separate systems. A policy document does not constrain a tool call. A model evaluation does not establish who authorized a deployment. A log does not prove that the recorded event is complete or untampered.

Aurelis connects these concerns into one traceable control loop.

## Product invariants

1. **Least authority:** no implied permissions; default deny.
2. **Separation of duties:** asset owner, policy author, approver and operator are distinct roles in the target architecture.
3. **Evidence before claims:** assurance verdicts are tied to versioned evidence, explicit metrics and policy versions.
4. **Explainable decisions:** every authorization returns a machine-readable outcome and reasons.
5. **Fail-closed enforcement:** integrations do not execute protected actions when the control plane cannot provide a valid decision.
6. **Vendor neutrality:** the core protocol does not depend on a particular model provider or agent framework.
7. **Reversibility:** authority grants, deployments and policy changes must be time-bounded, auditable and revocable.
8. **No false certification:** passing a configured policy is not universal safety, legal compliance or independent certification.

## End-state architecture

### 1. Identity and asset registry
Organizations, human identities, service identities, agents, models, tools, datasets, deployments, versions, owners, environments and dependency relationships. Target integrations include OIDC/SSO, SCIM, cloud IAM and common agent frameworks.

### 2. Authority graph
Versioned authority contracts define principals, resources, actions, purposes, data boundaries, conditions, delegation depth, expiry and approval requirements. Policy evaluation uses explicit grants and denials, least privilege and deny-overrides semantics. Every grant has an owner and review date.

### 3. Assurance and evidence fabric
Evidence is collected from evaluations, CI pipelines, red-team tests, model cards, deployment manifests, monitoring systems, incidents and human reviews. Each item carries provenance, source identity, asset/version binding, timestamp, integrity hash and verification status. Policies are versioned and deterministic where possible.

### 4. Runtime enforcement plane
SDKs, middleware and gateway adapters intercept tool calls and ask Aurelis for a decision. Decisions bind to the exact principal, action, resource, context, policy revision and expiry. Short-lived signed decision tokens prevent replay and stale grants. Enforcement points fail closed on timeout, invalid signature, stale policy or unavailable control plane.

### 5. Continuous operational assurance
Telemetry and event streams update reliability, drift, dependency health, policy compliance and risk state. Threshold breaches trigger re-evaluation, restriction, quarantine or human escalation. Recovery actions are explicit and reversible. Provider and tool dependencies are mapped to blast radius and fallback readiness.

### 6. Governance and audit
A tamper-evident event ledger records identity changes, policy revisions, evidence intake, assessments, approvals, grants, denials, incidents and overrides. External signed checkpoints anchor the ledger. Governance views show ownership, exceptions, expiry, control coverage and unresolved risks.

### 7. Integration and deployment
A stable API and protocol, SDKs, CI checks, webhooks, policy-as-code, cloud deployment adapters, observability integrations and enterprise identity connectors. Deployment modes target single-tenant self-hosted, managed control plane and hybrid edge enforcement.

## Core user journeys

- **Register:** discover or register an AI asset, its owner, version, environment and dependencies.
- **Define authority:** specify allowed actions, denied actions, data scope, autonomy ceiling, expiry and approval gates.
- **Prove readiness:** attach provenance-backed evidence and run policy evaluations before deployment.
- **Enforce:** intercept each protected tool action and obtain a context-bound decision.
- **Observe:** stream operational evidence and detect drift, policy violations and dependency failures.
- **Respond:** suspend a grant, quarantine an asset, require review or roll back to a known state.
- **Audit:** reconstruct who changed what, which evidence and policy applied, and why a decision was made.

## Current implementation boundary

The repository currently implements a single-instance Python/FastAPI control plane with SQLite, one-time organization bootstrap, salted API-key hashing, asset registration, explicit action grants/denials, human-approval flags, policy assessments, evidence hashes, a hash-linked audit log and a small browser console.

The following end-state capabilities are not yet implemented: multi-organization onboarding and roles, SSO/SCIM, delegated authority graph, signed short-lived runtime decisions, real tool-gateway adapters, continuous telemetry ingestion, incident automation, external audit anchoring, PostgreSQL/high availability, billing, and production-grade authenticated approval. The architecture above is the product target, not a claim that these functions already exist.
