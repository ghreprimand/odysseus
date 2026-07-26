# Memory

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## MEMORY-001 — Persistent Long-Term Memory & Vector Indexing

- **Domain**: `memory`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Extracts facts, user preferences, and temporal memories from chat sessions into vector/relational storage.

### Evidence summary

- `routes/memory/memory_routes.py` — `@router.get('')` — Fetches long-term user memory timeline.
- `services/memory/memory_extractor.py` — `MemoryExtractor` — LLM-driven fact extraction from conversation transcripts.

### Unknowns

- Conflicting memory facts extracted from contradictory user prompts.
