# Security Checklist & Threat Model

## Data classification
- Public: doctor specialty, non-sensitive availability metadata.
- Internal: operational metrics and configuration.
- Confidential: account identifiers, booking history.
- Highly confidential: prescriptions, consultation notes, payment references, authentication secrets.

## Attack surface
API gateway, authentication endpoints, booking APIs, admin APIs, PostgreSQL, Redis, workers, CI/CD and third-party payment/notification providers.

## OWASP controls
- Broken access control: JWT + RBAC; every resource access checks ownership/role.
- Injection: SQLAlchemy parameterized queries; Pydantic validation.
- Authentication failures: password hashing, short-lived access tokens, MFA flag; production should add refresh-token rotation and WebAuthn/TOTP.
- Sensitive data exposure: TLS, encrypted database/storage, field-level encryption for highly sensitive fields.
- Security misconfiguration: environment secrets, non-root container, restricted CORS in production.
- Vulnerable components: dependency pinning + CI dependency/container scanning.
- Logging failures: immutable audit events for privileged and clinical actions.
- DoS: gateway rate limiting, bounded request sizes, timeouts and circuit breakers.

## Key management
Use cloud KMS/secret manager. Never commit JWT/payment/database secrets. Rotate signing/encryption keys periodically with key IDs and overlapping verification windows.

## Audit
Record actor, action, resource, timestamp, request correlation ID and outcome. Do not put passwords, tokens or full clinical content into logs.

## MFA/RBAC
Roles: patient, doctor, admin. Production admin accounts require MFA. Least privilege applies to DB users, CI identities and service accounts.

## Resilience
Use timeouts, exponential backoff with jitter, circuit breakers, dead-letter queues and idempotency keys. Do not blindly retry non-idempotent payment operations.

## Compliance
Retention, consent, deletion/export workflows and regional data residency must be configured according to the applicable healthcare/privacy requirements and Amrutam's legal policy. The implementation intentionally avoids assuming a specific jurisdictional compliance framework.
