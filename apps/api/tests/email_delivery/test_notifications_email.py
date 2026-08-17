"""Unit tests for the platform-level transactional verification email (registration
follow-up). Integration-tier: send_verification_email opens its own DB session
internally (it runs as a FastAPI BackgroundTask, with no request session to reuse) to
check for an active platform_email_provider_config row before falling back to the
legacy .env-only PLATFORM_SMTP_* settings -- real Postgres is needed to exercise that
resolution order, even though no real SMTP send happens here (mocked at the
smtp_transport boundary, same convention as every other external-provider test in this
suite)."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import delete

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.config import Settings
from growixa_api.db import async_session_factory
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.notifications.email import send_password_reset_email, send_verification_email
from growixa_api.notifications.models import PlatformEmailProviderConfig


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "database_url": "postgresql+asyncpg://x:x@localhost/x",
        "redis_url": "redis://localhost",
        "rabbitmq_url": "amqp://localhost",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_noops_when_neither_db_config_nor_env_smtp_host_is_configured() -> None:
    with (
        patch(
            "growixa_api.notifications.email.get_settings",
            return_value=_settings(platform_smtp_host=""),
        ),
        patch("growixa_api.notifications.email.smtp_send_email", new=AsyncMock()) as mock_send,
    ):
        await send_verification_email(
            to_email="new@example.com", full_name="New User", raw_token="raw-token"
        )

    mock_send.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_password_reset_email_noops_when_no_provider_is_configured() -> None:
    with (
        patch(
            "growixa_api.notifications.email.get_settings",
            return_value=_settings(platform_smtp_host=""),
        ),
        patch("growixa_api.notifications.email.smtp_send_email", new=AsyncMock()) as mock_send,
    ):
        await send_password_reset_email(to_email="reset@example.com", raw_token="raw-reset-token")

    mock_send.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sends_via_env_smtp_fallback_when_no_db_config_exists() -> None:
    """No platform_email_provider_config row exists (clean DB state) -- falls back to
    the legacy .env-only PLATFORM_SMTP_* settings."""
    settings = _settings(
        platform_smtp_host="smtp.example.com",
        platform_smtp_port=587,
        platform_smtp_username="user",
        platform_smtp_password="pw",
        platform_smtp_from_email="noreply@growixa.local",
        platform_smtp_from_name="Growixa",
        frontend_base_url="https://growixa.netlify.app",
    )
    with (
        patch("growixa_api.notifications.email.get_settings", return_value=settings),
        patch("growixa_api.notifications.email.smtp_send_email", new=AsyncMock()) as mock_send,
    ):
        await send_verification_email(
            to_email="new@example.com", full_name="New User", raw_token="raw-token"
        )

    mock_send.assert_awaited_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["to_email"] == "new@example.com"
    assert kwargs["smtp_host"] == "smtp.example.com"
    assert "https://growixa.netlify.app/verify-email?token=raw-token" in kwargs["body_html"]
    assert "https://growixa.netlify.app/verify-email?token=raw-token" in kwargs["body_text"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_password_reset_email_uses_env_smtp_fallback_and_30_minute_copy() -> None:
    settings = _settings(
        platform_smtp_host="smtp.example.com",
        platform_smtp_port=587,
        platform_smtp_username="user",
        platform_smtp_password="pw",
        platform_smtp_from_email="noreply@growixa.local",
        platform_smtp_from_name="Growixa",
        frontend_base_url="https://growixa.netlify.app",
        password_reset_ttl_minutes=30,
    )
    with (
        patch("growixa_api.notifications.email.get_settings", return_value=settings),
        patch("growixa_api.notifications.email.smtp_send_email", new=AsyncMock()) as mock_send,
    ):
        await send_password_reset_email(to_email="reset@example.com", raw_token="raw-reset-token")

    mock_send.assert_awaited_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["to_email"] == "reset@example.com"
    assert kwargs["subject"] == "Reset your Growixa password"
    assert "https://growixa.netlify.app/reset-password?token=raw-reset-token" in kwargs["body_html"]
    assert "https://growixa.netlify.app/reset-password?token=raw-reset-token" in kwargs["body_text"]
    assert "expires in 30 minutes" in kwargs["body_html"]
    assert "can be used once" in kwargs["body_text"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_db_config_takes_priority_over_env_smtp_fallback() -> None:
    """An active platform_email_provider_config row is used instead of the legacy
    .env-only settings, even when both are present -- the DB config is meant to
    supersede it once a platform admin has configured one."""
    settings = _settings(
        platform_smtp_host="env-fallback.example.com",
        frontend_base_url="https://growixa.netlify.app",
    )
    async with async_session_factory() as session:
        session.add(
            PlatformEmailProviderConfig(
                provider="POSTMARK",
                smtp_host="smtp.postmarkapp.com",
                smtp_port=587,
                smtp_username="server-token",
                smtp_password_encrypted=encrypt_secret("server-token"),
                from_email="noreply@growixa.local",
                from_name="Growixa",
            )
        )
        await session.commit()

    try:
        with (
            patch("growixa_api.notifications.email.get_settings", return_value=settings),
            patch(
                "growixa_api.notifications.services.smtp_send_email", new=AsyncMock()
            ) as mock_send,
        ):
            await send_verification_email(
                to_email="new@example.com", full_name="New User", raw_token="raw-token"
            )

        mock_send.assert_awaited_once()
        kwargs = mock_send.call_args.kwargs
        assert kwargs["smtp_host"] == "smtp.postmarkapp.com"
        assert kwargs["smtp_password"] == "server-token"
    finally:
        async with async_session_factory() as session:
            await session.execute(delete(PlatformEmailProviderConfig))
            await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_password_reset_email_db_config_takes_priority_over_env_smtp_fallback() -> None:
    settings = _settings(
        platform_smtp_host="env-fallback.example.com",
        frontend_base_url="https://growixa.netlify.app",
    )
    async with async_session_factory() as session:
        session.add(
            PlatformEmailProviderConfig(
                provider="POSTMARK",
                smtp_host="smtp.postmarkapp.com",
                smtp_port=587,
                smtp_username="server-token",
                smtp_password_encrypted=encrypt_secret("server-token"),
                from_email="noreply@growixa.local",
                from_name="Growixa",
            )
        )
        await session.commit()

    try:
        with (
            patch("growixa_api.notifications.email.get_settings", return_value=settings),
            patch(
                "growixa_api.notifications.services.smtp_send_email", new=AsyncMock()
            ) as mock_send,
        ):
            await send_password_reset_email(
                to_email="reset@example.com", raw_token="raw-reset-token"
            )

        mock_send.assert_awaited_once()
        kwargs = mock_send.call_args.kwargs
        assert kwargs["smtp_host"] == "smtp.postmarkapp.com"
        assert kwargs["smtp_password"] == "server-token"
    finally:
        async with async_session_factory() as session:
            await session.execute(delete(PlatformEmailProviderConfig))
            await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_failure_does_not_raise() -> None:
    settings = _settings(platform_smtp_host="smtp.example.com")
    with (
        patch("growixa_api.notifications.email.get_settings", return_value=settings),
        patch(
            "growixa_api.notifications.email.smtp_send_email",
            new=AsyncMock(side_effect=EmailSendError("connection refused")),
        ),
    ):
        # Must not raise -- registration itself must never fail because of this.
        await send_verification_email(
            to_email="new@example.com", full_name="New User", raw_token="raw-token"
        )
