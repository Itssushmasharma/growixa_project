import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.contacts.models import Contact, ContactCustomField
from growixa_api.contacts.schemas import (
    ContactIn,
    ContactOut,
    ContactUpdateIn,
    CustomFieldIn,
    CustomFieldOut,
    UpdateContactStatusIn,
)
from growixa_api.contacts.services import (
    ContactNotFoundError,
    DuplicateEmailError,
    DuplicateFieldKeyError,
    UnknownCustomFieldError,
)
from growixa_api.contacts.services import create_custom_field as create_custom_field_service
from growixa_api.contacts.services import create_or_update_contact as create_or_update_service
from growixa_api.contacts.services import get_contact_with_fields as get_contact_service
from growixa_api.contacts.services import list_contacts_with_fields as list_contacts_service
from growixa_api.contacts.services import list_custom_fields as list_custom_fields_service
from growixa_api.contacts.services import update_contact as update_contact_service
from growixa_api.contacts.services import update_contact_status as update_contact_status_service
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import require_permission

router = APIRouter(prefix="/contacts", tags=["contacts"])

_require_manage = require_permission("contacts.manage")
_require_view = require_permission("contacts.view")


def _to_out(contact: Contact, custom_fields: dict[str, str]) -> ContactOut:
    return ContactOut(
        id=contact.id,
        email=contact.email,
        first_name=contact.first_name,
        last_name=contact.last_name,
        phone=contact.phone,
        status=contact.status,
        source=contact.source,
        created_at=contact.created_at,
        updated_at=contact.updated_at,
        custom_fields=custom_fields,
    )


@router.get("/custom-fields", response_model=list[CustomFieldOut])
async def list_custom_fields_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[ContactCustomField]:
    return list(await list_custom_fields_service(session))


@router.post("/custom-fields", response_model=CustomFieldOut, status_code=status.HTTP_201_CREATED)
async def create_custom_field_route(
    payload: CustomFieldIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactCustomField:
    try:
        return await create_custom_field_service(
            session, key=payload.key, label=payload.label, field_type=payload.field_type
        )
    except DuplicateFieldKeyError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A custom field with this key already exists"
        ) from exc


@router.get("", response_model=list[ContactOut])
async def list_contacts_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[ContactOut]:
    contacts_with_fields = await list_contacts_service(session)
    return [_to_out(contact, fields) for contact, fields in contacts_with_fields]


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact_route(
    payload: ContactIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields = await create_or_update_service(
            session,
            actor_id=actor_id,
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            source=payload.source,
            custom_fields=payload.custom_fields,
        )
    except UnknownCustomFieldError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Unknown custom field key: {exc.key}"
        ) from exc

    return _to_out(contact, fields)


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact_route(
    contact_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields = await get_contact_service(session, contact_id)
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc

    return _to_out(contact, fields)


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact_route(
    contact_id: uuid.UUID,
    payload: ContactUpdateIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields = await update_contact_service(
            session,
            actor_id=actor_id,
            contact_id=contact_id,
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            custom_fields=payload.custom_fields,
        )
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc
    except DuplicateEmailError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Another contact already uses this email"
        ) from exc
    except UnknownCustomFieldError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Unknown custom field key: {exc.key}"
        ) from exc

    return _to_out(contact, fields)


@router.patch("/{contact_id}/status", response_model=ContactOut)
async def update_contact_status_route(
    contact_id: uuid.UUID,
    payload: UpdateContactStatusIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields = await update_contact_status_service(
            session, actor_id=actor_id, contact_id=contact_id, status=payload.status
        )
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc

    return _to_out(contact, fields)
