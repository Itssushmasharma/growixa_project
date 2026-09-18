# ruff: noqa: E501

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.repositories import get_platform_system_account_id
from growixa_api.contacts.models import ContactCustomField
from growixa_api.personalization.renderer import (
    validate_template_tokens,
)
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion
from growixa_api.templates.repositories import (
    create_template as create_template_row,
)
from growixa_api.templates.repositories import (
    create_template_version,
    get_current_version,
    get_latest_version_number,
    get_platform_default_template,
    get_template,
    list_platform_default_templates,
    list_templates,
    list_versions,
)
from growixa_api.templates.repositories import (
    delete_template as delete_template_row,
)
from growixa_api.templates.schemas import EmailTemplateIn, EmailTemplateVersionIn


class TemplateNotFoundError(Exception):
    pass


class TemplateInUseError(Exception):
    """Raised when deleting a template blocked by campaigns.template_id's foreign key —
    a campaign copies a template's content at creation time (DATA_MODEL.md's "ad hoc
    content" design), so the FK exists only to preserve the "created from" link, not
    because the campaign depends on the template still existing. No ON DELETE behavior
    is set for it, so this is a real DB-enforced block, not a bug — surfaced as a clean
    409 instead of a raw 500."""


async def _validate_template_personalization(
    session: AsyncSession,
    account_id: uuid.UUID,
    subject: str,
    body_html: str,
    body_text: str | None,
) -> None:
    res = await session.execute(
        select(ContactCustomField.key).where(
            ContactCustomField.account_id == account_id,
            ContactCustomField.is_personalization_usable.is_(True),
        )
    )
    allowed_custom_keys = set(res.scalars().all())
    validate_template_tokens(subject, allowed_custom_field_keys=allowed_custom_keys)
    validate_template_tokens(body_html, allowed_custom_field_keys=allowed_custom_keys)
    if body_text:
        validate_template_tokens(body_text, allowed_custom_field_keys=allowed_custom_keys)


async def create_template(
    session: AsyncSession, account_id: uuid.UUID, data: EmailTemplateIn, actor_id: uuid.UUID
) -> tuple[EmailTemplate, EmailTemplateVersion]:
    await _validate_template_personalization(
        session, account_id, data.subject, data.body_html, data.body_text
    )
    template = await create_template_row(
        session, {"account_id": account_id, "name": data.name, "created_by_user_id": actor_id}
    )
    version = await create_template_version(
        session,
        {
            "account_id": account_id,
            "template_id": template.id,
            "version_number": 1,
            "subject": data.subject,
            "body_html": data.body_html,
            "body_text": data.body_text,
            "created_by_user_id": actor_id,
        },
    )
    return template, version


async def delete_template(
    session: AsyncSession, account_id: uuid.UUID, template_id: uuid.UUID
) -> None:
    template = await get_template(session, account_id, template_id)
    if template is None:
        raise TemplateNotFoundError
    try:
        await delete_template_row(session, template)
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise TemplateInUseError from exc


async def get_template_with_current_version(
    session: AsyncSession, account_id: uuid.UUID, template_id: uuid.UUID
) -> tuple[EmailTemplate, EmailTemplateVersion | None]:
    template = await get_template(session, account_id, template_id)
    if template is None:
        raise TemplateNotFoundError
    version = await get_current_version(session, template_id)
    return template, version


async def list_templates_with_current_version(
    session: AsyncSession, account_id: uuid.UUID
) -> list[tuple[EmailTemplate, EmailTemplateVersion | None]]:
    templates = await list_templates(session, account_id)
    return [(template, await get_current_version(session, template.id)) for template in templates]


async def list_template_versions(
    session: AsyncSession, account_id: uuid.UUID, template_id: uuid.UUID
) -> Sequence[EmailTemplateVersion]:
    template = await get_template(session, account_id, template_id)
    if template is None:
        raise TemplateNotFoundError
    return await list_versions(session, template_id)


async def add_template_version(
    session: AsyncSession,
    account_id: uuid.UUID,
    template_id: uuid.UUID,
    data: EmailTemplateVersionIn,
    actor_id: uuid.UUID,
) -> tuple[EmailTemplate, EmailTemplateVersion]:
    """Editing a template always appends a new version — the previous version's row is
    never touched, per DATA_MODEL.md's insert-only history for `email_template_versions`."""
    template = await get_template(session, account_id, template_id)
    if template is None:
        raise TemplateNotFoundError
    await _validate_template_personalization(
        session, account_id, data.subject, data.body_html, data.body_text
    )
    next_version_number = await get_latest_version_number(session, template_id) + 1
    version = await create_template_version(
        session,
        {
            "account_id": account_id,
            "template_id": template_id,
            "version_number": next_version_number,
            "subject": data.subject,
            "body_html": data.body_html,
            "body_text": data.body_text,
            "created_by_user_id": actor_id,
        },
    )
    return template, version


# --- Platform-published default templates (GRX-EMAIL-016) -----------------------------
#
# Owned by the reserved platform system account, gated by platform.templates.manage
# (never require_permission -- platform admins are not `users` rows, DEC-GRX-018).
# Deliberately no account-scoped custom-field tokens: validate_template_tokens() with no
# allowed_custom_field_keys only accepts the standard recipient/account tokens, which
# resolve the same for every account regardless of that account's own custom fields.


