# Aurelis operations

## Product boundary

Aurelis currently supports controlled AI workflow economics assessments through its API. The service records workflows, source-linked cost events and outcome events, then calculates unit economics from the records supplied.

The current deployment is a single-instance SQLite evaluation boundary. Do not use confidential customer data until the specific deployment, data path, access controls, retention and contractual terms have been reviewed and approved.

## Local development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export AURELIS_BOOTSTRAP_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(40))')"
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API documentation is available at /docs during development.

## Bootstrap an organization

```bash
curl -X POST http://127.0.0.1:8000/v1/bootstrap \
  -H "X-Bootstrap-Key: $AURELIS_BOOTSTRAP_KEY" \
  -H "Content-Type: application/json" \
  -d '{"organization_name":"Example"}'
```

Store the returned API key in a secret manager. It is shown only once.

## Economics workflow

1. Create a workflow with its purpose, accountable owner and reporting currency using `POST /v1/workflows`.
2. Record model inference, compute, tooling, human review, rework and other costs using `POST /v1/workflows/{workflow_id}/costs`.
3. Record successful/failed outcomes, first-pass status and the buyer-approved value classification using `POST /v1/workflows/{workflow_id}/outcomes`.
4. Review unit economics using `GET /v1/workflows/{workflow_id}/economics?days=30`.
5. Review the portfolio using `GET /v1/economics/portfolio?days=30`.
6. Inspect and verify the event history using `GET /v1/audit/events` and `GET /v1/audit/verify`.

All workflow endpoints require `X-Aurelis-Key: aur_<key-id>.<secret>`.

## Evidence rules

- Every cost and outcome must have a source label and idempotency key.
- Reusing an idempotency key with a different payload is rejected.
- Currency must match the workflow reporting currency.
- Failed outcomes cannot be marked first-pass successful or carry realized value.
- Only successful outcomes may carry verified value.
- Estimated and unverified value are excluded from verified ROI.
- Aurelis stores supplied source references; it does not independently validate the underlying business result.
- Missing sources must be disclosed. Do not interpret missing data as zero.

## Commercial inquiries

The public site posts business inquiries to `POST /v1/commercial/inquiries`. New inquiries are stored in the application database. The current release does not provide an automated email notification or CRM sync; the operator must monitor the authorized inquiry store. Do not promise response SLAs until monitoring and ownership are in place.

## Container

Set `AURELIS_BOOTSTRAP_KEY` to a random value of at least 32 characters and `AURELIS_CORS_ORIGINS` to explicit origins, then run `docker compose up --build -d`.

## Production gates

- TLS and restrictive reverse proxy.
- Durable encrypted storage and tested backups.
- Network access restricted to trusted gateways.
- Rate limiting, abuse protection and monitoring for the public inquiry endpoint.
- Data minimization, documented retention/deletion and an approved customer-data path.
- Inquiry ownership and notification/CRM handling.
- SSO or appropriately managed access controls for the intended deployment.
- PostgreSQL or another supported durable database for multi-instance/high-availability needs.
- Security review, incident procedure and recovery exercises.
- Written customer authorization and contractual scope before processing data.

Do not claim enterprise production readiness, independent audit status, security certification or native integrations until those gates have been completed and verified.
