# Email

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## EMAIL-001 — Email Account Setup, IMAP/SMTP Connection & Polling

- **Domain**: `email`
- **Status**: `verified`
- **Evidence Maturity**: `E1`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires a controlled live IMAP account and network access.

### Purpose

Configures IMAP/SMTP email accounts, validates TLS certificates, and polls background inbox updates.

### Evidence summary

- `routes/email_routes.py` — `setup_email_routes` — Sets up email account management and synchronization routes.
- `routes/email_pollers.py` — `_start_poller` — Background poller for email inbox synchronization.
- `tests/test_service_health_email.py` — `test_email_ok_all_connect` — Tests IMAP connection health probing and status reporting.

### Unknowns

- Account lockouts if bad credentials are repeatedly polled.

## EMAIL-002 — Email Searching, Threading & Message Operations

- **Domain**: `email`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Parses email headers, folds signatures, groups messages into threads, and executes full-text email search.

### Evidence summary

- `routes/email_routes.py` — `@router.get('/search')` — Executes search across cached email headers and text.
- `src/email_thread_parser.py` — `parse_email_thread` — Builds conversation tree from Message-ID and In-Reply-To headers.

### Unknowns

- Malformed MIME email structures failing HTML sanitization.

## EMAIL-003 — Email Composition, Draft Management & Sending

- **Domain**: `email`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires a controlled live SMTP account and network access.

### Purpose

Creates, saves, and dispatches HTML/plaintext email messages via SMTP.

### Evidence summary

- `routes/email_routes.py` — `@router.post('/send')` — Sends email message via user SMTP credentials.

### Unknowns

- SMTP connection drop mid-send causing unsent mail state.

## EMAIL-004 — Email MCP Server & Codex Integration Bridge

- **Domain**: `email`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Exposes constrained email reading and draft capabilities to external Codex / MCP agents with scope checks.

### Evidence summary

- `mcp_servers/email_server.py` — `EmailMcpServer` — MCP server exposing email tools over stdio/SSE.
- `routes/codex_routes.py` — `setup_codex_routes` — Bridge endpoints for external Codex plugin integration.

### Unknowns

- Unauthorized mail sending if token scopes are improperly scoped.
