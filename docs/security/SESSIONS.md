# Sessions

Sessions track:

- principal
- issued / expires
- roles
- permissions
- authentication method
- token fingerprint (never raw token in API/audit)

## Lifecycle

1. `SESSION_STORE.create(...)` → `(session, opaque_token)`
2. `resolve_token(token)` → active session or error
3. `revoke(session_id)` → subsequent resolve fails with `session_revoked`

## HTTP

`GET /security/sessions` returns public metadata only (fingerprints, no secrets).

Out of scope: SSO, OAuth, SAML, OIDC, LDAP, Active Directory.
