import logging

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.integrations.smtp_transport import send_email as smtp_send_email
from growixa_api.notifications.layout import EmailContent, render
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
    content = EmailContent(
        subject="Verify your Growixa account",
        preheader="Confirm your email address to activate your Growixa account.",
        heading=f"Welcome to Growixa, {full_name}",
        paragraphs=("Confirm your email address to activate your account and get started.",),
        action_label="Verify my email",
        action_url=verify_url,
        footer_note=(
            f"This link expires in {settings.email_verification_ttl_hours} hours. "
            "If you did not create a Growixa account, you can ignore this email."
        ),
    )
    await _deliver(content, to_email=to_email, description="verification email")


async def send_password_reset_email(*, to_email: str, raw_token: str) -> None:
    """Best-effort password reset notification using the same platform transactional email
    channel as account verification. Failures are logged without raising so the public
    request endpoint can keep its enumeration-safe generic response."""
    settings = get_settings()
    reset_url = f"{settings.frontend_base_url}/reset-password?token={raw_token}"
    content = EmailContent(
        subject="Reset your Growixa password",
        preheader="Choose a new password for your Growixa account.",
        heading="Reset your password",
        paragraphs=(
            "We received a request to reset your Growixa password. "
            "Choose a new one using the button below.",
        ),
        action_label="Choose a new password",
        action_url=reset_url,
        footer_note=(
            f"This link expires in {settings.password_reset_ttl_minutes} minutes "
            "and can be used once. If you did not request this, you can ignore this "
            "email -- your password will not change."
        ),
    )
    await _deliver(content, to_email=to_email, description="password reset email")


async def send_invitation_email(
    *,
    to_email: str,
    account_name: str,
    invited_by_name: str,
    role_name: str,
    raw_token: str,
) -> None:
    """Best-effort team invitation (GRX-USER-003). Same fire-and-forget contract as the
    other two: the invitation row and its token already exist once this runs, and
    users/api.py still returns the raw token to the inviting admin, so a send failure
    degrades to the pre-existing "share the token out of band" path rather than losing
    the invitation."""
    settings = get_settings()
    accept_url = f"{settings.frontend_base_url}/accept-invitation?token={raw_token}"
    content = EmailContent(
        subject=f"{invited_by_name} invited you to {account_name} on Growixa",
        preheader=f"Set up your account to join {account_name} on Growixa.",
        heading=f"Join {account_name} on Growixa",
        paragraphs=(
            f"{invited_by_name} has invited you to join {account_name} on Growixa as {role_name}.",
            "Accept the invitation to set your password and finish creating your account.",
        ),
        action_label="Accept invitation",
        action_url=accept_url,
        footer_note=(
            f"This invitation expires in {settings.invitation_ttl_days} days. "
            "If you were not expecting it, you can ignore this email."
        ),
    )
    await _deliver(content, to_email=to_email, description="invitation email")


async def _deliver(content: EmailContent, *, to_email: str, description: str) -> None:
    """Shared best-effort delivery wrapper. Every transactional message swallows
    EmailSendError -- see each sender's docstring for why its own caller must not fail
    on a send problem -- so the try/except lives here once instead of per sender."""
    rendered = render(content)
    try:
        async with async_session_factory() as session:
            await _send(
                session,
                to_email=to_email,
                subject=rendered.subject,
                body_html=rendered.html,
                body_text=rendered.text,
            )
    except EmailSendError:
        logger.exception("failed to send %s to %s", description, to_email)


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
