# Note

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## NOTE-001 — Interactive Notes & Checklist Management

- **Domain**: `note`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides Google Keep-style notes, rich markdown text, checklist items, pinning, color tags, and reminders.

### Evidence summary

- `routes/note/note_routes.py` — `@router.get('')` — Lists all user notes with pin and archive states.
- `static/js/notes.js` — `initNotesView` — Main interactive notes grid and modal manager.

### Unknowns

- Concurrent edits on note item checkboxes.
