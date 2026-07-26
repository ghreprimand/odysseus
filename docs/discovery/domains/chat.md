# Chat

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## CHAT-001 — Core Chat Streaming & SSE Message Generation

- **Domain**: `chat`
- **Status**: `verified`
- **Evidence Maturity**: `E2`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires access to a live LLM provider endpoint (OpenAI API key or local Ollama server).

### Purpose

Handles real-time Server-Sent Events (SSE) chat streaming, token rendering, and model response generation.

### Evidence summary

- `routes/chat_routes.py` — `chat_stream` — POST /api/chat_stream SSE endpoint; builds the shared chat context, then dispatches to the chat-mode or agent-mode streaming path.
- `routes/chat_helpers.py` — `build_chat_context` — Shared context builder invoked by chat_stream; runs message preprocessing and assembles the memory/RAG/web context preface.
- `src/chat_handler.py` — `ChatHandler.preprocess_message` — Message preprocessing (attachments, URLs, tool preprocessing) reached from build_chat_context via routes/chat_helpers.py:preprocess.
- `src/chat_processor.py` — `ChatProcessor.build_context_preface` — Builds the retrieval and web-source context preface injected into the streamed request.
- `src/llm_core.py` — `stream_llm_with_fallback` — Chat-mode streaming dispatcher called from chat_stream; wraps stream_llm with an ordered provider fallback chain.
- `src/llm_core.py` — `stream_llm` — Per-request streaming entry wrapped by stream_llm_with_fallback; acquires the local model slot and delegates to _stream_llm_inner.
- `src/agent_loop.py` — `stream_agent_loop` — Agent-mode streaming path called from chat_stream when the request selects agent mode.
- `tests/test_chat_metrics.py` — `test_stream_llm_passes_through_llamacpp_timings` — Inspected unit test asserting stream_llm forwards backend generation timings into the emitted metrics chunk.
- `tests/test_resend_message_nondestructive.py` — `test_resend_message_does_not_truncate_by_default` — Inspected unit test asserting the frontend resend path does not truncate prior conversation turns.

### Unknowns

- Stream interruption on connection drops requires retry logic.

## CHAT-002 — Session Management & Conversation State

- **Domain**: `chat`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Manages session creation, listing, switching, renaming, and persistence of conversation metadata.

### Evidence summary

- `routes/session_routes.py` — `@router.get('/api/sessions')` — Lists active sessions filtered by user owner scope.
- `core/session_manager.py` — `SessionManager` — Provides thread-safe session storage operations.

### Unknowns

- Concurrent file writes to sessions.json under high load.

## CHAT-003 — Chat History & Message Editing/Truncation

- **Domain**: `chat`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides history retrieval, message content updating, message deletion, and history branch truncation.

### Evidence summary

- `routes/history/history_routes.py` — `@router.get('/api/history/{session_id}')` — Fetches message history timeline for a session.
- `routes/history_routes.py` — `_sys.modules[__name__] = _canonical` — Backward-compatibility shim module.

### Unknowns

- Truncating messages re-indexes context window and clears cached tool calls.

## CHAT-004 — File & Multimodal Attachment Handling

- **Domain**: `chat`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Handles uploading, mime validation, image preview, vision encoding, and file attachments in chat messages.

### Evidence summary

- `routes/upload_routes.py` — `@router.post('')` — Accepts multi-part file uploads and generates vision metadata.
- `src/upload_handler.py` — `UploadHandler.save_file` — Validates upload size and atomicity on disk.

### Unknowns

- Large file uploads may consume server disk space if cleanup task fails.

## CHAT-005 — Chat Message Search

- **Domain**: `chat`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Enables full-text keyword search across stored chat messages and sessions.

### Evidence summary

- `routes/search_routes.py` — `setup_search_routes` — Registers chat message search endpoint.
- `src/session_search.py` — `search_sessions` — Executes query matching against session transcripts.

### Unknowns

- Full table scans on un-indexed text columns for very large databases.

## CHAT-006 — System Prompts & Preset Management

- **Domain**: `chat`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides creation, selection, and customization of system prompt presets for chat sessions.

### Evidence summary

- `routes/preset_routes.py` — `setup_preset_routes` — API routes for listing and modifying system prompt presets.
- `src/preset_manager.py` — `PresetManager` — Disk-backed manager for prompt presets.

### Unknowns

- Invalid JSON syntax in user presets file can corrupt preset loading.

## CHAT-007 — Emoji Rendering & Twemoji SVG Proxy

- **Domain**: `chat`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Proxies Twemoji SVG icons locally to render flat SVG emojis in message text without external CDN dependencies.

### Evidence summary

- `routes/emoji_routes.py` — `setup_emoji_routes` — Serves locally cached Twemoji SVGs.

### Unknowns

- First request fetches SVG from remote CDN before caching locally.

## CHAT-008 — Input History Recall (Arrow Up)

- **Domain**: `chat`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Allows users to cycle through previously sent prompt messages in the chat composer input using Arrow-Up/Down keys.

### Evidence summary

- `static/js/composerArrowUpRecall.js` — `initComposerRecall` — Listens for ArrowUp keypress on composer textarea.

### Unknowns

- Client-side browser storage limits.

## CHAT-009 — Context Window Compaction & Truncation

- **Domain**: `chat`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Compacts session transcript history when prompt size exceeds context limits using summarization.

### Evidence summary

- `routes/history/history_routes.py` — `@router.post('/api/session/{session_id}/compact')` — Triggers context summarization and compaction.
- `src/context_compactor.py` — `compact_context` — Executes context token pruning and summary generation.

### Unknowns

- Aggressive compaction may discard subtle user instructions.
