"""Unit tests for smtp_transport's TLS-mode selection, error wrapping, and connection
test (GRX-EMAIL-011/012). Moved from email_delivery to integrations per
MODULE_BOUNDARIES.md — email_delivery may depend on integrations, not the reverse, and
GRX-EMAIL-012's "test connection" feature belongs to integrations (connection setup).

Port 465 is implicit TLS; every other port is plaintext-then-STARTTLS. aiosmtplib itself
is mocked here — these tests only assert which mode we ask for, not real network behavior.
"""

import ssl
from unittest.mock import AsyncMock

import aiosmtplib
import pytest

from growixa_api.integrations import smtp_transport
from growixa_api.integrations.smtp_transport import EmailSendError


async def _send(monkeypatch: pytest.MonkeyPatch, *, smtp_port: int) -> AsyncMock:
    mock_send = AsyncMock()
    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    await smtp_transport.send_email(
        smtp_host="mail.example.com",
        smtp_port=smtp_port,
        smtp_username="user",
        smtp_password="pass",
        from_email="from@example.com",
        from_name="Sender",
        to_email="to@example.com",
        subject="Subject",
        body_html="<p>hi</p>",
        body_text="hi",
    )
    return mock_send


async def test_port_465_uses_implicit_tls(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_send = await _send(monkeypatch, smtp_port=465)
    assert mock_send.call_args.kwargs["use_tls"] is True
    assert mock_send.call_args.kwargs["start_tls"] is False


async def test_port_587_uses_starttls(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_send = await _send(monkeypatch, smtp_port=587)
    assert mock_send.call_args.kwargs["use_tls"] is False
    assert mock_send.call_args.kwargs["start_tls"] is True


async def test_tls_certificate_errors_are_wrapped_as_email_send_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ssl.SSLCertVerificationError (e.g. an expired server cert) is an OSError, not an
    aiosmtplib.SMTPException — without catching OSError too, this escaped as a raw 500
    instead of the intended EmailSendError -> 502 response."""

    async def _raise(*args: object, **kwargs: object) -> None:
        raise ssl.SSLCertVerificationError("certificate has expired")

    monkeypatch.setattr(aiosmtplib, "send", _raise)

    with pytest.raises(EmailSendError, match="certificate has expired"):
        await smtp_transport.send_email(
            smtp_host="mail.example.com",
            smtp_port=465,
            smtp_username="user",
            smtp_password="pass",
            from_email="from@example.com",
            from_name="Sender",
            to_email="to@example.com",
            subject="Subject",
            body_html="<p>hi</p>",
            body_text="hi",
        )


class _FakeSMTPClient:
    """Stands in for aiosmtplib.SMTP's async-context-manager + login() shape, without
    opening a real socket. `login_error`, if set, is raised by login() instead of
    recording the call."""

    captured_kwargs: dict[str, object] = {}
    login_call: tuple[str, str] | None = None
    login_error: Exception | None = None

    def __init__(self, **kwargs: object) -> None:
        type(self).captured_kwargs = kwargs

    async def __aenter__(self) -> "_FakeSMTPClient":
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False

    async def login(self, username: str, password: str) -> None:
        if self.login_error is not None:
            raise self.login_error
        type(self).login_call = (username, password)


async def test_test_connection_uses_correct_tls_kwargs_and_logs_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeSMTPClient.login_error = None
    monkeypatch.setattr(aiosmtplib, "SMTP", _FakeSMTPClient)

    await smtp_transport.test_connection(
        smtp_host="mail.example.com",
        smtp_port=465,
        smtp_username="user",
        smtp_password="pass",
    )

    assert _FakeSMTPClient.captured_kwargs["use_tls"] is True
    assert _FakeSMTPClient.captured_kwargs["start_tls"] is False
    assert _FakeSMTPClient.login_call == ("user", "pass")


async def test_test_connection_wraps_auth_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeSMTPClient.login_error = aiosmtplib.SMTPAuthenticationError(535, "bad creds")
    monkeypatch.setattr(aiosmtplib, "SMTP", _FakeSMTPClient)

    with pytest.raises(EmailSendError, match="bad creds"):
        await smtp_transport.test_connection(
            smtp_host="mail.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="wrong",
        )
