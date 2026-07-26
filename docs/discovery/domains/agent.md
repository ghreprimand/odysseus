# Agent

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## AGENT-001 — Autonomous Agent Loop & Tool Execution Engine

- **Domain**: `agent`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Executes multi-step agent reasoning loops, tool invocation parsing, and automated response generation.

### Evidence summary

- `src/agent_loop.py` — `run_agent_loop` — Core loop evaluating model tool requests and executing handlers.
- `src/tool_execution.py` — `execute_tool_call` — Dispatches tool invocation requests to underlying tool handlers.

### Unknowns

- Infinite tool loop if termination condition fails.

## AGENT-002 — Scheduled Tasks & Event Bus Dispatcher

- **Domain**: `agent`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Schedules background recurring or delayed tasks, emits event bus triggers, and executes automated flows.

### Evidence summary

- `routes/task_routes.py` — `@router.get('')` — Fetches active scheduled tasks.
- `src/task_scheduler.py` — `TaskScheduler` — Async task scheduler dispatching cron and delay triggers.

### Unknowns

- Task execution failure handling on system restart.

## AGENT-003 — Webhook Event Subscriptions & Trigger Processing

- **Domain**: `agent`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Manages incoming/outgoing webhook subscriptions, endpoint authentication tokens, and event triggers.

### Evidence summary

- `routes/webhook_routes.py` — `@router.get('/webhooks')` — Returns list of registered webhooks.
- `src/webhook_manager.py` — `WebhookManager` — Handles payload delivery and signature verification.

### Unknowns

- SSRF risks when contacting external webhook URLs if unvalidated.

## AGENT-004 — Assistant Settings, Task Check-Ins & Background Job Monitor

- **Domain**: `agent`
- **Status**: `partial`
- **Evidence Maturity**: `E1`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Manages per-user assistant sessions and scheduled check-in settings, drains background job completions, and retains a legacy no-op activity logging shim.

### Evidence summary

- `routes/assistant_routes.py` — `setup_assistant_routes` — Active assistant session, settings, manual check-in, run-status and timezone-list endpoints, including the owner-scoping guards.
- `src/bg_monitor.py` — `_drain_agent` — Runs the agent loop headless against a session to produce the background-job follow-up turn.
- `src/bg_monitor.py` — `_run_followup` — Drains completed background jobs and auto-continues the owning session, deferring while a live turn is in progress.
- `src/assistant_log.py` — `log_to_assistant` — Legacy no-op activity logging shim retained for existing callers; documented as inactive rather than as current behaviour.

### Unknowns

- Route `/api/assistant/logs` cited in legacy docs is absent from assistant router.
- Existing unit test `tests/cli/test_logs_cli_resolve_nonstring.py` tests CLI target-name resolution logic, not active assistant routes or bg_monitor execution loop.

## AGENT-005 — Model Context Protocol (MCP) Server Integration

- **Domain**: `agent`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Integrates external MCP servers over stdio/SSE to expand agent capabilities dynamically.

### Evidence summary

- `routes/mcp_routes.py` — `setup_mcp_routes` — Exposes management endpoints for external MCP servers.
- `src/mcp_manager.py` — `McpManager` — Manages MCP server subprocess lifecycles.

### Unknowns

- Subprocess leaks if external MCP server process fails to terminate clean.

## AGENT-006 — AI Interaction Tools & Pipeline Orchestration

- **Domain**: `agent`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides specialized AI interaction tools for agent self-debugging, debate, and multi-model collaboration.

### Evidence summary

- `src/ai_interaction.py` — `init_ai_interaction_tools` — Registers specialized multi-agent interaction primitives.
- `src/builtin_actions.py` — `execute_builtin_action` — Executes pre-built action intent sequences.

### Unknowns

- High API token consumption during extended agent debates.

## AGENT-007 — Subprocess & Background Job Execution Tools

- **Domain**: `agent`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides sandboxed bash/shell tool execution capabilities with output streaming and background tracking.

### Evidence summary

- `src/agent_tools/subprocess_tools.py` — `run_command` — Executes shell commands in background/foreground.
- `src/bg_jobs.py` — `JobManager` — Tracks async background subprocess tasks.

### Unknowns

- Arbitrary shell command execution permissions if sandbox confinement fails.
