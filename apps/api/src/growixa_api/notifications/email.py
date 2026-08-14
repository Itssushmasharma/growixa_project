import logging

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.integrations.smtp_transport import send_email as smtp_send_email
from growixa_api.notifications.repositories import get_active_platform_config
from growixa_api.notifications.services import send_via_platform_config

logger = logging.getLogger("growixa_api")


async def send_verification_email(*, to_email: str, full_name: str, raw_token: str) -> None:
    """Best-effort: a failure here never fails registration itself -- the account row
    already exists regardless, and there is no compensating action to take. Called as a
    FastAPI BackgroundTask from accounts/api.py's register_route, not awaited inline --
    a real production incident showed an unreachable SMTP relay could otherwise hold a
    registration request open for up to a minute.

    Resolution order: the platform admin's DB-configured provider
    (platform_email_provider_config) if one is active, else the legacy .env-only
    PLATFORM_SMTP_* settings (so an existing deployment isn't broken by this table's
    introduction), else no-ops (logged) so registration keeps working before any email
    provider has been configured at all.
    """
    settings = get_settings()
    verify_url = f"{settings.frontend_base_url}/verify-email?token={raw_token}"
    body_html = (
        f"<p>Hi {full_name},</p>"
        "<p>Welcome to Growixa! Click the link below to verify your email and activate "
        "your account:</p>"
        f'<p><a href="{verify_url}">{verify_url}</a></p>'
        f"<p>This link expires in {settings.email_verification_ttl_hours} hours.</p>"
    )
    body_text = (
        f"Hi {full_name},\n\n"
        "Welcome to Growixa! Visit the link below to verify your email and activate "
        f"your account:\n{verify_url}\n\n"
        f"This link expires in {settings.email_verification_ttl_hours} hours."
    )
    subject = "Verify your Growixa account"

    try:
        async with async_session_factory() as session:
            await _send(
                session,
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
            )
    except EmailSendError:
        logger.exception("failed to send verification email to %s", to_email)


async def _send(
    session: AsyncSession, *, to_email: str, subject: str, body_html: str, body_text: str
) -> None:
    config = await get_active_platform_config(session)
    if config is not None:
        await send_via_platform_config(
            config, to_email=to_email, subject=subject, body_html=body_html, body_text=body_text
        )
        return

    settings = get_settings()
    if not settings.platform_smtp_host:
        logger.warning(
            "no platform email provider configured (neither DB nor .env); skipping email to %s",
            to_email,
        )
        return

    await smtp_send_email(
        smtp_host=settings.platform_smtp_host,
        smtp_port=settings.platform_smtp_port,
        smtp_username=settings.platform_smtp_username,
        smtp_password=settings.platform_smtp_password,
        from_email=settings.platform_smtp_from_email,
        from_name=settings.platform_smtp_from_name,
        to_email=to_email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
    )
