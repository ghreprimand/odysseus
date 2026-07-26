# Skill

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## SKILL-001 — Dynamic Skill Management & Code Execution Engine

- **Domain**: `skill`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Allows users to create, import, edit, test, and execute custom Python/Markdown skills dynamically.

### Evidence summary

- `routes/skills_routes.py` — `setup_skills_routes` — Exposes CRUD and remote import routes for user skills.
- `services/memory/skills.py` — `SkillsManager` — Handles skill storage, parsing, and execution.

### Unknowns

- Arbitrary code execution risks if skill import URL is untrusted.
