"""Unit tests for email_sender.send_email's TLS-mode selection and error wrapping.

Mirrors apps/api/tests/test_smtp_sender.py — port 465 is implicit TLS, every other port
is plaintext-then-STARTTLS; TLS/OS errors must come out as EmailSendError. aiosmtplib
itself is mocked here.
"""

import ssl
from unittest.mock import AsyncMock

import aiosmtplib
import pytest

from growixa_worker import email_sender
from growixa_worker.email_sender import EmailSendError


async def _send(monkeypatch: pytest.MonkeyPatch, *, smtp_port: int) -> AsyncMock:
    mock_send = AsyncMock()
    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    await email_sender.send_email(
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
    async def _raise(*args: object, **kwargs: object) -> None:
        raise ssl.SSLCertVerificationError("certificate has expired")

    monkeypatch.setattr(aiosmtplib, "send", _raise)

    with pytest.raises(EmailSendError, match="certificate has expired"):
        await email_sender.send_email(
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
