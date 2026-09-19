"""App-level import-graph smoke test.

Regression guard for a real production bug: `growixa_api.accounts.models` (the `Account`
ORM class every `account_id` foreign key points to) was never imported anywhere in
`app.py`'s import graph -- only `migrations/env.py` imported it, for Alembic autogenerate.
SQLAlchemy never registered the `accounts` table in `Base.metadata`, so every
`ForeignKey("accounts.id")` reference failed to resolve the moment SQLAlchemy needed to
order tables for an INSERT (e.g. on the first `/auth/login`, inserting a `RefreshToken`)
-- while `/health` kept returning 200, since it doesn't touch the ORM. `configure_mappers()`
alone does *not* catch this: FK-target resolution for plain Core `ForeignKey` columns (not
`relationship()`) is deferred until a flush actually needs table sort order, so this
checks the real, direct signal instead -- whether the `accounts` table ever made it into
`Base.metadata.tables` at all.

Must run in a fresh subprocess: importing `tests/conftest.py` (as every other test in this
suite implicitly does) already imports `growixa_api.accounts.models` directly for its own
fixtures, which would mask this exact bug if this test shared that process.
"""

import os
import subprocess
import sys

import pytest
from httpx import ASGITransport, AsyncClient

from growixa_api.app import create_app


def test_create_app_registers_the_accounts_table_every_account_id_fk_points_to() -> None:
    src_dir = os.path.abspath("src")
    if not os.path.isdir(src_dir):
        src_dir = os.path.abspath("apps/api/src")
    env = {**os.environ, "PYTHONPATH": src_dir}

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from growixa_api.app import create_app\n"
            "from growixa_api.db import Base\n"
            "create_app()\n"
            "assert 'accounts' in Base.metadata.tables, "
            "'accounts table never registered -- growixa_api.accounts.models was never "
            "imported anywhere in the app import graph'\n",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "origin,allowed", [("http://localhost:3000", True), ("https://untrusted.example", False)]
)
async def test_cors_only_allows_configured_origins(origin: str, allowed: bool) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.options(
            "/auth/login",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )
    assert response.status_code == (200 if allowed else 400)
    assert response.headers.get("access-control-allow-origin") == (origin if allowed else None)


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/seo/analyze", {"url": "http://127.0.0.1/internal"}),
        ("/ai/chat", {"message": "pricing"}),
    ],
)
async def test_unavailable_public_features_never_report_success(
    path: str,
    payload: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def forbidden_request(*args: object, **kwargs: object) -> None:
        raise AssertionError("Pending features must not make outbound requests")

    # Patching the transport used by httpx leaves the in-process ASGI client intact.
    import httpx

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden_request)
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.post(path, json=payload)
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "FEATURE_PENDING"
