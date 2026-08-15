import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import decrypt_secret, encrypt_secret
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.integrations.smtp_transport import send_email as smtp_send_email
from growixa_api.integrations.smtp_transport import test_connection as smtp_test_connection
from growixa_api.notifications import repositories
from growixa_api.notifications.models import PlatformEmailProviderConfig
from growixa_api.notifications.schemas import PlatformEmailProviderConfigIn


async def get_platform_config(session: AsyncSession) -> PlatformEmailProviderConfig | None:
    return await repositories.get_active_platform_config(session)


async def set_platform_config(
    session: AsyncSession,
    data: PlatformEmailProviderConfigIn,
    actor_platform_admin_id: uuid.UUID,
) -> PlatformEmailProviderConfig:
    """Deactivates any existing active platform email config and creates a new row --
    same deactivate-then-insert convention as PlatformAIProviderConfig."""
    await repositories.deactivate_active_platform_config(session)
    return await repositories.create_platform_config(
        session,
        {
            "provider": data.provider,
            "smtp_host": data.smtp_host,
            "smtp_port": data.smtp_port,
            "smtp_username": data.smtp_username,
            "smtp_password_encrypted": encrypt_secret(data.smtp_password),
            "from_email": data.from_email,
            "from_name": data.from_name,
            "created_by_platform_admin_id": actor_platform_admin_id,
        },
    )


async def test_platform_config_connection(data: PlatformEmailProviderConfigIn) -> None:
    """Connects and authenticates with the given (not-yet-saved) credentials -- nothing
    is persisted, no message is sent. Same "test before save" convention as
    integrations/smtp_transport.py's own test_connection (GRX-EMAIL-012) and
    ai/services.py's AI provider test_connection."""
    await smtp_test_connection(
        smtp_host=data.smtp_host,
        smtp_port=data.smtp_port,
        smtp_username=data.smtp_username,
        smtp_password=data.smtp_password,
    )


async def send_via_platform_config(
    config: PlatformEmailProviderConfig,
    *,
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str,
) -> None:
    await smtp_send_email(
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_username=config.smtp_username,
        smtp_password=decrypt_secret(config.smtp_password_encrypted),
        from_email=config.from_email,
        from_name=config.from_name,
        to_email=to_email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
    )


__all__ = [
    "EmailSendError",
    "get_platform_config",
    "send_via_platform_config",
    "set_platform_config",
    "test_platform_config_connection",
]
