# Aurelis architecture

Aurelis is an enterprise AI workflow economics and value infrastructure layer. It reconciles explicitly ingested workflow delivery costs with operational outcomes and evidence-backed value.

## Product flow

1. **Workflow registry** — tenant-owned workflow, purpose, accountable owner and reporting currency.
2. **Cost ledger** — source-linked model inference, compute, tooling, human review, rework and other cost records.
3. **Outcome ledger** — successful and failed work, first-pass success and value classification.
4. **Economics engine** — deterministic fully loaded cost per success, first-pass success rate, verified net value and verified ROI.
5. **Evidence and audit** — idempotency keys, source references and the existing tenant-scoped hash-linked event history.
6. **Portfolio reporting** — workflow-level economics; currencies remain separate.

## Calculation semantics

- Fully loaded cost is the sum of cost records explicitly ingested for the workflow and period.
- Cost per successful outcome is total recorded cost divided by successful outcomes.
- First-pass success rate is successful outcomes marked first-pass divided by successful outcomes.
- Verified value includes only successful outcomes whose value status is `verified`.
- Verified ROI is (verified value - total recorded cost) / total recorded cost. It is not returned when there is no cost or no verified value.
- Estimated value is shown separately and never included in verified ROI.
- Costs and outcomes must use the workflow reporting currency.
- Duplicate idempotency keys do not create duplicate records.

## Trust boundaries and limitations

Aurelis calculates from the records supplied. It cannot infer costs or outcomes from systems that have not been connected. The current release has API-based ingestion; native enterprise connectors are not yet included. The API uses the existing tenant key model and SQLite persistence, which is a single-instance evaluation boundary. SSO/SCIM, fine-grained RBAC, external immutable audit anchoring, multi-region availability and independent security review are not claimed.

Aurelis is not an accounting system, statutory audit opinion, compliance certification or autonomous financial decision-maker. Customer-approved evidence rules are required before value is classified as verified.
