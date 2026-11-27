# Aurelis commercial product specification

## Category
Enterprise AI workflow economics and value infrastructure.

## Commercial job
Give finance, AI and operations leaders a defensible answer to four questions for each AI-enabled workflow:
1. What did it cost to deliver work, including model, compute, tooling, human review and rework?
2. How many outcomes succeeded, failed or required rework?
3. What value is supported by evidence, and what remains only estimated?
4. Should the workflow be expanded, redesigned, paused or retired?

## Initial buyer
Economic buyer: CFO / finance transformation leader / CIO / Chief AI Officer.
Operational champion: AI platform leader, FinOps lead, automation owner or workflow operations director.
Initial account qualification: an enterprise already running at least one material AI-enabled workflow, with identifiable operating costs and a named business owner.

## Product modules
- Workflow Registry: named workflows, accountable owners, purpose and reporting currency.
- Cost Ledger: idempotent cost records for model inference, compute, tooling, human review, rework and other delivery costs.
- Outcome Ledger: successful/failed outcomes, first-pass success and value classification.
- Economics Engine: fully loaded cost per successful outcome, first-pass success rate, verified value, net value and verified ROI.
- Evidence and Audit: source references, deterministic calculations and hash-linked events.
- Portfolio View: workflow-level results without incorrectly summing across currencies.

## Calculation rules
- Fully loaded cost = sum of explicitly ingested cost records in the reporting period.
- Cost per successful outcome = fully loaded cost / successful outcomes.
- First-pass success rate = successful outcomes marked first-pass / successful outcomes.
- Verified value = sum of value amounts classified as verified for successful outcomes. The current API records the caller's classification and source reference; it does not independently validate the underlying business event.
- Verified ROI = (verified value - fully loaded cost) / fully loaded cost, only when cost and verified value are both present.
- Estimated and unverified value never enters verified ROI.
- Failed outcomes cannot claim first-pass success or realized value.
- Every record has an idempotency key to prevent duplicate ingestion.
- Currency must match the workflow reporting currency. Portfolio totals are not combined across currencies.

## Commercial entry offer
A complimentary 60-minute Workflow Economics Review:
- select one live AI-enabled workflow;
- map cost sources and human interventions;
- identify the outcome definition and baseline;
- identify missing evidence and attribution gaps;
- return a concise measurement plan and a go / redesign / do-not-scale recommendation.

Paid next step: a bounded, paid Workflow Economics Assessment for one workflow, with agreed data scope, deliverables, acceptance criteria and price before work begins.

Recurring product: enterprise subscription for continuous workflow cost/outcome ingestion, economics reporting, alerts, evidence history and portfolio governance. Commercial pricing is quoted only after scope and buyer willingness-to-pay are established; no unsupported price claims.

## Non-claims
Aurelis does not claim customer results, savings, regulatory certification, independent audit status, automatic access to enterprise systems, or production security certification. A metric is only as complete as the source records supplied. Verified value requires a documented customer-approved evidence rule.

## Current release boundary
The API currently provides workflow registry, cost and outcome ingestion, deterministic unit-economics calculations, idempotency, tenant scoping and commercial inquiry intake. Native integrations, SSO/SCIM, role-based access control, multi-region availability, immutable external audit anchoring and independent security review remain release gates before enterprise production procurement.

## Commercial validation gates
1. Conduct 8–10 structured conversations with qualified budget owners and workflow owners across distinct enterprises.
2. Record the current measurement method, data sources, economic consequence, incumbent tool, buying trigger, budget owner and procurement/security requirements.
3. Do not count interest as demand. Demand requires a buyer to provide a real workflow, identify an owner, agree to a defined paid assessment scope and discuss a budget.
4. Do not build a connector until a qualified buyer confirms the source system and access path.
5. Proceed to recurring subscription only after the assessment demonstrates repeatable monthly use and the buyer identifies an ongoing owner and budget.

## Data handling
Use synthetic data for public examples. Do not upload customer records, prompts, credentials or personal data without written authorization, data minimization, security review and appropriate contractual controls. The current SQLite deployment is a single-instance evaluation boundary, not an enterprise multi-tenant production claim.
