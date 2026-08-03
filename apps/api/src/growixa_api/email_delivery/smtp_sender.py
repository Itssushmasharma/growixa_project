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

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            start_tls=True,
        )
    except aiosmtplib.SMTPException as exc:
        raise EmailSendError(str(exc)) from exc
