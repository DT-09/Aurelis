# Threat model

## Protected assets
Tenant records, API credentials, authority contracts, evidence, policy definitions, decisions and audit history.

## Implemented controls
- One-time bootstrap guarded by a deployment secret.
- Salted PBKDF2-HMAC-SHA256 API-key verification.
- Tenant-scoped queries and foreign-key constraints.
- Strict request schemas; unknown fields are rejected.
- Default-deny action authorization; explicit denials take precedence.
- Evidence content hashes and a per-tenant hash-linked audit chain.
- Production startup rejects weak bootstrap secrets and wildcard CORS.
- Non-root container, read-only root filesystem, dropped capabilities.

## Known limitations
- No SSO, SCIM, fine-grained RBAC, or authenticated human approval.
- No key-revocation endpoint yet; rotation creates a new key but does not revoke the old one.
- Hash chaining detects local modification but cannot stop a privileged database operator rewriting the whole chain. Use externally signed, immutable checkpoints for stronger tamper evidence.
- No automatic runtime interception, model monitoring, or tool sandbox.
- SQLite is single-instance storage; no HA claim.
- No independent penetration test or compliance certification.

Do not expose the API directly to untrusted networks without TLS termination, network controls, backups, monitoring and rate limiting. Never commit secrets or customer evidence.
