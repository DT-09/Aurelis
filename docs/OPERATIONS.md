# Operations

## Local run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export AURELIS_BOOTSTRAP_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(40))')"
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Development API docs are at /docs.

## Bootstrap

```bash
curl -X POST http://127.0.0.1:8000/v1/bootstrap \
  -H "X-Bootstrap-Key: $AURELIS_BOOTSTRAP_KEY" \
  -H "Content-Type: application/json" \
  -d '{"organization_name":"Example"}'
```

Store the returned API key in a secret manager. It is shown only once.

## Core workflow
1. Register an asset at POST /v1/assets with explicit authority_contract.allowed_actions.
2. Add source evidence at POST /v1/evidence.
3. Define deterministic rules at POST /v1/policies.
4. Evaluate metrics and evidence at POST /v1/assessments.
5. Request action authorization at POST /v1/authority/authorize.
6. Rotate credentials with POST /v1/keys; revoke the old key with DELETE /v1/keys/{key_id}. Keep at least one active key.\n7. Verify the audit history at GET /v1/audit/verify.

## Container

Set AURELIS_BOOTSTRAP_KEY to a random value of at least 32 characters and AURELIS_CORS_ORIGINS to explicit origins, then run docker compose up --build -d.

## Production checklist
- TLS and restrictive reverse proxy.
- Durable encrypted storage and tested backups.
- Network access restricted to trusted gateways.
- Monitoring for health, latency, storage and failed decisions.
- Enforcement integrated at the actual tool-execution boundary.
- Approver identity and action/context binding handled by the consuming system.
- Threat model, security review and recovery exercises completed for the target deployment.
