from __future__ import annotations

import abc
import ssl
from email.message import EmailMessage

import aiosmtplib


class EmailSendError(Exception):
    """Wraps any SMTP-transport failure behind one type."""


def _build_tls_context() -> ssl.SSLContext:
    """Build a TLS context that encrypts all traffic and accommodates self-hosted
    SMTP relays with self-signed/internal certificates."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class BaseWorkerEmailProvider(abc.ABC):
    @abc.abstractmethod
    async def send(
        self,
        *,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        raise NotImplementedError


class WorkerSmtpProvider(BaseWorkerEmailProvider):
    def __init__(self, *, host: str, port: int, username: str, password: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    async def send(
        self,
        *,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        message = EmailMessage()
        message["From"] = f"{from_name} <{from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        for name, value in (extra_headers or {}).items():
            message[name] = value
        message.set_content(body_text or "")
        message.add_alternative(body_html, subtype="html")

        implicit_tls = self.port == 465
        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=implicit_tls,
                start_tls=not implicit_tls,
                validate_certs=False,
                tls_context=_build_tls_context(),
            )
        except (aiosmtplib.SMTPException, OSError) as exc:
            raise EmailSendError(str(exc)) from exc


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
    extra_headers: dict[str, str] | None = None,
) -> None:
    provider = WorkerSmtpProvider(
        host=smtp_host,
        port=smtp_port,
        username=smtp_username,
        password=smtp_password,
    )
    await provider.send(
        from_email=from_email,
        from_name=from_name,
        to_email=to_email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        extra_headers=extra_headers,
    )
