# Source Provenance & Audit Baseline

## Target Repository & Snapshot

- **Repository**: `odysseus-dev/odysseus`
- **Branch**: `discovery`
- **Pinned Commit SHA**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Snapshot Date**: `2026-07-23T14:49:02Z`

## Discovery Package Organization

The public discovery documentation package under `docs/discovery/` is structured as follows:

- `feature-catalog.json`: Canonical machine-readable JSON catalog containing 79 feature records.
- `feature-catalog.md`: Human-readable summary derived from `feature-catalog.json`.
- `BASELINE-STATUS.md`: Publication status, evidence-validation snapshot, and durable maintainer guidance.
- `audit-method.md`: Audit rules, scope, and evidence maturity definitions (E0 to E4).
- `domains/`: 16 functional domain markdown files detailing feature implementations.
- `references/`: Audit provenance and repository snapshot metadata.
- `tools/`: Structural, consistency, and evidence validators with focused evidence-validator tests.

## Exclusion Principles

This public documentation package explicitly excludes:
- Internal planning artifacts or private meeting notes.
- Machine-specific filesystem paths or user environments.
- API keys, credentials, or private service endpoints.
- Application code or automated test mutations.
