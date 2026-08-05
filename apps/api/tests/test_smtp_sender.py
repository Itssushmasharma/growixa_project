"""Unit tests for smtp_sender.send_email's TLS-mode selection and error wrapping
(GRX-EMAIL-011 fixes, both found via a live test against a real Custom SMTP server).

Port 465 is implicit TLS; every other port is plaintext-then-STARTTLS. aiosmtplib itself
is mocked here — these tests only assert which mode we ask for, not real network behavior.
"""

import ssl
from unittest.mock import AsyncMock

import aiosmtplib
import pytest

from growixa_api.email_delivery import smtp_sender
from growixa_api.email_delivery.smtp_sender import EmailSendError


async def _send(monkeypatch: pytest.MonkeyPatch, *, smtp_port: int) -> AsyncMock:
    mock_send = AsyncMock()
    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    await smtp_sender.send_email(
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
        await smtp_sender.send_email(
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
