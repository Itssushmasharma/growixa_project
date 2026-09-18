import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission
from growixa_api.personalization.renderer import PersonalizationError
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion
from growixa_api.templates.schemas import (
    EmailTemplateIn,
    EmailTemplateOut,
    EmailTemplateVersionIn,
    EmailTemplateVersionOut,
    TemplateValidationIn,
    TemplateValidationOut,
)
from growixa_api.templates.services import (
    TemplateInUseError,
    TemplateNotFoundError,
    add_template_version,
    clone_template_for_account,
    create_template,
    delete_template,
    duplicate_template_service,
    get_template_with_current_version,
    list_platform_default_templates_with_current_version,
    list_template_versions,
    list_templates_with_current_version,
    validate_template_content,
)

router = APIRouter(prefix="/templates", tags=["templates"])

_require_manage = require_permission("campaigns.manage")
_require_view = require_permission("campaigns.view")


def _to_out(
    template: EmailTemplate, current_version: EmailTemplateVersion | None
) -> EmailTemplateOut:
    return EmailTemplateOut(
        id=template.id,
        name=template.name,
        is_platform_default=template.is_platform_default,
        created_at=template.created_at,
        updated_at=template.updated_at,
        current_version=(
            EmailTemplateVersionOut.model_validate(current_version)
            if current_version is not None
            else None
        ),
    )


@router.get("", response_model=list[EmailTemplateOut])
async def list_templates_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[EmailTemplateOut]:
    templates = await list_templates_with_current_version(session, account_id)
    return [_to_out(template, version) for template, version in templates]


@router.post("", response_model=EmailTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template_route(
    payload: EmailTemplateIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> EmailTemplateOut:
    try:
        template, version = await create_template(session, account_id, payload, actor_id)
    except PersonalizationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    await session.commit()
    return _to_out(template, version)


@router.get("/platform-defaults", response_model=list[EmailTemplateOut])
async def list_platform_default_templates_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[EmailTemplateOut]:
    """Browse-only (GRX-EMAIL-016) -- every account sees the same platform-published
    defaults; deliberately not account-scoped, unlike list_templates_route above. Must be
    registered before /{template_id} or "platform-defaults" would be swallowed by that
    route's UUID path param and 422 instead of matching here."""
    templates = await list_platform_default_templates_with_current_version(session)
    return [_to_out(template, version) for template, version in templates]


@router.post("/validate", response_model=TemplateValidationOut)
async def validate_template_route(
    payload: TemplateValidationIn,
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> TemplateValidationOut:
    """Validates subject, HTML body, and plain-text body against personalization tokens.
    Returns validation status and any compliance warnings."""
    try:
        warnings = await validate_template_content(
            session,
            account_id,
            payload.subject,
            payload.body_html,
            payload.body_text,
        )
        return TemplateValidationOut(valid=True, warnings=warnings)
    except PersonalizationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.post(
    "/{template_id}/clone", response_model=EmailTemplateOut, status_code=status.HTTP_201_CREATED
)
async def clone_platform_default_template_route(
    template_id: uuid.UUID,
    actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> EmailTemplateOut:
    """The "Use this template" action -- clones a platform default into the caller's own
    account as an independent, editable row (clone-not-edit, GRX-EMAIL-016)."""
    try:
        template, version = await clone_template_for_account(
            session, account_id, template_id, actor_id
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found") from exc
    except PersonalizationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    await session.commit()
    return _to_out(template, version)


@router.post(
    "/{template_id}/duplicate", response_model=EmailTemplateOut, status_code=status.HTTP_201_CREATED
)
async def duplicate_template_route(
    template_id: uuid.UUID,
    actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> EmailTemplateOut:
    """Duplicates an account-owned email template into '{name} (Copy)'."""
    try:
        template, version = await duplicate_template_service(
            session, account_id, template_id, actor_id
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found") from exc
    except PersonalizationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    await session.commit()
    return _to_out(template, version)


@router.get("/{template_id}", response_model=EmailTemplateOut)
async def get_template_route(
    template_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> EmailTemplateOut:
    try:
        template, version = await get_template_with_current_version(
            session, account_id, template_id
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found") from exc
    return _to_out(template, version)


@router.get("/{template_id}/versions", response_model=list[EmailTemplateVersionOut])
async def list_template_versions_route(
    template_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[EmailTemplateVersionOut]:
    try:
        versions = await list_template_versions(session, account_id, template_id)
    except TemplateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found") from exc
    return [EmailTemplateVersionOut.model_validate(version) for version in versions]


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template_route(
    template_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await delete_template(session, account_id, template_id)
    except TemplateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found") from exc
    except TemplateInUseError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This template is referenced by one or more campaigns and cannot be deleted",
        ) from exc
    await session.commit()


@router.post("/{template_id}/versions", response_model=EmailTemplateOut)
async def add_template_version_route(
    template_id: uuid.UUID,
    payload: EmailTemplateVersionIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> EmailTemplateOut:
    try:
        template, version = await add_template_version(
            session, account_id, template_id, payload, actor_id
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found") from exc
    except PersonalizationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    await session.commit()
    return _to_out(template, version)
