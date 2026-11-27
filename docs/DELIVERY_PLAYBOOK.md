# Aurelis delivery playbook — AI Workflow Economics Assessment

## Purpose

Deliver a reproducible, evidence-backed economic assessment for one live AI workflow. This playbook is a controlled service procedure, not an independent audit.

## Before accepting data

1. Confirm the buyer, workflow owner, purpose, reporting period and decision to be made.
2. Agree in writing on scope, fee, acceptance criteria, delivery date and authorized data sources.
3. Obtain written authorization for each export and confirm the approved transfer/storage method.
4. Request minimized exports. Do not request passwords, API keys, customer prompts, personal data or unrelated records.
5. Confirm whether the current Aurelis environment is approved for the data. If not, use an approved customer-controlled environment or decline the data.
6. Record retention/deletion terms before receipt.

## Required input map

| Domain | Minimum fields | Common source |
|---|---|---|
| Workflow outcomes | outcome ID, timestamp, status, workflow ID | workflow/CRM/ticket export |
| Model/API costs | date, provider, model, amount, currency, request/workflow reference | provider billing export |
| Compute | date, service, amount, currency, allocation key | cloud billing export |
| Tooling | date, license/service, amount, currency, allocation basis | vendor invoice |
| Human review | time period, role/rate or approved cost, duration, workflow/outcome reference | time or operations export |
| Rework | outcome ID, rework count/time/cost, reason | workflow/ticket export |
| Value evidence | outcome ID, value amount, currency, evidence source, customer-approved status | finance/CRM/operations evidence |

Not every source will exist. The coverage matrix must show what is present, missing, allocated or estimated.

## Reconciliation procedure

1. Freeze the agreed reporting period and timezone.
2. Preserve original files read-only and record filenames, source owner, received timestamp and file hash.
3. Profile schema, missingness, duplicate keys, currency, timestamp ranges and row counts.
4. Map each source to the agreed workflow and outcome identifiers.
5. Separate directly observed cost from allocated cost and estimated cost.
6. Reconcile totals to source exports; document unmatched and excluded rows.
7. Deduplicate using source-native identifiers where possible.
8. Classify outcomes using the buyer-approved definition.
9. Calculate cost per successful outcome only when cost and outcome populations align.
10. Classify value as verified, estimated or unverified using the written evidence rule.
11. Calculate verified ROI only when the required cost and value evidence is present and comparable.
12. Independently recheck totals and sample source-to-output traceability.

## Required report sections

1. Executive decision summary.
2. Scope, period, workflow and outcome definition.
3. Source inventory and coverage matrix.
4. Reconciliation controls and data-quality findings.
5. Cost composition and allocation method.
6. Outcome quality, first-pass success and rework.
7. Cost per successful outcome.
8. Verified / estimated / unverified value.
9. ROI only where supported.
10. Limitations, assumptions and unresolved gaps.
11. Scale / redesign / pause / collect-more-evidence recommendation.
12. Appendix: reproducible calculations and source references.

## Quality gates

Do not issue a positive ROI conclusion when:
- cost sources are materially incomplete;
- cost and outcome periods do not align;
- workflow allocation is unsupported;
- currencies differ without an agreed conversion method;
- the value rule is not approved by the customer;
- value is only estimated or unverified;
- duplicates or missing records could materially change the result.

State the limitation and recommend the minimum additional evidence required.

## Closeout

- Walk through the report with the buyer.
- Record corrections and acceptance against the agreed criteria.
- Deliver only the agreed artifacts through the approved channel.
- Retain/delete source files according to the written terms.
- Ask whether a recurring monthly decision requires ongoing measurement; do not presume a subscription.
