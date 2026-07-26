# Security

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## SECURITY-001 — Authentication, Session Cookies & User Management

- **Domain**: `security`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Handles bcrypt password hashing, session cookie issuance, authentication enforcement, and user administration.

### Evidence summary

- `routes/auth_routes.py` — `@router.post('/login')` — Authenticates credentials and sets session cookie.
- `core/auth.py` — `AuthManager` — Handles user creation, password verification, and session tokens.

### Unknowns

- Cookie session hijack if deployed over unencrypted HTTP without HTTPS cookie flags.

## SECURITY-002 — System Vault Encrypted Secret Storage

- **Domain**: `security`
- **Status**: `verified`
- **Evidence Maturity**: `E1`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires installed Bitwarden CLI (`bw`) executable.

### Purpose

Encrypts API keys, passphrases, and third-party secrets on disk using AES-GCM / PBKDF2 key derivation.

### Evidence summary

- `routes/vault_routes.py` — `setup_vault_routes` — Admin routes for vault configuration, login, unlock, lock, and logout.
- `src/secret_storage.py` — `SecretStorage` — Fernet symmetric key DB secret encryption.
- `tests/test_vault_password_not_in_argv.py` — `test_bw_password_not_in_argv` — Verifies master password is fed via stdin and never appears in process argv.

### Unknowns

- Loss of vault master passphrase renders all encrypted secrets permanently unrecoverable.

## SECURITY-003 — API Token Management & Scope Access Control

- **Domain**: `security`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Generates scoped API bearer tokens (read/write/admin) for external tool and script authentication.

### Evidence summary

- `routes/api_token_routes.py` — `setup_api_token_routes` — Exposes API token creation, scope assignment, and revocation.
- `core/database.py` — `ApiToken` — SQLAlchemy ORM schema for API tokens and permissions.

### Unknowns

- Leaked API bearer tokens with excessive permission scopes.

## SECURITY-004 — Prompt Security & Injection Defense Engine

- **Domain**: `security`
- **Status**: `verified`
- **Evidence Maturity**: `E1`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Scans system prompts and external inputs for prompt injection attempts, jailbreaks, and sensitive data leaks.

### Evidence summary

- `src/prompt_security.py` — `untrusted_context_message` — Wraps untrusted context with guard delimiters and sets metadata.trusted = False.
- `src/tool_security.py` — `NON_ADMIN_BLOCKED_TOOLS` — Enforces tool execution safety for non-admin user roles.
- `tests/test_skill_index_prompt_injection.py` — `test_skill_index` — Verifies skill index descriptions cannot leak into trusted system prompts.
- `tests/test_tool_output_prompt_injection.py` — `test_tool_output` — Tool output injection guards.

### Unknowns

- False positives blocking legitimate complex coding or security prompts.

## SECURITY-005 — URL & Path Confinement Security Guards

- **Domain**: `security`
- **Status**: `verified`
- **Evidence Maturity**: `E1`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Prevents SSRF attacks and path traversal by validating target IP addresses and resolving symlinks.

### Evidence summary

- `src/url_safety.py` — `check_outbound_url` — Rejects non-HTTP(S) schemes, link-local, cloud metadata SSRF addresses.
- `src/url_security.py` — `validate_public_http_url` — Validates public-facing endpoints.
- `tests/test_url_safety.py` — `test_url_safety` — Scheme validation, cloud metadata SSRF rejection, IP classification.
- `tests/test_tool_path_confinement.py` — `test_path_confinement` — Path traversal checks.
- `tests/test_workspace_confine.py` — `test_workspace_confine` — Workspace confinement checks.

### Unknowns

- DNS rebinding attacks if IP address is re-resolved post-validation.

## SECURITY-006 — HTTP Security Headers Middleware

- **Domain**: `security`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Injects standard OWASP HTTP security headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options).

### Evidence summary

- `core/middleware.py` — `SecurityHeadersMiddleware` — Sets strict security headers and CSP nonces on HTTP responses.

### Unknowns

- Strict Content Security Policy (CSP) blocking third-party embedded web resources.

## SECURITY-007 — Admin System Data Wipe ('Danger Zone')

- **Domain**: `security`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides administrative reset operations to wipe sessions, cache, uploaded files, or factory reset state.

### Evidence summary

- `routes/admin_wipe/admin_wipe_routes.py` — `@router.delete('/wipe/{kind}')` — Executes systemic data wipe based on requested scope.

### Unknowns

- Accidental catastrophic data loss if triggered without user confirmation.
