from __future__ import annotations

import abc
import ssl
from contextlib import suppress
from email.message import EmailMessage

import aiosmtplib

from growixa_api.auth.encryption import decrypt_secret
from growixa_api.integrations.models import EmailProviderConnection
from growixa_api.integrations.smtp_transport import EmailSendError


def _build_tls_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class BaseEmailProvider(abc.ABC):
    """Abstract base class for all Growixa email delivery providers.
    Enables pluggable providers (Postmark, Custom SMTP, Resend, SES, etc.)
    with a unified interface for sending and connection testing."""

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Name/identifier of the provider (e.g. POSTMARK, CUSTOM_SMTP)."""
        raise NotImplementedError

    @abc.abstractmethod
    async def test_connection(self) -> None:
        """Validates credentials and connectivity without sending an email.
        Raises EmailSendError on failure."""
        raise NotImplementedError

    @abc.abstractmethod
    async def send_email(
        self,
        *,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None,
        reply_to_email: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        """Sends an email message through this provider.
        Raises EmailSendError on failure."""
        raise NotImplementedError


class CustomSmtpEmailProvider(BaseEmailProvider):
    """SMTP provider for self-hosted relays, Postal, Stalwart, or generic SMTP servers."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    @property
    def provider_name(self) -> str:
        return "CUSTOM_SMTP"

    async def test_connection(self) -> None:
        implicit_tls = self.port == 465
        client = aiosmtplib.SMTP(
            hostname=self.host,
            port=self.port,
            use_tls=implicit_tls,
            start_tls=not implicit_tls,
            validate_certs=False,
            tls_context=_build_tls_context(),
            timeout=10,
        )
        try:
            await client.connect()
            if self.username or self.password:
                await client.login(self.username, self.password)
        except (aiosmtplib.SMTPException, OSError) as exc:
            raise EmailSendError(str(exc)) from exc
        finally:
            with suppress(Exception):
                await client.quit()

    async def send_email(
        self,
        *,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None,
        reply_to_email: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        message = EmailMessage()
        message["From"] = f"{from_name} <{from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        if reply_to_email:
            message["Reply-To"] = reply_to_email
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


class PostmarkEmailProvider(CustomSmtpEmailProvider):
    """Postmark provider utilizing Postmark's SMTP relay endpoint with token authentication."""

    @property
    def provider_name(self) -> str:
        return "POSTMARK"


def get_email_provider(connection: EmailProviderConnection) -> BaseEmailProvider:
    """Factory function returning the appropriate BaseEmailProvider instance for a connection."""
    password = decrypt_secret(connection.smtp_password_encrypted)
    if connection.provider == "POSTMARK":
        return PostmarkEmailProvider(
            host=connection.smtp_host,
            port=connection.smtp_port,
            username=connection.smtp_username,
            password=password,
        )
    return CustomSmtpEmailProvider(
        host=connection.smtp_host,
        port=connection.smtp_port,
        username=connection.smtp_username,
        password=password,
    )
