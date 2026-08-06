import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion


async def create_template(session: AsyncSession, fields: dict[str, Any]) -> EmailTemplate:
    template = EmailTemplate(**fields)
    session.add(template)
    await session.flush()
    return template


async def get_template(session: AsyncSession, template_id: uuid.UUID) -> EmailTemplate | None:
    return await session.get(EmailTemplate, template_id)


async def delete_template(session: AsyncSession, template: EmailTemplate) -> None:
    await session.delete(template)


async def list_templates(session: AsyncSession) -> Sequence[EmailTemplate]:
    result = await session.execute(select(EmailTemplate).order_by(EmailTemplate.created_at))
    return result.scalars().all()


async def create_template_version(
    session: AsyncSession, fields: dict[str, Any]
) -> EmailTemplateVersion:
    version = EmailTemplateVersion(**fields)
    session.add(version)
    await session.flush()
    return version


async def get_latest_version_number(session: AsyncSession, template_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.max(EmailTemplateVersion.version_number)).where(
            EmailTemplateVersion.template_id == template_id
        )
    )
    return result.scalar() or 0


async def get_current_version(
    session: AsyncSession, template_id: uuid.UUID
) -> EmailTemplateVersion | None:
    result = await session.execute(
        select(EmailTemplateVersion)
        .where(EmailTemplateVersion.template_id == template_id)
        .order_by(EmailTemplateVersion.version_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_versions(
    session: AsyncSession, template_id: uuid.UUID
) -> Sequence[EmailTemplateVersion]:
    result = await session.execute(
        select(EmailTemplateVersion)
        .where(EmailTemplateVersion.template_id == template_id)
        .order_by(EmailTemplateVersion.version_number.desc())
    )
    return result.scalars().all()
