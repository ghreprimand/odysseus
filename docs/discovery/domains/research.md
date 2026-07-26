# Research

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## RESEARCH-001 — Deep Research Execution Engine & SSE Progress Streaming

- **Domain**: `research`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Executes multi-step recursive deep research tasks, web page scraping, synthesis, and streams live progress.

### Evidence summary

- `routes/research/research_routes.py` — `@router.post('/api/research/start')` — Initiates deep research job.
- `src/deep_research.py` — `DeepResearchEngine` — Recursive search and summary crawler.

### Unknowns

- High memory consumption when parsing multi-megabyte HTML target pages.

## RESEARCH-002 — Research Library, Detail View & Image Controls

- **Domain**: `research`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Stores completed research reports, generated diagrams, reference links, and manages image visibility.

### Evidence summary

- `routes/research/research_routes.py` — `@router.get('/api/research/library')` — Returns all saved research reports.

### Unknowns

- Orphaned report files if storage directory is modified out-of-band.

## RESEARCH-003 — Web Search Engine Integration (SearXNG & Multi-Provider)

- **Domain**: `research`
- **Status**: `verified`
- **Evidence Maturity**: `E1`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires an active SearXNG instance or external search API provider.

### Purpose

Queries SearXNG, DuckDuckGo, or Google Search instances to retrieve web search snippets.

### Evidence summary

- `routes/search_routes.py` — `setup_search_routes` — Defines /api/search, /api/search/config, and /api/search/query endpoints.
- `src/search/core.py` — `SearchEngine` — Compatibility module aliasing services.search.core.
- `tests/test_search_ranking.py` — `test_news_queries_prefer_news_sources_over_sports_and_social_results` — Tests search result domain ranking and scoring.

### Unknowns

- Search provider IP throttling or rate-limiting.

## RESEARCH-004 — Research Result Peeking & Topic Spinoff Generation

- **Domain**: `research`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Extracts preliminary research snippets and spawns child research sessions focused on specific sub-topics.

### Evidence summary

- `routes/research/research_routes.py` — `@router.post('/api/research/spinoff/{session_id}')` — Spawns child research session for specific query.

### Unknowns

- Deep recursion tree depth when spawning multiple nested spinoffs.
