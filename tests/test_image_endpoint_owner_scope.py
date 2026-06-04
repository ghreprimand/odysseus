"""Owner-scope regression for the image edit/inpaint/harmonize proxies.

POST /api/image/inpaint and /api/image/harmonize (require_privilege
"can_generate_images" — a normal user, not admin) resolve a ModelEndpoint two
ways and send its *decrypted* api_key upstream as `Authorization: Bearer …`:

  1. caller-supplied `_endpoint` -> matched by normalized base_url
  2. nothing supplied            -> first enabled image endpoint

Both must be owner-scoped (caller's own rows + legacy null-owner shared rows) so
an image-privileged user can't pass another user's endpoint URL — or fall through
to their first image endpoint — and spend that owner's API key / quota. Mirrors
the session / research / compare / resolve_session_auth owner-scope fixes.

Test isolation: we drive the real `_owned_image_endpoint` against a tiny fake
query, swapping in a fake ModelEndpoint via monkeypatch for each test. Do not
mutate core.database at import time; those globals are shared by later tests
that build real SQLAlchemy tables.
"""

from types import SimpleNamespace

import pytest

import routes.gallery_routes as gallery_routes
from routes.gallery_routes import _owned_image_endpoint


class _Predicate:
    def __init__(self, check):
        self._check = check

    def __call__(self, row):
        return self._check(row)

    def __or__(self, other):
        return _Predicate(lambda row: self(row) or other(row))


class _Column:
    def __init__(self, name):
        self.name = name

    def __eq__(self, value):
        return _Predicate(lambda row: getattr(row, self.name) == value)


class _ModelEndpoint:
    base_url = _Column("base_url")
    owner = _Column("owner")
    is_enabled = _Column("is_enabled")
    model_type = _Column("model_type")


class _Query:
    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, *predicates):
        self._rows = [r for r in self._rows if all(p(r) for p in predicates)]
        return self

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None


class _DB:
    def __init__(self, rows):
        self._rows = rows

    def query(self, model):
        assert model is _ModelEndpoint
        return _Query(self._rows)


def _ep(base_url, owner, *, is_enabled=True, model_type="image"):
    return SimpleNamespace(base_url=base_url, owner=owner, is_enabled=is_enabled,
                           model_type=model_type, api_key="sk-secret")


@pytest.fixture
def resolve(monkeypatch):
    monkeypatch.setattr(gallery_routes, "ModelEndpoint", _ModelEndpoint)

    def _resolve(rows, owner, target_url=None):
        return _owned_image_endpoint(_DB(rows), owner, target_url)

    return _resolve


URL = "https://images.example.com/v1"


# --- caller-supplied _endpoint (URL match) -----------------------------------

def test_url_match_rejects_another_owners_private_endpoint(resolve):
    rows = [_ep(URL, "bob")]
    assert resolve(rows, "alice", URL) is None


def test_url_match_returns_callers_own_endpoint(resolve):
    rows = [_ep(URL, "bob"), _ep(URL, "alice")]
    ep = resolve(rows, "alice", URL)
    assert ep is not None and ep.owner == "alice"


def test_url_match_allows_legacy_null_owner_shared_row(resolve):
    rows = [_ep(URL, None)]
    ep = resolve(rows, "alice", URL)
    assert ep is not None and ep.owner is None


def test_url_match_normalizes_v1_suffix(resolve):
    # caller passes the URL without /v1; the owned row stores it with /v1.
    rows = [_ep("https://images.example.com/v1", "alice")]
    ep = resolve(rows, "alice", "https://images.example.com")
    assert ep is not None and ep.owner == "alice"


def test_url_match_rejects_disabled_endpoint(resolve):
    # The caller owns a row whose URL matches, but it's disabled — its api_key
    # must not be borrowed (same constraint as the fallback path).
    rows = [_ep(URL, "alice", is_enabled=False)]
    assert resolve(rows, "alice", URL) is None


def test_url_match_rejects_non_image_endpoint(resolve):
    # Owned + URL matches, but it's an llm endpoint, not image.
    rows = [_ep(URL, "alice", model_type="llm")]
    assert resolve(rows, "alice", URL) is None


# --- first-enabled fallback (no _endpoint) -----------------------------------

def test_fallback_never_picks_another_owners_endpoint(resolve):
    rows = [_ep(URL, "bob"), _ep("https://shared.example/v1", None)]
    ep = resolve(rows, "alice")
    assert ep is not None and ep.owner is None


def test_fallback_returns_none_when_only_others(resolve):
    rows = [_ep(URL, "bob"), _ep("https://c.example/v1", "carol")]
    assert resolve(rows, "alice") is None


def test_fallback_skips_non_image_and_disabled(resolve):
    rows = [
        _ep(URL, "alice", model_type="llm"),
        _ep("https://d.example/v1", "alice", is_enabled=False),
        _ep("https://img.example/v1", "alice"),
    ]
    ep = resolve(rows, "alice")
    assert ep is not None and ep.base_url == "https://img.example/v1"


def test_null_owner_is_legacy_single_user_noop(resolve):
    rows = [_ep(URL, "bob")]
    assert resolve(rows, None, URL).owner == "bob"
