"""Unit tests for the platform-level transactional verification email (registration
follow-up). Mocks growixa_api.integrations.smtp_transport.send_email -- these tests
verify the no-op-when-unconfigured guard and the argument-building, not real SMTP
delivery (already covered by smtp_transport's own tests/live "test connection" use)."""

from unittest.mock import AsyncMock, patch

import pytest

from growixa_api.config import Settings
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.notifications.email import send_verification_email


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "database_url": "postgresql+asyncpg://x:x@localhost/x",
        "redis_url": "redis://localhost",
        "rabbitmq_url": "amqp://localhost",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_noops_when_smtp_host_not_configured() -> None:
    with (
        patch(
            "growixa_api.notifications.email.get_settings",
            return_value=_settings(platform_smtp_host=""),
        ),
        patch("growixa_api.notifications.email.send_email", new=AsyncMock()) as mock_send,
    ):
        await send_verification_email(
            to_email="new@example.com", full_name="New User", raw_token="raw-token"
        )

    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_sends_with_verification_link_when_configured() -> None:
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
        patch("growixa_api.notifications.email.send_email", new=AsyncMock()) as mock_send,
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
async def test_send_failure_does_not_raise() -> None:
    settings = _settings(platform_smtp_host="smtp.example.com")
    with (
        patch("growixa_api.notifications.email.get_settings", return_value=settings),
        patch(
            "growixa_api.notifications.email.send_email",
            new=AsyncMock(side_effect=EmailSendError("connection refused")),
        ),
    ):
        # Must not raise -- registration itself must never fail because of this.
        await send_verification_email(
            to_email="new@example.com", full_name="New User", raw_token="raw-token"
        )
