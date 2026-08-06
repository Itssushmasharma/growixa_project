import uuid
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion
from growixa_api.templates.repositories import (
    create_template as create_template_row,
)
from growixa_api.templates.repositories import (
    create_template_version,
    get_current_version,
    get_latest_version_number,
    get_template,
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


async def create_template(
    session: AsyncSession, data: EmailTemplateIn, actor_id: uuid.UUID
) -> tuple[EmailTemplate, EmailTemplateVersion]:
    template = await create_template_row(
        session, {"name": data.name, "created_by_user_id": actor_id}
    )
    version = await create_template_version(
        session,
        {
            "template_id": template.id,
            "version_number": 1,
            "subject": data.subject,
            "body_html": data.body_html,
            "body_text": data.body_text,
            "created_by_user_id": actor_id,
        },
    )
    return template, version


async def delete_template(session: AsyncSession, template_id: uuid.UUID) -> None:
    template = await get_template(session, template_id)
    if template is None:
        raise TemplateNotFoundError
    try:
        await delete_template_row(session, template)
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise TemplateInUseError from exc


async def get_template_with_current_version(
    session: AsyncSession, template_id: uuid.UUID
) -> tuple[EmailTemplate, EmailTemplateVersion | None]:
    template = await get_template(session, template_id)
    if template is None:
        raise TemplateNotFoundError
    version = await get_current_version(session, template_id)
    return template, version


async def list_templates_with_current_version(
    session: AsyncSession,
) -> list[tuple[EmailTemplate, EmailTemplateVersion | None]]:
    templates = await list_templates(session)
    return [(template, await get_current_version(session, template.id)) for template in templates]


async def list_template_versions(
    session: AsyncSession, template_id: uuid.UUID
) -> Sequence[EmailTemplateVersion]:
    template = await get_template(session, template_id)
    if template is None:
        raise TemplateNotFoundError
    return await list_versions(session, template_id)


async def add_template_version(
    session: AsyncSession,
    template_id: uuid.UUID,
    data: EmailTemplateVersionIn,
    actor_id: uuid.UUID,
) -> tuple[EmailTemplate, EmailTemplateVersion]:
    """Editing a template always appends a new version — the previous version's row is
    never touched, per DATA_MODEL.md's insert-only history for `email_template_versions`."""
    template = await get_template(session, template_id)
    if template is None:
        raise TemplateNotFoundError
    next_version_number = await get_latest_version_number(session, template_id) + 1
    version = await create_template_version(
        session,
        {
            "template_id": template_id,
            "version_number": next_version_number,
            "subject": data.subject,
            "body_html": data.body_html,
            "body_text": data.body_text,
            "created_by_user_id": actor_id,
        },
    )
    return template, version
