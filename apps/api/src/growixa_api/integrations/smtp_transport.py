from email.message import EmailMessage
from typing import TypedDict

import aiosmtplib

# A "test connection" check is interactive (a user is waiting on it in the UI), unlike a
# real send which runs in the background — so it gets a much shorter timeout than
# aiosmtplib's 60s default.
TEST_CONNECTION_TIMEOUT_SECONDS = 10


class EmailSendError(Exception):
    """Wraps any SMTP-transport failure (connection, TLS, auth, rejected recipient) behind
    one type so callers don't need to know aiosmtplib's exception hierarchy."""


class _TlsKwargs(TypedDict):
    use_tls: bool
    start_tls: bool


def _tls_kwargs(smtp_port: int) -> _TlsKwargs:
    # Port 465 is implicit TLS (encrypted from the first byte); every other port
    # (587, 25, ...) is plaintext-then-STARTTLS. Passing start_tls=True to a port-465
    # server makes aiosmtplib wait for a plaintext banner that never arrives.
    implicit_tls = smtp_port == 465
    return {"use_tls": implicit_tls, "start_tls": not implicit_tls}


async def send_email(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    from_email: str,
    from_name: str,
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None,
) -> None:
    message = EmailMessage()
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body_text or "")
    message.add_alternative(body_html, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            **_tls_kwargs(smtp_port),
        )
    except (aiosmtplib.SMTPException, OSError, ValueError) as exc:
        # OSError also catches ssl.SSLError (e.g. an expired/invalid server certificate
        # surfaces as ssl.SSLCertVerificationError, not an SMTPException) plus raw
        # connection failures (DNS, refused, reset) that aiosmtplib doesn't wrap itself.
        # ValueError catches aiosmtplib's own pre-flight config validation (e.g. a
        # hostname/port that fails its sanity checks) -- a real production incident hit
        # this exact path (a newline-contaminated SMTP host env var) and crashed
        # registration with an unhandled 500 instead of just skipping the email, which
        # defeats the whole point of every caller treating this as best-effort.
        raise EmailSendError(str(exc)) from exc


async def test_connection(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
) -> None:
    """Connects and authenticates only — sends no message. Used to validate credentials
    during setup, before a connection is saved (or resaved)."""
    try:
        async with aiosmtplib.SMTP(
            hostname=smtp_host,
            port=smtp_port,
            timeout=TEST_CONNECTION_TIMEOUT_SECONDS,
            **_tls_kwargs(smtp_port),
        ) as smtp:
            await smtp.login(smtp_username, smtp_password)
    except (aiosmtplib.SMTPException, OSError) as exc:
        raise EmailSendError(str(exc)) from exc