async def create_platform_template(
    session: AsyncSession, data: EmailTemplateIn
) -> tuple[EmailTemplate, EmailTemplateVersion]:
    platform_account_id = await get_platform_system_account_id(session)
    validate_template_tokens(data.subject)
    validate_template_tokens(data.body_html)
    if data.body_text:
        validate_template_tokens(data.body_text)

    template = await create_template_row(
        session,
        {
            "account_id": platform_account_id,
            "name": data.name,
            "is_platform_default": True,
        },
    )
    version = await create_template_version(
        session,
        {
            "account_id": platform_account_id,
            "template_id": template.id,
            "version_number": 1,
            "subject": data.subject,
            "body_html": data.body_html,
            "body_text": data.body_text,
        },
    )
    return template, version


async def add_platform_template_version(
    session: AsyncSession, template_id: uuid.UUID, data: EmailTemplateVersionIn
) -> tuple[EmailTemplate, EmailTemplateVersion]:
    """Same insert-only-history semantics as add_template_version -- editing a platform
    default never mutates a version already-cloned copies point at, since a clone owns
    an entirely separate EmailTemplate/EmailTemplateVersion row (see clone_template_for_
    account) and never references the platform original at all after the clone."""
    template = await get_platform_default_template(session, template_id)
    if template is None:
        raise TemplateNotFoundError
    validate_template_tokens(data.subject)
    validate_template_tokens(data.body_html)
    if data.body_text:
        validate_template_tokens(data.body_text)

    next_version_number = await get_latest_version_number(session, template_id) + 1
    version = await create_template_version(
        session,
        {
            "account_id": template.account_id,
            "template_id": template_id,
            "version_number": next_version_number,
            "subject": data.subject,
            "body_html": data.body_html,
            "body_text": data.body_text,
        },
    )
    return template, version


async def retire_platform_template(session: AsyncSession, template_id: uuid.UUID) -> None:
    template = await get_platform_default_template(session, template_id)
    if template is None:
        raise TemplateNotFoundError
    await delete_template_row(session, template)


async def list_platform_default_templates_with_current_version(
    session: AsyncSession,
) -> list[tuple[EmailTemplate, EmailTemplateVersion | None]]:
    templates = await list_platform_default_templates(session)
    return [(template, await get_current_version(session, template.id)) for template in templates]


async def clone_template_for_account(
    session: AsyncSession,
    account_id: uuid.UUID,
    template_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> tuple[EmailTemplate, EmailTemplateVersion]:
    """The "Use this template" action (GRX-EMAIL-016): creates an independent, account-owned copy —
    clone-not-edit is a hard requirement, so the customer never gets a reference to the
    platform-owned original. A later platform update or retirement of that original
    therefore cannot alter, break, or silently mutate a campaign already built from the
    clone."""
    source = await get_platform_default_template(session, template_id)
    if source is None:
        raise TemplateNotFoundError
    source_version = await get_current_version(session, template_id)
    if source_version is None:
        raise TemplateNotFoundError

    await _validate_template_personalization(
        session,
        account_id,
        source_version.subject,
        source_version.body_html,
        source_version.body_text,
    )

    clone = await create_template_row(
        session,
        {
            "account_id": account_id,
            "name": source.name,
            "is_platform_default": False,
            "created_by_user_id": actor_id,
        },
    )
    clone_version = await create_template_version(
        session,
        {
            "account_id": account_id,
            "template_id": clone.id,
            "version_number": 1,
            "subject": source_version.subject,
            "body_html": source_version.body_html,
            "body_text": source_version.body_text,
            "created_by_user_id": actor_id,
        },
    )
    return clone, clone_version


async def duplicate_template_service(
    session: AsyncSession,
    account_id: uuid.UUID,
    template_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> tuple[EmailTemplate, EmailTemplateVersion]:
    """Duplicates an account-owned email template into a new template with name '{original_name} (Copy)'.
    Enforces multi-tenant account isolation."""
    source = await get_template(session, account_id, template_id)
    if source is None:
        raise TemplateNotFoundError
    source_version = await get_current_version(session, template_id)
    if source_version is None:
        raise TemplateNotFoundError

    await _validate_template_personalization(
        session,
        account_id,
        source_version.subject,
        source_version.body_html,
        source_version.body_text,
    )

    duplicate_name = f"{source.name} (Copy)"
    new_template = await create_template_row(
        session,
        {
            "account_id": account_id,
            "name": duplicate_name,
            "is_platform_default": False,
            "created_by_user_id": actor_id,
        },
    )
    new_version = await create_template_version(
        session,
        {
            "account_id": account_id,
            "template_id": new_template.id,
            "version_number": 1,
            "subject": source_version.subject,
            "body_html": source_version.body_html,
            "body_text": source_version.body_text,
            "created_by_user_id": actor_id,
        },
    )
    return new_template, new_version


async def validate_template_content(
    session: AsyncSession,
    account_id: uuid.UUID,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> list[str]:
    """Validates template tokens and returns a list of warnings (e.g. missing unsubscribe tag).
    Raises PersonalizationError if invalid tokens or unclosed tags are present."""
    await _validate_template_personalization(
        session,
        account_id,
        subject,
        body_html,
        body_text,
    )
    warnings: list[str] = []
    if "{{unsubscribe_url}}" not in body_html:
        warnings.append(
            "Notice: Template does not contain an explicit {{unsubscribe_url}} placeholder. "
            "A default compliance unsubscribe footer will be automatically appended."
        )
    return warnings
