"""Instagram OAuth connect-flow integration tests (GRX-SOCIAL-003).

Integration-tier: exercises real Postgres and the real create_app() app. The Graph API
itself is monkeypatched (instagram_client) — no live Meta Developer App available in this
environment, same documented-evidence-gap convention as test_send_campaign.py's
monkeypatched SMTP transport. The Redis-backed `state` CSRF check needs a real reachable
Redis (Compose's `redis` service has no host port mapping, per test_redis.py's own note)
— these tests skip, not fail, when Redis isn't reachable from the test runner; they run
for real inside the api container (`docker compose exec api pytest`).
"""

import uuid
from collections.abc import Awaitable, Callable
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from redis.exceptions import RedisError
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.redis import client as redis_client
from growixa_api.social import instagram_client
from growixa_api.social.instagram_client import (
    NoLinkedInstagramAccountError,
    ResolvedInstagramAccount,
)
from growixa_api.social.models import SocialConnection


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _require_redis() -> None:
    try:
        await redis_client.ping()
    except RedisError as exc:
        pytest.skip(f"Redis not reachable from the test runner: {exc}")


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(SocialConnection))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_authorize_route_redirects_to_meta_with_a_state_param(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    await _require_redis()
    account_id = await account_factory()
    admin_id = await user_factory(
        full_name="Test Super Admin", role_name="Super Admin", account_id=account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(admin_id),
            follow_redirects=False,
        ) as client:
            response = await client.get("/integrations/instagram/oauth/authorize")

        assert response.status_code == 302
        location = response.headers["location"]
        assert location.startswith("https://www.facebook.com/")
        # keep_blank_values=True: instagram_app_id is unset (empty) in this test
        # environment, and parse_qs silently drops blank-valued keys by default.
        query = parse_qs(urlparse(location).query, keep_blank_values=True)
        assert "state" in query
        assert query["client_id"] == [get_settings().instagram_app_id]
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_callback_with_denied_consent_redirects_with_an_error(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    admin_id = await user_factory(
        full_name="Test Super Admin", role_name="Super Admin", account_id=account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(admin_id),
            follow_redirects=False,
        ) as client:
            response = await client.get(
                "/integrations/instagram/oauth/callback", params={"error": "access_denied"}
            )

        assert response.status_code == 302
        location = response.headers["location"]
        assert "instagram=error" in location
        assert "reason=denied" in location
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_callback_with_an_unknown_state_redirects_with_invalid_state(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    await _require_redis()
    account_id = await account_factory()
    admin_id = await user_factory(
        full_name="Test Super Admin", role_name="Super Admin", account_id=account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(admin_id),
            follow_redirects=False,
        ) as client:
            response = await client.get(
                "/integrations/instagram/oauth/callback",
                params={"code": "fake-code", "state": "bogus-never-issued"},
            )

        assert response.status_code == 302
        location = response.headers["location"]
        assert "instagram=error" in location
        assert "reason=invalid_state" in location
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_connect_flow_persists_a_connection(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    await _require_redis()

    async def _fake_exchange_code(**kwargs: object) -> str:
        return "fake-short-lived-token"

    async def _fake_exchange_long_lived(**kwargs: object) -> tuple[str, int]:
        return "fake-long-lived-token", 5184000

    async def _fake_resolve(**kwargs: object) -> ResolvedInstagramAccount:
        return ResolvedInstagramAccount(
            facebook_page_id="page-123",
            ig_business_account_id="ig-123",
            ig_username="growixa_test",
            page_access_token="fake-page-token",
        )

    monkeypatch.setattr(instagram_client, "exchange_code_for_token", _fake_exchange_code)
    monkeypatch.setattr(
        instagram_client, "exchange_for_long_lived_token", _fake_exchange_long_lived
    )
    monkeypatch.setattr(instagram_client, "resolve_instagram_business_account", _fake_resolve)

    account_id = await account_factory()
    admin_id = await user_factory(
        full_name="Test Super Admin", role_name="Super Admin", account_id=account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(admin_id),
            follow_redirects=False,
        ) as client:
            authorize_response = await client.get("/integrations/instagram/oauth/authorize")
            location = authorize_response.headers["location"]
            state = parse_qs(urlparse(location).query)["state"][0]

            callback_response = await client.get(
                "/integrations/instagram/oauth/callback",
                params={"code": "fake-code", "state": state},
            )

        assert callback_response.status_code == 302
        assert "instagram=connected" in callback_response.headers["location"]

        async with async_session_factory() as session:
            result = await session.execute(
                select(SocialConnection).where(SocialConnection.account_id == account_id)
            )
            connection = result.scalar_one()
            assert connection.ig_business_account_id == "ig-123"
            assert connection.is_active is True

        # The state is single-use -- replaying it must fail, not silently succeed again.
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(admin_id),
            follow_redirects=False,
        ) as client:
            replay_response = await client.get(
                "/integrations/instagram/oauth/callback",
                params={"code": "fake-code", "state": state},
            )
        assert "reason=invalid_state" in replay_response.headers["location"]
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_no_linked_instagram_account_redirects_with_graph_api_error(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    await _require_redis()

    async def _fake_exchange_code(**kwargs: object) -> str:
        return "fake-short-lived-token"

    async def _fake_exchange_long_lived(**kwargs: object) -> tuple[str, int]:
        return "fake-long-lived-token", 5184000

    async def _fake_resolve_no_account(**kwargs: object) -> ResolvedInstagramAccount:
        raise NoLinkedInstagramAccountError("no linked IG account")

    monkeypatch.setattr(instagram_client, "exchange_code_for_token", _fake_exchange_code)
    monkeypatch.setattr(
        instagram_client, "exchange_for_long_lived_token", _fake_exchange_long_lived
    )
    monkeypatch.setattr(
        instagram_client, "resolve_instagram_business_account", _fake_resolve_no_account
    )

    account_id = await account_factory()
    admin_id = await user_factory(
        full_name="Test Super Admin", role_name="Super Admin", account_id=account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(admin_id),
            follow_redirects=False,
        ) as client:
            authorize_response = await client.get("/integrations/instagram/oauth/authorize")
            location = authorize_response.headers["location"]
            state = parse_qs(urlparse(location).query)["state"][0]

            callback_response = await client.get(
                "/integrations/instagram/oauth/callback",
                params={"code": "fake-code", "state": state},
            )

        assert "instagram=error" in callback_response.headers["location"]
        assert "reason=graph_api_error" in callback_response.headers["location"]
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_only_integrations_manage_can_connect(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    # Admin (not Super Admin) — integrations.manage is Super-Admin-only per RBAC.md.
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin", account_id=account_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.get(
                "/integrations/instagram/oauth/authorize", follow_redirects=False
            )
        assert response.status_code == 403
    finally:
        await _cleanup()
