import pytest
from pathlib import Path


class _Response:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}
        self.content = b"{}"

    @property
    def is_success(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._data


class _Endpoint:
    def __init__(self, base_url, name="Local", enabled=True, endpoint_id="ep1"):
        self.id = endpoint_id
        self.name = name
        self.base_url = base_url
        self.is_enabled = enabled


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return list(self.rows)


class _Db:
    def __init__(self, rows_by_model=None):
        self.rows_by_model = rows_by_model or {}
        self.closed = False

    def execute(self, *_args, **_kwargs):
        return None

    def query(self, model):
        return _Query(self.rows_by_model.get(model, []))

    def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_ollama_check_reports_model_count(monkeypatch):
    import src.system_diagnostics as diag

    async def fake_probe(url, timeout=diag.CHECK_TIMEOUT):
        assert url == "http://127.0.0.1:11434/api/tags"
        return _Response(data={"models": [{"name": "qwen"}, {"name": "gemma"}]})

    monkeypatch.setattr(diag, "_probe_http", fake_probe)
    monkeypatch.setattr(diag, "_ollama_base_url", lambda: "http://127.0.0.1:11434/v1")

    check = await diag._ollama_check()

    assert check["status"] == "ok"
    assert "2 local models" in check["message"]


@pytest.mark.asyncio
async def test_model_endpoint_checks_warn_when_none_enabled(monkeypatch):
    import src.system_diagnostics as diag

    monkeypatch.setattr(diag, "SessionLocal", lambda: _Db({
        diag.ModelEndpoint: [_Endpoint("http://127.0.0.1:11434/v1", enabled=False)]
    }))

    checks = await diag._model_endpoint_checks()

    assert checks[0]["status"] == "warning"
    assert checks[0]["action"]["tab"] == "services"


@pytest.mark.asyncio
async def test_model_endpoint_checks_probe_local_endpoints_only(monkeypatch):
    import src.system_diagnostics as diag

    calls = []

    async def fake_probe(url, timeout=diag.CHECK_TIMEOUT):
        calls.append(url)
        return _Response(status_code=503)

    monkeypatch.setattr(diag, "_probe_http", fake_probe)
    monkeypatch.setattr(diag, "SessionLocal", lambda: _Db({
        diag.ModelEndpoint: [
            _Endpoint("http://127.0.0.1:11434/v1", name="Ollama", endpoint_id="local"),
            _Endpoint("https://api.openai.com/v1", name="OpenAI", endpoint_id="remote"),
        ]
    }))

    checks = await diag._model_endpoint_checks()

    assert calls == ["http://127.0.0.1:11434/v1/models"]
    assert checks[0]["status"] == "ok"
    assert checks[1]["status"] == "warning"
    assert "Ollama" in checks[1]["label"]


def test_diagnostics_overall_rollup():
    import src.system_diagnostics as diag

    assert diag._overall([{"checks": [{"status": "ok"}, {"status": "skipped"}]}]) == "healthy"
    assert diag._overall([{"checks": [{"status": "warning"}]}]) == "degraded"
    assert diag._overall([{"checks": [{"status": "error"}]}]) == "error"


def test_mcp_checks_include_live_browser_status(monkeypatch):
    import src.system_diagnostics as diag

    class _McpManager:
        def get_all_statuses(self):
            return {"builtin_browser": {"status": "connected", "tool_count": 29}}

    monkeypatch.setattr(diag, "SessionLocal", lambda: _Db({diag.McpServer: []}))

    checks = diag._mcp_checks(_McpManager())

    assert checks[0]["id"] == "browser_mcp"
    assert checks[0]["status"] == "ok"
    assert "29 tools" in checks[0]["message"]


def test_support_bundle_redacts_secret_keys_and_tokens():
    import src.system_diagnostics as diag

    secret = "sk-" + ("a" * 28)
    payload = {
        "api_key": secret,
        "message": f"{Path.home()}/Projects/odysseus failed with token=super-secret-token",
        "nested": {"authorization": "Bearer " + ("b" * 24)},
    }

    redacted = diag._redact_obj(payload)

    assert redacted["api_key"] == "<redacted>"
    assert str(Path.home()) not in redacted["message"]
    assert "super-secret-token" not in redacted["message"]
    assert redacted["nested"]["authorization"] == "<redacted>"


@pytest.mark.asyncio
async def test_support_bundle_text_includes_redacted_diagnostics(monkeypatch):
    import src.system_diagnostics as diag

    secret = "sk-" + ("c" * 28)

    async def fake_collect(_mcp_manager=None):
        return {
            "overall": "error",
            "checked_at": "2026-06-02T00:00:00Z",
            "groups": [{
                "id": "core",
                "label": "Core",
                "checks": [diag._check(
                    "database",
                    "Database",
                    "error",
                    "Database failed.",
                    detail=f"{Path.home()}/data/app.db {secret}",
                )],
            }],
        }

    monkeypatch.setattr(diag, "collect_system_diagnostics", fake_collect)
    monkeypatch.setattr(diag, "load_settings", lambda: {"search_provider": "searxng", "search_url": "https://example.test?q=1"})
    monkeypatch.setattr(diag, "load_features", lambda: {"rag": True, "web_search": True})
    monkeypatch.setattr(diag, "_git_revision", lambda: "abc123")

    result = await diag.collect_diagnostics_support_bundle()

    assert result["bundle"]["kind"] == "odysseus_diagnostics_support_bundle"
    assert "Database failed." in result["text"]
    assert secret not in result["text"]
    assert str(Path.home()) not in result["text"]
    assert "<redacted>" in result["text"]
