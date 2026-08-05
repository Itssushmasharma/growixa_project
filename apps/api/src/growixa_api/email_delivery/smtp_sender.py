from email.message import EmailMessage

import aiosmtplib


class EmailSendError(Exception):
    """Wraps any SMTP-transport failure (connection, TLS, auth, rejected recipient) behind
    one type so callers don't need to know aiosmtplib's exception hierarchy."""


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

    # Port 465 is implicit TLS (encrypted from the first byte); every other port
    # (587, 25, ...) is plaintext-then-STARTTLS. Passing start_tls=True to a port-465
    # server makes aiosmtplib wait for a plaintext banner that never arrives.
    implicit_tls = smtp_port == 465

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=implicit_tls,
            start_tls=not implicit_tls,
        )
    except (aiosmtplib.SMTPException, OSError) as exc:
        # OSError also catches ssl.SSLError (e.g. an expired/invalid server certificate
        # surfaces as ssl.SSLCertVerificationError, not an SMTPException) plus raw
        # connection failures (DNS, refused, reset) that aiosmtplib doesn't wrap itself.
        raise EmailSendError(str(exc)) from exc
