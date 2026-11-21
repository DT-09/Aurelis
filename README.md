# Aurelis

**AI authority and assurance infrastructure.** A vendor-neutral control plane that makes AI identity, delegated authority, assurance evidence, policy decisions and audit history explicit.

Aurelis follows one governing rule: an AI system receives no authority by implication. An action must be explicitly granted, must not be explicitly denied, and must satisfy any configured human-approval gate. Unknown actions default to deny.

## Integrated control loop

`Identity → Authority → Evidence → Policy → Decision → Audit`

| System | Capability |
|---|---|
| Identity & ownership | Tenant-scoped credentials and AI asset registry |
| Authority | Per-asset contracts for allowed, denied and human-gated actions |
| Assurance | Deterministic policy evaluation: ASSURED / DEGRADED / BLOCKED / UNKNOWN |
| Evidence | Asset-bound source records with SHA-256 content hashes |
| Audit | Per-tenant hash-linked event history and integrity verification |
| Operator surface | Browser console and versioned JSON API |

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

Save the returned API key securely. It is shown only once; only a salted PBKDF2-HMAC-SHA256 hash is stored.

## API workflow

Tenant endpoints require `X-Aurelis-Key: aur_<key-id>.<secret>`.

1. `POST /v1/assets` — register an asset and authority contract.
2. `POST /v1/evidence` — attach evidence to the asset.
3. `POST /v1/policies` — define deterministic metric rules.
4. `POST /v1/assessments` — evaluate metrics and evidence.
5. `POST /v1/authority/authorize` — request a default-deny action decision.
6. `POST /v1/keys` and `DELETE /v1/keys/{key_id}` — rotate and revoke credentials without locking out the organization.\n7. `GET /v1/audit/events` and `GET /v1/audit/verify` — inspect and verify the audit trail.

See [Architecture](docs/ARCHITECTURE.md), [Threat model](docs/THREAT_MODEL.md), and [Operations](docs/OPERATIONS.md).

## Deployment and release boundary

Dockerfile and Docker Compose configuration are included. SQLite is the embedded, single-instance persistence layer. This release does **not** claim multi-instance high availability, automatic runtime interception, SSO/SCIM, fine-grained RBAC, independently authenticated human approval, external immutable audit anchoring, compliance certification, or independent security testing.

Integrators must enforce decisions at the actual tool-execution boundary and fail closed when Aurelis is unavailable. A passing assessment means supplied metrics met supplied rules; it is not proof of universal safety or regulatory compliance.

## Development

```bash
pip install -r requirements.txt
python -m compileall -q app tests
pytest -q
```

## License

No license has been declared. All rights reserved unless the repository owner adds an explicit license.