"""Read-only system diagnostics used by the admin System settings tab."""

import asyncio
import json
import os
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy import text

import core.database as database
from core.constants import SEARXNG_INSTANCE
from src.integrations import load_integrations
from src.settings import load_features, load_settings

CHECK_TIMEOUT = 1.25
SessionLocal = database.SessionLocal
EmailAccount = getattr(database, "EmailAccount", object())
McpServer = getattr(database, "McpServer", object())
ModelEndpoint = getattr(database, "ModelEndpoint", object())
_SECRET_KEY_RE = re.compile(r"(api[_-]?key|authorization|bearer|cookie|password|secret|token)", re.I)
_SECRET_VALUE_PATTERNS = [
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)\b(bearer|authorization)\s+([A-Za-z0-9._~+/=-]{12,})"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*([^\s,;]+)"),
]


def _check(
    check_id: str,
    label: str,
    status: str,
    message: str,
    hint: Optional[str] = None,
    action: Optional[Dict[str, str]] = None,
    detail: Optional[str] = None,
) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "id": check_id,
        "label": label,
        "status": status,
        "message": message,
    }
    if hint:
        item["hint"] = hint
    if action:
        item["action"] = action
    if detail:
        item["detail"] = detail
    return item


def _group(group_id: str, label: str, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"id": group_id, "label": label, "checks": checks}


def _overall(groups: List[Dict[str, Any]]) -> str:
    statuses = [c.get("status") for g in groups for c in g.get("checks", [])]
    if "error" in statuses:
        return "error"
    if "warning" in statuses:
        return "degraded"
    return "healthy"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


async def _probe_http(url: str, timeout: float = CHECK_TIMEOUT) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        return await client.get(url)


def _in_docker() -> bool:
    if os.path.exists("/.dockerenv"):
        return True
    try:
        with open("/proc/1/cgroup", "r", encoding="utf-8", errors="ignore") as fh:
            return any(marker in fh.read() for marker in ("docker", "containerd", "kubepods"))
    except Exception:
        return False


def _ollama_base_url() -> str:
    return (
        os.getenv("OLLAMA_BASE_URL")
        or os.getenv("OLLAMA_URL")
        or ("http://host.docker.internal:11434/v1" if _in_docker() else "http://127.0.0.1:11434/v1")
    )


