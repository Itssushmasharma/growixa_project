import logging

from growixa_api.config import get_settings
from growixa_api.integrations.smtp_transport import EmailSendError, send_email

logger = logging.getLogger("growixa_api")


async def send_verification_email(*, to_email: str, full_name: str, raw_token: str) -> None:
    """Best-effort: a failure here never fails registration itself -- the account row
    already exists regardless, and there is no compensating action to take. No-ops
    (logged) if platform_smtp_host isn't set, so registration keeps working before the
    operator has configured real SMTP credentials.

    Sent synchronously from the API process rather than via the worker's job queue --
    the same precedent already set by the "test connection" flow in
    integrations/smtp_transport.py. One transactional email per (rate-limited)
    registration isn't the bulk-send case BACKGROUND_JOB_ARCHITECTURE.md's
    inline-send rule exists to prevent.
    """
    settings = get_settings()
    if not settings.platform_smtp_host:
        logger.warning("platform SMTP not configured; skipping verification email to %s", to_email)
        return

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

    try:
        await send_email(
            smtp_host=settings.platform_smtp_host,
            smtp_port=settings.platform_smtp_port,
            smtp_username=settings.platform_smtp_username,
            smtp_password=settings.platform_smtp_password,
            from_email=settings.platform_smtp_from_email,
            from_name=settings.platform_smtp_from_name,
            to_email=to_email,
            subject="Verify your Growixa account",
            body_html=body_html,
            body_text=body_text,
        )
    except EmailSendError:
        logger.exception("failed to send verification email to %s", to_email)
