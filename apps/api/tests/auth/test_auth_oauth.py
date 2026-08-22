"""OAuth authentication integration tests (GRX-AUTH-006).

Exercises multi-provider OAuth authorize & callback endpoints with real/fake Redis state
and mocked Google OAuth exchange.
"""

import json
import uuid
from collections.abc import Awaitable, Callable
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.auth.oauth.base import OAuthUserProfile
from growixa_api.auth.oauth.google import GoogleOAuthProvider
from growixa_api.auth.oauth.registry import _PROVIDERS
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.redis import get_redis
from growixa_api.users.models import OAuthIdentity, User


class _InMemoryRedis:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def get(self, name: str) -> str | None:
        return self._data.get(name)

    async def set(self, name: str, value: str, ex: int | None = None) -> bool:
        self._data[name] = value
        return True

    async def delete(self, *names: str) -> int:
        count = 0
        for name in names:
            if name in self._data:
                del self._data[name]
                count += 1
        return count


class _MockGoogleOAuthProvider(GoogleOAuthProvider):
    def __init__(self, profile: OAuthUserProfile) -> None:
        super().__init__(client_id="mock-client-id", client_secret="mock-client-secret")
        self._mock_profile = profile

    async def exchange_code_and_get_profile(self, code: str, redirect_uri: str) -> OAuthUserProfile:
        return self._mock_profile


async def _cleanup_test_data() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AuditLog))
        await session.execute(delete(OAuthIdentity))
        await session.commit()


@pytest.fixture(autouse=True)
async def cleanup_after_test():
    yield
    await _cleanup_test_data()


@pytest.mark.asyncio
async def test_oauth_authorize_unsupported_provider_raises_400() -> None:
    fake_redis = _InMemoryRedis()
    app = create_app()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        response = await client.get("/auth/oauth/unknown-provider")

    assert response.status_code == 400
    assert "Unsupported OAuth provider" in response.json()["detail"]


@pytest.mark.asyncio
async def test_oauth_authorize_google_redirects_with_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "google_client_id", "test-google-client-id")
    fake_redis = _InMemoryRedis()
    app = create_app()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        response = await client.get("/auth/oauth/google?redirect_target=/dashboard/settings")

    assert response.status_code == 307
    location = response.headers["location"]
    parsed = urlparse(location)
    assert parsed.netloc == "accounts.google.com"
    qs = parse_qs(parsed.query)
    assert qs["client_id"] == ["test-google-client-id"]
    assert "state" in qs

    state = qs["state"][0]
    stored_state_raw = await fake_redis.get(f"grx:auth:oauth_state:{state}")
    assert stored_state_raw is not None
    stored = json.loads(stored_state_raw)
    assert stored["provider"] == "google"
    assert stored["redirect_target"] == "/dashboard/settings"


@pytest.mark.asyncio
async def test_oauth_callback_missing_code_redirects_with_error() -> None:
    fake_redis = _InMemoryRedis()
    app = create_app()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        response = await client.get("/auth/oauth/google/callback")

    assert response.status_code == 307
    assert "/login?oauth_error=" in response.headers["location"]


@pytest.mark.asyncio
async def test_oauth_callback_invalid_state_redirects_with_error() -> None:
    fake_redis = _InMemoryRedis()
    app = create_app()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        response = await client.get(
            "/auth/oauth/google/callback?code=fake_code&state=nonexistent_state"
        )

    assert response.status_code == 307
    assert "oauth_error=OAuthStateInvalidError" in response.headers["location"]


@pytest.mark.asyncio
async def test_oauth_callback_provisions_new_user_and_sets_cookies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    random_id = str(uuid.uuid4())[:8]
    test_email = f"google-user-{random_id}@example.com"
    mock_profile = OAuthUserProfile(
        provider="google",
        provider_user_id=f"google-sub-{random_id}",
        email=test_email,
        full_name="Google New User",
        avatar_url="https://lh3.googleusercontent.com/photo.jpg",
        is_email_verified=True,
    )
    mock_provider = _MockGoogleOAuthProvider(mock_profile)
    monkeypatch.setitem(_PROVIDERS, "google", mock_provider)

    fake_redis = _InMemoryRedis()
    state = f"valid-state-{random_id}"
    await fake_redis.set(
        f"grx:auth:oauth_state:{state}",
        json.dumps({"provider": "google", "redirect_target": "/dashboard/welcome"}),
    )

    app = create_app()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        response = await client.get(f"/auth/oauth/google/callback?code=mock_code&state={state}")

    assert response.status_code == 307
    assert response.headers["location"].endswith("/dashboard/welcome")
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    # Verify user and account created in database
    async with async_session_factory() as session:
        user_res = await session.execute(select(User).where(User.email == test_email))
        user = user_res.scalar_one_or_none()
        assert user is not None
        assert user.status == "ACTIVE"
        assert user.full_name == "Google New User"
        assert user.password_hash is None

        ident_res = await session.execute(
            select(OAuthIdentity).where(OAuthIdentity.provider_user_id == f"google-sub-{random_id}")
        )
        ident = ident_res.scalar_one_or_none()
        assert ident is not None
        assert ident.user_id == user.id
        assert ident.provider == "google"


@pytest.mark.asyncio
async def test_oauth_callback_links_existing_user_by_email(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account_id = await account_factory()
    user_id = await user_factory(
        full_name="Existing Email User",
        role_name="Admin",
        account_id=account_id,
    )

    async with async_session_factory() as session:
        user = await session.get(User, user_id)
        assert user is not None
        existing_email = user.email

    mock_profile = OAuthUserProfile(
        provider="google",
        provider_user_id="google-sub-existing-link",
        email=existing_email,
        full_name="Existing Email User",
        is_email_verified=True,
    )
    mock_provider = _MockGoogleOAuthProvider(mock_profile)
    monkeypatch.setitem(_PROVIDERS, "google", mock_provider)

    fake_redis = _InMemoryRedis()
    state = "state-link-existing"
    await fake_redis.set(
        f"grx:auth:oauth_state:{state}",
        json.dumps({"provider": "google", "redirect_target": None}),
    )

    app = create_app()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        response = await client.get(f"/auth/oauth/google/callback?code=mock_code&state={state}")

    assert response.status_code == 307
    assert response.headers["location"].endswith("/dashboard")
    assert "access_token" in response.cookies

    # Verify identity linked
    async with async_session_factory() as session:
        ident_res = await session.execute(
            select(OAuthIdentity).where(
                OAuthIdentity.provider_user_id == "google-sub-existing-link"
            )
        )
        ident = ident_res.scalar_one_or_none()
        assert ident is not None
        assert ident.user_id == user_id
        assert ident.account_id == account_id
