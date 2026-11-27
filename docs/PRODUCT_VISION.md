# Aurelis — product vision

## Category

Enterprise AI workflow economics and value infrastructure.

## Mission

Make the economics of AI-enabled work measurable at the level where business decisions are made: the workflow and its successful outcome.

Aurelis connects operating costs, human effort, rework, outcome quality and customer-approved value evidence. It gives finance, AI and operations leaders a defensible basis to decide which workflows to scale, redesign, pause or retire.

## The expensive problem

Enterprise AI reporting is fragmented:

- Model providers report usage and inference charges.
- Cloud platforms report compute consumption.
- Operations teams record completed work, exceptions and rework.
- Managers estimate productivity and savings.
- Finance needs attributable, reviewable economic outcomes.

These records rarely share a common workflow identifier, outcome definition or evidence standard. As a result, leaders can see AI activity without being able to reconcile the full cost of a successful business outcome.

Aurelis addresses this gap. It does not assume that AI usage creates value.

## Initial customer

An enterprise already operating material AI-enabled workflows, with:
- a named workflow owner;
- recurring volume and measurable outcomes;
- identifiable model, infrastructure and tooling costs;
- human review, escalation or rework;
- an executive sponsor accountable for AI economics.

Economic buyers: CFO, finance transformation leader, CIO or Chief AI Officer.
Operational champions: AI platform/FinOps leader, automation director or workflow operations leader.

Aurelis should initially qualify buyers with a live measurement problem and a current decision about scaling, redesigning or controlling an AI workflow.

## Core product

1. **Workflow registry** — workflow purpose, owner, outcome definition and reporting currency.
2. **Cost ledger** — source-linked model, compute, tooling, human review, rework and other costs.
3. **Outcome ledger** — successful/failed outcomes, first-pass success and exception/rework status.
4. **Value evidence** — customer-approved rules that distinguish verified, estimated and unverified value.
5. **Economics engine** — fully loaded cost per successful outcome, first-pass success, verified net value and verified ROI when evidence supports it.
6. **Decision record** — explicit data coverage, assumptions, limitations and a go / redesign / pause recommendation.
7. **Audit history** — tenant-scoped event history, source references and deterministic calculations.

## Initial commercial wedge

Start with one workflow, not an enterprise-wide platform rollout.

The first paid engagement is a bounded AI Workflow Economics Assessment. It reconciles customer-approved exports and operating records, identifies missing cost/value evidence, calculates defensible unit economics where the data permits, and gives the buyer a decision-ready report.

The software supports repeatable calculations and evidence history. The initial delivery may include controlled analyst-led data mapping because native integrations are not yet implemented.

## Product invariants

- Evidence before claims: no savings or ROI claim without an explicit evidence rule.
- Cost completeness is visible: missing sources are stated, never silently treated as zero.
- Outcome definitions are explicit and agreed with the customer.
- Estimated value is never presented as verified value.
- Currency boundaries are preserved.
- Duplicate ingestion is prevented through idempotency.
- Every result is reproducible from supplied records and documented calculation rules.
- No autonomous financial decisions or write access to customer systems.

## What Aurelis is not

- Not a token dashboard or generic AI observability product.
- Not an accounting system, statutory audit, valuation, tax opinion or compliance certification.
- Not an AI implementation agency.
- Not a promise that every AI workflow will produce positive ROI.
- Not a fully integrated enterprise platform in the current release.

## Current implementation boundary

Implemented: FastAPI service, organization bootstrap, API-key authentication, tenant-scoped SQLite storage, workflow registry, cost and outcome ingestion, deterministic economics calculations, idempotency, hash-linked event history, portfolio reporting and commercial inquiry intake.

Not implemented: native enterprise connectors, SSO/SCIM, fine-grained RBAC, PostgreSQL/high availability, automated data mapping, external immutable audit anchoring, independent penetration testing, enterprise security certification, billing and production support commitments.

The current release is an evaluation and controlled-assessment system. Do not ingest confidential customer data or represent it as enterprise-production-ready until security, privacy, contractual and deployment controls are reviewed.

## North-star outcome

For each in-scope AI workflow, the buyer can answer:

1. What did one successful outcome actually cost?
2. How much human review and rework was required?
3. What value is supported by accepted evidence?
4. What data is missing?
5. Should this workflow be scaled, redesigned, paused or stopped?
