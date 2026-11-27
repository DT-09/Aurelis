# Aurelis

**Enterprise AI Workflow Economics and Value Infrastructure.**

Aurelis measures the economics of AI-enabled work at the workflow level. It reconciles explicitly ingested delivery costs—model inference, compute, tooling, human review and rework—with successful outcomes and evidence-backed value.

The commercial question is simple: **what does one successful AI-assisted outcome actually cost, and what verified value does it create?**

## What the product does

- Register AI-enabled business workflows and accountable owners.
- Ingest cost records with source references and idempotency keys.
- Ingest successful and failed outcomes, including first-pass success.
- Separate verified value from estimated or unverified value.
- Calculate fully loaded cost per successful outcome, first-pass success rate, verified net value and verified ROI.
- Preserve tenant-scoped records and append events to the existing hash-linked audit history.
- Provide portfolio reporting without mixing currencies.

## Commercial path

1. Complimentary 60-minute Workflow Economics Review for one workflow.
2. Paid, bounded Workflow Economics Assessment with agreed scope and acceptance criteria.
3. Recurring enterprise subscription for continuous measurement, evidence history and portfolio reporting.

Aurelis does not publish invented customer results or unsupported savings claims. Pricing is scoped with the buyer after workflow complexity, data access and procurement requirements are understood.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export AURELIS_BOOTSTRAP_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(40))')"
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. Bootstrap the first organization once:

```bash
curl -X POST http://127.0.0.1:8000/v1/bootstrap \
  -H "X-Bootstrap-Key: $AURELIS_BOOTSTRAP_KEY" \
  -H "Content-Type: application/json" \
  -d '{"organization_name":"Example"}'
```

Save the returned API key securely. It is shown only once.

## Economics API

All workflow endpoints require `X-Aurelis-Key: aur_<key-id>.<secret>`.

1. `POST /v1/workflows` — register a workflow, owner and reporting currency.
2. `POST /v1/workflows/{workflow_id}/costs` — ingest categorized delivery costs.
3. `POST /v1/workflows/{workflow_id}/outcomes` — record successful or failed outcomes and value evidence.
4. `GET /v1/workflows/{workflow_id}/economics?days=30` — calculate unit economics.
5. `GET /v1/economics/portfolio?days=30` — review workflow-level economics.
6. `GET /v1/audit/events` and `GET /v1/audit/verify` — inspect and verify the event history.

Cost categories: `model_inference`, `compute`, `tooling`, `human_review`, `rework`, `other`.

## Evidence rules

- ROI uses verified value only. Estimated value is displayed separately.
- Costs must use the workflow's reporting currency.
- Idempotency keys prevent duplicate event ingestion.
- Failed outcomes cannot claim first-pass success or realized value.
- Missing source systems make the economics incomplete; the API states this limitation.
- These calculations are operational measurement, not an independently audited financial statement.

## Current deployment boundary

The current persistence layer is SQLite and supports a single application instance. Native enterprise connectors, SSO/SCIM, fine-grained RBAC, external immutable audit anchoring, multi-region availability and independent security testing are not claimed. Do not use real customer data until security, privacy, contractual and deployment controls have been reviewed.

## Development

```bash
pip install -r requirements.txt
python -m compileall -q app tests
pytest -q
```

See [Commercial Product Specification](docs/COMMERCIAL_PRODUCT.md), [Architecture](docs/ARCHITECTURE.md), [Threat Model](docs/THREAT_MODEL.md) and [Operations](docs/OPERATIONS.md).

## License

No license has been declared. All rights reserved unless the repository owner adds an explicit license.
