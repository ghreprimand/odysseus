# Model

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## MODEL-001 — Multi-Provider LLM Model Discovery & Metadata Management

- **Domain**: `model`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Discovers models from OpenAI, Anthropic, Ollama, vLLM, LMStudio, OpenRouter, and Google AI Studio endpoints.

### Evidence summary

- `routes/model_routes.py` — `@router.get('/api/models')` — Returns unified list of available models across providers.
- `src/model_discovery.py` — `ModelDiscovery.discover_all` — Queries connected provider endpoints for available model IDs.

### Unknowns

- Remote endpoint timeouts may slow down full discovery refresh.

## MODEL-002 — Model Capability & Context Limits Detection

- **Domain**: `model`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Detects vision, tool calling, reasoning, and context window limits for connected model endpoints.

### Evidence summary

- `src/model_capabilities.py` — `get_model_capabilities` — Maps model names to vision and tool support flags.
- `src/endpoint_resolver.py` — `resolve_endpoint_headers` — Resolves auth headers and target URLs for model endpoints.

### Unknowns

- Incorrect context limit metadata for unlisted custom fine-tunes.

## MODEL-003 — LLM Core Provider Communication & Fallback Routing

- **Domain**: `model`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Provider dispatch, header injection and fallback advancement are only observable against a reachable LLM provider endpoint; not exercised in this documentation pass.

### Purpose

Manages HTTP request dispatching, authorization header injection, and fallback provider routing for LLM calls.

### Evidence summary

- `src/llm_core.py` — `llm_call_async` — Non-streaming provider request dispatcher: resolves the endpoint, injects authorization headers and executes the HTTP call.
- `src/llm_core.py` — `llm_call_async_with_fallback` — Ordered fallback wrapper that retries llm_call_async across the configured candidate endpoints.
- `src/llm_core.py` — `stream_llm_with_fallback` — Ordered fallback wrapper for the streaming path; advances to the next candidate when a provider yields an empty completion.

### Unknowns

- Unexpected API changes in upstream third-party model providers.

## MODEL-004 — Model Selection & Display Ordering Preferences

- **Domain**: `model`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Allows pinning, sorting, and hiding specific models in the UI selection dropdown.

### Evidence summary

- `routes/model_routes.py` — `@router.post('/order')` — Saves custom model display order preference.

### Unknowns

- Stale model IDs in custom order lists after model endpoints are removed.

## MODEL-005 — Side-by-Side Model Comparison (A/B Testing)

- **Domain**: `model`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Enables dual-model side-by-side response evaluation, arena scoring, and latency comparison.

### Evidence summary

- `routes/compare/compare_routes.py` — `@router.post('/start')` — Starts a parallel dual-model comparison stream.
- `static/js/compare/index.js` — `initCompareView` — Renders side-by-side model chat panes.

### Unknowns

- High memory and network usage when streaming two model responses simultaneously.

## MODEL-006 — GitHub Copilot Device Flow Authentication

- **Domain**: `model`
- **Status**: `verified`
- **Evidence Maturity**: `E2`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires an interactive GitHub Copilot OAuth device-flow account.

### Purpose

Authenticates with GitHub Copilot via OAuth device flow to use Copilot models directly.

### Evidence summary

- `routes/copilot_routes.py` — `setup_copilot_routes` — Builds the Copilot device-flow router at prefix /api/copilot, wiring _start_device_flow and _poll_device_flow.
- `routes/device_flow.py` — `create_device_flow_router` — Shared factory registering POST /device/start and POST /device/poll under the caller-supplied prefix.
- `src/copilot.py` — `request_device_code` — Issues the GitHub device-code request that begins the Copilot OAuth device flow.
- `src/copilot.py` — `poll_access_token` — Polls GitHub for the access token once the user has authorized the device code.
- `tests/test_provider_device_flow_js.py` — `test_copilot_success_uses_complete_verification_uri` — Inspected unit test asserting the Copilot device-flow runner surfaces the complete verification URI returned by the backend.

### Unknowns

- Token expiration requires manual device re-authentication.

## MODEL-007 — ChatGPT Subscription Device Flow Authentication

- **Domain**: `model`
- **Status**: `verified`
- **Evidence Maturity**: `E2`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires an interactive ChatGPT subscription OAuth flow.

### Purpose

Authenticates with ChatGPT Pro/Plus subscription tokens via device login flow.

### Evidence summary

- `routes/chatgpt_subscription_routes.py` — `setup_chatgpt_subscription_routes` — Builds the ChatGPT subscription device-flow router at prefix /api/chatgpt-subscription.
- `routes/device_flow.py` — `create_device_flow_router` — Shared factory registering POST /device/start and POST /device/poll under the caller-supplied prefix.
- `src/chatgpt_subscription.py` — `request_device_code` — Issues the ChatGPT device-authorization request that begins the subscription OAuth device flow.
- `src/chatgpt_subscription.py` — `poll_device_auth` — Polls the ChatGPT device-authorization endpoint for completion using the stored device_auth_id and user_code.
- `tests/test_provider_device_flow_js.py` — `test_chatgpt_success_uses_plain_verification_uri` — Inspected unit test asserting the ChatGPT device-flow runner uses the plain verification URI rather than the Copilot complete-URI form.

### Unknowns

- Changes in OpenAI auth endpoint security challenges.

## MODEL-008 — Embedding Model Lane & Vector Provider Setup

- **Domain**: `model`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Configures local sentence-transformers, FastEmbed, or remote OpenAI embedding model lanes.

### Evidence summary

- `routes/embedding_routes.py` — `setup_embedding_routes` — Provides embedding provider configuration endpoints.
- `src/embeddings.py` — `EmbeddingManager` — Generates dense vector embeddings for RAG and memory.

### Unknowns

- First-time download of heavy PyTorch model weights on CPU-only machines.
