"""Shared pairing helpers for the companion bridge.

Token minting + LAN discovery + QR rendering, kept here as small, importable
units so the route layer stays thin and the logic is directly testable.
"""

from __future__ import annotations

import json
import os
import secrets
import socket
import uuid
from urllib.parse import urlparse

import bcrypt

PAIRING_VERSION = 1
COMPANION_SCOPE = "chat"


def default_port() -> int:
    """Best guess at the port the server is reachable on. Callers that know the
    real request port should pass it explicitly."""
    try:
        return int(os.environ.get("APP_PORT", "7000"))
    except ValueError:
        return 7000


def configured_bind_host() -> str:
    """Return the configured app bind host, using the same env knobs documented
    for Docker/native launches. The default is loopback: safe, but not reachable
    by a phone until the operator opts into LAN/Tailscale exposure."""
    return (
        os.environ.get("APP_BIND")
        or os.environ.get("ODYSSEUS_HOST")
        or "127.0.0.1"
    ).strip() or "127.0.0.1"


def is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    return host.lower().strip("[]") in {"localhost", "127.0.0.1", "::1"}


def _is_tailscale_ip(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4 or parts[0] != "100":
        return False
    try:
        second = int(parts[1])
    except ValueError:
        return False
    return 64 <= second <= 127


def access_kind(host: str) -> str:
    """Classify a host for UI labels. Keep this intentionally simple: the
    Companion UI is advisory, not a network security decision point."""
    if is_loopback_host(host):
        return "loopback"
    if _is_tailscale_ip(host):
        return "tailscale"
    return "lan"


def _netloc(host: str, port: int, scheme: str) -> str:
    default = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    display_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
    return display_host if default else f"{display_host}:{port}"


def access_url(host: str, port: int, scheme: str = "http") -> str:
    return f"{scheme}://{_netloc(host, port, scheme)}"


def lan_ip_candidates() -> list[str]:
    """Likely LAN IPv4 addresses for this host, best candidate first.

    The UDP-connect trick reveals the egress interface the OS would use to reach
    the default gateway -- i.e. the address a phone on the same Wi-Fi should
    target. No packets are actually sent. Loopback is dropped.
    """
    candidates: list[str] = []

    def _add(ip):
        if ip and ip not in candidates and not ip.startswith("127."):
            candidates.append(ip)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        _add(s.getsockname()[0])
    except OSError:
        pass
    finally:
        s.close()

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            _add(info[4][0])
    except OSError:
        pass

    return candidates


def access_candidates(request_url: str | None = None) -> dict:
    """Build display-only URLs for reaching this server from another device.

    This does not mint credentials and does not probe the network. It reports
    the URLs Odysseus can infer locally, plus a conservative bind warning when
    the app appears to be loopback-only.
    """
    parsed = urlparse(request_url or "")
    scheme = parsed.scheme or "http"
    request_host = parsed.hostname or ""
    port = parsed.port or default_port()
    bind_host = configured_bind_host()

    hosts: list[str] = []
    for host in [request_host, *lan_ip_candidates()]:
        if host and host not in hosts:
            hosts.append(host)

    urls = []
    for host in hosts:
        kind = access_kind(host)
        urls.append({
            "host": host,
            "kind": kind,
            "url": access_url(host, port, scheme),
            "current": host == request_host,
            "recommended": kind in {"tailscale", "lan"} and not is_loopback_host(host),
        })

    reachable = any(u["recommended"] for u in urls)
    return {
        "bind_host": bind_host,
        "loopback_only": is_loopback_host(bind_host),
        "current_url": access_url(request_host, port, scheme) if request_host else "",
        "urls": urls,
        "reachable_from_another_device": reachable and not is_loopback_host(bind_host),
    }


def find_admin_user() -> str | None:
    """Resolve an admin username from data/auth.json (schema uses is_admin),
    falling back to the first user."""
    auth_path = os.path.join("data", "auth.json")
    try:
        with open(auth_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    users = data.get("users") or {}
    if not isinstance(users, dict):
        return None
    for uname, udata in users.items():
        if isinstance(udata, dict) and udata.get("is_admin") is True:
            return uname
    return next(iter(users), None)


def mint_token(owner: str, name: str = "companion") -> tuple[str, str]:
    """Create a chat-scoped API token row and return (token_id, raw_token).

    The raw token is returned ONCE -- only its bcrypt hash + an 8-char prefix
    are persisted. Mirrors routes/api_token_routes.py so cookie- and
    companion-minted tokens are indistinguishable to the auth middleware.
    """
    from core.database import get_db_session, ApiToken

    raw_token = "ody_" + secrets.token_urlsafe(32)
    token_hash = bcrypt.hashpw(raw_token.encode(), bcrypt.gensalt()).decode()
    token_id = str(uuid.uuid4())[:8]

    with get_db_session() as db:
        db.add(ApiToken(
            id=token_id,
            owner=owner,
            name=name,
            token_hash=token_hash,
            token_prefix=raw_token[:8],
            scopes=COMPANION_SCOPE,
            is_active=True,
        ))
    return token_id, raw_token


def pairing_payload(host: str, port: int, token: str) -> dict:
    """The exact JSON a client scans / accepts. Keep keys stable."""
    return {"v": PAIRING_VERSION, "host": host, "port": port, "token": token}


def pairing_qr_png_data_uri(payload: dict) -> str | None:
    """Render the pairing payload as a QR `data:` URI for an <img>. Returns None
    if the optional qrcode dep is unavailable."""
    try:
        import base64
        import io

        import qrcode

        img = qrcode.make(json.dumps(payload, separators=(",", ":")))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None