def _ollama_api_root(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if base.endswith("/v1"):
        return base[:-3].rstrip("/")
    if base.endswith("/api"):
        return base[:-4].rstrip("/")
    return base


def _host_is_localish(host: str) -> bool:
    host = (host or "").lower()
    if host in {"localhost", "127.0.0.1", "::1", "0.0.0.0", "host.docker.internal"}:
        return True
    if host.startswith(("10.", "192.168.", "100.")):
        return True
    if host.startswith("172."):
        try:
            second = int(host.split(".", 2)[1])
            return 16 <= second <= 31
        except Exception:
            return False
    return False


def _is_local_endpoint(base_url: str) -> bool:
    try:
        parsed = urlparse(base_url if "://" in base_url else f"http://{base_url}")
        return _host_is_localish(parsed.hostname or "")
    except Exception:
        return False


def _git_revision() -> Optional[str]:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            check=False,
            capture_output=True,
            text=True,
            timeout=1,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _redact_text(value: str) -> str:
    text_value = value
    home = str(Path.home())
    if home and home != ".":
        text_value = text_value.replace(home, "~")
    for pattern in _SECRET_VALUE_PATTERNS:
        if pattern.groups >= 2:
            text_value = pattern.sub(lambda match: f"{match.group(1)} <redacted>", text_value)
        else:
            text_value = pattern.sub("<redacted>", text_value)
    return text_value


def _redact_obj(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: Dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            redacted[key_str] = "<redacted>" if _SECRET_KEY_RE.search(key_str) else _redact_obj(item)
        return redacted
    if isinstance(value, list):
        return [_redact_obj(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_obj(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _runtime_snapshot(settings: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
    return _redact_obj({
        "platform": platform.platform(),
        "python": platform.python_version(),
        "in_docker": _in_docker(),
        "cwd": str(Path.cwd()),
        "git_revision": _git_revision(),
        "data_dir_exists": Path("data").exists(),
        "features": {
            "rag": features.get("rag", True),
            "web_search": features.get("web_search", True),
        },
        "local_services": {
            "chroma": f"http://{os.getenv('CHROMADB_HOST', 'localhost')}:{os.getenv('CHROMADB_PORT', '8100')}",
            "ollama": _ollama_api_root(_ollama_base_url()),
        },
        "search": {
            "provider": settings.get("search_provider") or "default",
            "url": settings.get("search_url") or SEARXNG_INSTANCE or "",
        },
        "notifications": {
            "reminder_channel": settings.get("reminder_channel") or "browser",
        },
    })


def _models_url(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    if base.endswith("/v1"):
        return f"{base}/models"
    if base.endswith("/api"):
        return f"{base}/tags"
    return f"{base}/models"


def _safe_endpoint_label(ep: Any) -> str:
    name = getattr(ep, "name", "") or "endpoint"
    try:
        parsed = urlparse(getattr(ep, "base_url", "") or "")
        location = parsed.netloc or parsed.path
    except Exception:
        location = ""
    return f"{name} ({location})" if location else name


def _core_checks() -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        checks.append(_check("database", "Database", "ok", "SQLite is reachable."))
    except Exception as exc:
        checks.append(_check(
            "database",
            "Database",
            "error",
            "Database query failed.",
            "Check that data/app.db exists and the app process can read it.",
            detail=str(exc),
        ))
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    data_dir = Path("data")
    try:
        if not data_dir.exists():
            checks.append(_check(
                "data_dir",
                "Data directory",
                "warning",
                "data/ does not exist yet.",
                "Run setup.py or restart Odysseus so it can create its data directory.",
            ))
        elif os.access(data_dir, os.R_OK | os.W_OK):
            checks.append(_check("data_dir", "Data directory", "ok", "data/ is readable and writable."))
        else:
            checks.append(_check(
                "data_dir",
                "Data directory",
                "error",
                "data/ is not readable and writable by this process.",
                "Fix the ownership or permissions on the data directory.",
            ))
    except Exception as exc:
        checks.append(_check("data_dir", "Data directory", "error", "Could not inspect data/.", detail=str(exc)))
    return checks


async def _chroma_check(features: Dict[str, Any]) -> Dict[str, Any]:
    if not features.get("rag", True):
        return _check("chroma", "ChromaDB", "skipped", "RAG is disabled.")
    host = os.getenv("CHROMADB_HOST", "localhost")
    port = os.getenv("CHROMADB_PORT", "8100")
    base = f"http://{host}:{port}"
    for path in ("/api/v2/heartbeat", "/api/v1/heartbeat"):
        try:
            resp = await _probe_http(f"{base}{path}")
            if resp.is_success:
                return _check("chroma", "ChromaDB", "ok", f"Heartbeat succeeded at {base}.")
        except Exception:
            pass
    return _check(
        "chroma",
        "ChromaDB",
        "error",
        f"No heartbeat response from {base}.",
        "Start ChromaDB or update CHROMADB_HOST/CHROMADB_PORT in .env.",
    )


async def _ollama_check() -> Dict[str, Any]:
    base = _ollama_base_url()
    root = _ollama_api_root(base)
    try:
        resp = await _probe_http(f"{root}/api/tags")
        if not resp.is_success:
            return _check("ollama", "Ollama", "warning", f"Ollama returned HTTP {resp.status_code} at {root}.")
        data = resp.json() if resp.content else {}
        count = len(data.get("models") or [])
        return _check("ollama", "Ollama", "ok", f"{count} local model{'s' if count != 1 else ''} available at {root}.")
    except Exception as exc:
        return _check(
            "ollama",
            "Ollama",
            "warning",
            f"Ollama was not reachable at {root}.",
            "If you use Ollama, start it and add http://localhost:11434/v1 in Add Models.",
            action={"tab": "services", "label": "Add Models"},
            detail=str(exc),
        )


async def _model_endpoint_checks() -> List[Dict[str, Any]]:
    db = None
    try:
        db = SessionLocal()
        endpoints = db.query(ModelEndpoint).all()
    except Exception as exc:
        return [_check("model_endpoints", "Model endpoints", "error", "Could not read configured model endpoints.", detail=str(exc))]
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    enabled = [ep for ep in endpoints if getattr(ep, "is_enabled", True)]
    if not enabled:
        return [_check(
            "model_endpoints",
            "Model endpoints",
            "warning",
            "No enabled model endpoints are configured.",
            "Add a local Ollama/vLLM endpoint or a cloud provider before starting a chat.",
            action={"tab": "services", "label": "Add Models"},
        )]

    local_eps = [ep for ep in enabled if _is_local_endpoint(getattr(ep, "base_url", ""))]
    remote_count = len(enabled) - len(local_eps)
    summary = f"{len(enabled)} enabled endpoint{'s' if len(enabled) != 1 else ''}"
    if local_eps or remote_count:
        summary += f" ({len(local_eps)} local, {remote_count} remote/API)"

    checks = [_check("model_endpoints", "Model endpoints", "ok", summary, action={"tab": "services", "label": "Manage"})]

    async def probe(ep: Any) -> Dict[str, Any]:
        label = _safe_endpoint_label(ep)
        try:
            resp = await _probe_http(_models_url(getattr(ep, "base_url", "")))
            if resp.is_success:
                return _check(f"model_endpoint:{getattr(ep, 'id', label)}", label, "ok", "Model list endpoint responded.")
            return _check(
                f"model_endpoint:{getattr(ep, 'id', label)}",
                label,
                "warning",
                f"Model list returned HTTP {resp.status_code}.",
                "Use Add Models to test or update this endpoint.",
                action={"tab": "services", "label": "Open"},
            )
        except Exception as exc:
            return _check(
                f"model_endpoint:{getattr(ep, 'id', label)}",
                label,
                "warning",
                "Local model endpoint did not respond.",
                "Use Add Models to test or update this endpoint.",
                action={"tab": "services", "label": "Open"},
                detail=str(exc),
            )

    if local_eps:
        checks.extend(await asyncio.gather(*(probe(ep) for ep in local_eps[:5])))
        if len(local_eps) > 5:
            checks.append(_check("model_endpoint_extra", "More local endpoints", "skipped", f"{len(local_eps) - 5} additional local endpoints not probed."))
    return checks


async def _search_check(settings: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
    if not features.get("web_search", True):
        return _check("search", "Search", "skipped", "Web search is disabled.")
    provider = (settings.get("search_provider") or "").lower()
    if provider == "searxng":
        base = (settings.get("search_url") or SEARXNG_INSTANCE or "").strip().rstrip("/")
        if not base:
            return _check("search", "SearXNG", "warning", "SearXNG is selected but no URL is configured.", action={"tab": "search", "label": "Search"})
        try:
            resp = await _probe_http(base)
            if resp.is_success:
                return _check("search", "SearXNG", "ok", f"SearXNG is reachable at {base}.")
            return _check("search", "SearXNG", "warning", f"SearXNG returned HTTP {resp.status_code} at {base}.", action={"tab": "search", "label": "Search"})
        except Exception as exc:
            return _check(
                "search",
                "SearXNG",
                "warning",
                f"SearXNG was not reachable at {base}.",
                "Start SearXNG, change the search provider, or configure a fallback.",
                action={"tab": "search", "label": "Search"},
                detail=str(exc),
            )

    key_requirements = {
        "brave": ("brave_api_key", "Brave API key"),
        "google": ("google_pse_key", "Google PSE key"),
        "tavily": ("tavily_api_key", "Tavily API key"),
        "serper": ("serper_api_key", "Serper API key"),
    }
    if provider in key_requirements:
        key, label = key_requirements[provider]
        if settings.get(key):
            return _check("search", "Search", "ok", f"{provider} is configured.")
        return _check("search", "Search", "warning", f"{provider} is selected but {label} is missing.", action={"tab": "search", "label": "Search"})
    return _check("search", "Search", "ok", f"{provider or 'default'} search provider selected.")


def _email_check() -> Dict[str, Any]:
    db = None
    try:
        db = SessionLocal()
        accounts = db.query(EmailAccount).all()
    except Exception as exc:
        return _check("email", "Email", "error", "Could not read email accounts.", detail=str(exc))
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    enabled = [a for a in accounts if getattr(a, "enabled", True)]
    if not enabled:
        return _check("email", "Email", "skipped", "No enabled email accounts configured.", action={"tab": "integrations", "label": "Integrations"})
    complete = [a for a in enabled if getattr(a, "imap_host", "") or getattr(a, "smtp_host", "")]
    if len(complete) == len(enabled):
        return _check("email", "Email", "ok", f"{len(enabled)} enabled email account{'s' if len(enabled) != 1 else ''} configured.", action={"tab": "integrations", "label": "Integrations"})
    return _check("email", "Email", "warning", "One or more enabled email accounts are missing IMAP/SMTP hosts.", action={"tab": "integrations", "label": "Integrations"})


async def _ntfy_check(settings: Dict[str, Any]) -> Dict[str, Any]:
    channel = (settings.get("reminder_channel") or "browser").lower()
    integrations = [
        i for i in load_integrations()
        if i.get("enabled", True)
        and (i.get("preset") == "ntfy" or (i.get("name") or "").lower() == "ntfy")
        and i.get("base_url")
    ]
    if not integrations:
        status = "warning" if channel == "ntfy" else "skipped"
        message = "Reminder channel is ntfy but no enabled ntfy integration exists." if channel == "ntfy" else "No enabled ntfy integration configured."
        return _check("ntfy", "ntfy", status, message, action={"tab": "integrations", "label": "Integrations"})

    base = (integrations[0].get("base_url") or "").strip().rstrip("/")
    try:
        resp = await _probe_http(base)
        if resp.is_success:
            return _check("ntfy", "ntfy", "ok", f"ntfy server is reachable at {base}.", action={"tab": "integrations", "label": "Integrations"})
        return _check("ntfy", "ntfy", "warning", f"ntfy returned HTTP {resp.status_code} at {base}.", action={"tab": "integrations", "label": "Integrations"})
    except Exception as exc:
        return _check(
            "ntfy",
            "ntfy",
            "warning",
            f"ntfy was not reachable at {base}.",
            "Check the ntfy integration URL. This diagnostic does not publish a test notification.",
            action={"tab": "integrations", "label": "Integrations"},
            detail=str(exc),
        )


def _mcp_checks(mcp_manager: Any = None) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    if os.getenv("ODYSSEUS_DISABLE_MCP", "").lower() in {"1", "true", "yes"}:
        checks.append(_check("browser_mcp", "Browser MCP", "skipped", "Built-in MCP startup is disabled by ODYSSEUS_DISABLE_MCP."))
    elif mcp_manager and hasattr(mcp_manager, "get_all_statuses"):
        statuses = mcp_manager.get_all_statuses()
        browser = statuses.get("builtin_browser")
        if browser and browser.get("status") == "connected":
            tool_count = browser.get("tool_count", 0)
            checks.append(_check("browser_mcp", "Browser MCP", "ok", f"Browser MCP connected with {tool_count} tools."))
        elif browser:
            checks.append(_check(
                "browser_mcp",
                "Browser MCP",
                "warning",
                browser.get("error") or "Browser MCP is not connected.",
                "Run npx -y @playwright/mcp@latest --version once, then restart Odysseus.",
                action={"tab": "tools", "label": "Agent Tools"},
            ))
        else:
            checks.append(_check(
                "browser_mcp",
                "Browser MCP",
                "warning",
                "Browser MCP is not connected yet.",
                "It starts a few seconds after app startup if @playwright/mcp is available in the npx cache.",
                action={"tab": "tools", "label": "Agent Tools"},
            ))
    else:
        checks.append(_check("browser_mcp", "Browser MCP", "skipped", "Live MCP status is unavailable during this request."))

    db = None
    try:
        db = SessionLocal()
        servers = db.query(McpServer).all()
    except Exception as exc:
        checks.append(_check("mcp", "User MCP servers", "error", "Could not read MCP server config.", detail=str(exc)))
        return checks
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass
    enabled = [s for s in servers if getattr(s, "is_enabled", True)]
    if enabled:
        checks.append(_check("mcp", "User MCP servers", "ok", f"{len(enabled)} user MCP server{'s' if len(enabled) != 1 else ''} configured.", action={"tab": "tools", "label": "Agent Tools"}))
    else:
        checks.append(_check("mcp", "User MCP servers", "ok", "No user MCP servers configured.", action={"tab": "tools", "label": "Agent Tools"}))
    return checks


async def collect_system_diagnostics(mcp_manager: Any = None) -> Dict[str, Any]:
    settings = load_settings()
    features = load_features()
    ai_checks = await asyncio.gather(
        _chroma_check(features),
        _ollama_check(),
    )
    groups = [
        _group("core", "Core", _core_checks()),
        _group("local_ai", "Local AI", [*ai_checks, *(await _model_endpoint_checks())]),
        _group("research", "Research", [await _search_check(settings, features)]),
        _group("notifications", "Notifications", [_email_check(), await _ntfy_check(settings)]),
        _group("tools", "Tools", _mcp_checks(mcp_manager)),
    ]
    return {
        "overall": _overall(groups),
        "checked_at": _utc_timestamp(),
        "groups": groups,
    }


def _format_support_bundle(bundle: Dict[str, Any]) -> str:
    diagnostics = bundle.get("diagnostics") or {}
    runtime = bundle.get("runtime") or {}
    lines = [
        "Odysseus diagnostics support bundle",
        f"Generated: {bundle.get('generated_at', '')}",
        f"Overall: {diagnostics.get('overall', 'unknown')}",
        "",
        "Runtime:",
        f"- Platform: {runtime.get('platform', 'unknown')}",
        f"- Python: {runtime.get('python', 'unknown')}",
        f"- Docker: {runtime.get('in_docker', False)}",
        f"- Git revision: {runtime.get('git_revision') or 'unknown'}",
        "",
        "Checks:",
    ]
    for group in diagnostics.get("groups") or []:
        lines.append(f"[{group.get('label') or group.get('id') or 'Group'}]")
        for check in group.get("checks") or []:
            status = str(check.get("status") or "unknown").upper()
            label = check.get("label") or check.get("id") or "Check"
            message = check.get("message") or ""
            lines.append(f"- {status} {label}: {message}")
            if check.get("hint"):
                lines.append(f"  Hint: {check['hint']}")
            if check.get("detail"):
                lines.append(f"  Detail: {check['detail']}")
    lines.extend([
        "",
        "Redacted JSON:",
        json.dumps(bundle, indent=2, sort_keys=True),
    ])
    return "\n".join(_redact_text(line) for line in lines)


async def collect_diagnostics_support_bundle(mcp_manager: Any = None) -> Dict[str, Any]:
    settings = load_settings()
    features = load_features()
    diagnostics = await collect_system_diagnostics(mcp_manager)
    bundle = _redact_obj({
        "kind": "odysseus_diagnostics_support_bundle",
        "generated_at": _utc_timestamp(),
        "runtime": _runtime_snapshot(settings, features),
        "diagnostics": diagnostics,
    })
    return {
        "bundle": bundle,
        "text": _format_support_bundle(bundle),
    }
