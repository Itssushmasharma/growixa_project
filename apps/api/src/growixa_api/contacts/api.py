import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.contacts.models import (
    Contact,
    ContactCustomField,
    ContactList,
    Segment,
    SegmentRule,
    Tag,
)
from growixa_api.contacts.schemas import (
    AddListMemberIn,
    AttachTagIn,
    ContactIn,
    ContactListIn,
    ContactListOut,
    ContactOut,
    ContactUpdateIn,
    CustomFieldIn,
    CustomFieldOut,
    SegmentIn,
    SegmentOut,
    SegmentRuleOut,
    TagIn,
    TagOut,
    UpdateContactStatusIn,
)
from growixa_api.contacts.services import (
    ContactListNotFoundError,
    ContactNotFoundError,
    DuplicateEmailError,
    DuplicateFieldKeyError,
    DuplicateTagNameError,
    InvalidSegmentRuleError,
    SegmentNotFoundError,
    TagNotFoundError,
    UnknownCustomFieldError,
)
from growixa_api.contacts.services import add_contact_to_list as add_contact_to_list_service
from growixa_api.contacts.services import attach_tag_to_contact as attach_tag_service
from growixa_api.contacts.services import create_custom_field as create_custom_field_service
from growixa_api.contacts.services import create_list as create_list_service
from growixa_api.contacts.services import create_or_update_contact as create_or_update_service
from growixa_api.contacts.services import create_segment_with_rules as create_segment_service
from growixa_api.contacts.services import create_tag as create_tag_service
from growixa_api.contacts.services import detach_tag_from_contact as detach_tag_service
from growixa_api.contacts.services import get_contact_with_fields as get_contact_service
from growixa_api.contacts.services import get_list_with_count as get_list_service
from growixa_api.contacts.services import get_segment_with_details as get_segment_service
from growixa_api.contacts.services import list_contacts_with_fields as list_contacts_service
from growixa_api.contacts.services import list_custom_fields as list_custom_fields_service
from growixa_api.contacts.services import list_lists_with_counts as list_lists_service
from growixa_api.contacts.services import list_segment_members as list_segment_members_service
from growixa_api.contacts.services import list_segments_with_details as list_segments_service
from growixa_api.contacts.services import list_tags as list_tags_service
from growixa_api.contacts.services import (
    remove_contact_from_list as remove_contact_from_list_service,
)
from growixa_api.contacts.services import update_contact as update_contact_service
from growixa_api.contacts.services import update_contact_status as update_contact_status_service
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import require_permission

router = APIRouter(prefix="/contacts", tags=["contacts"])

_require_manage = require_permission("contacts.manage")
_require_view = require_permission("contacts.view")


def _to_out(contact: Contact, custom_fields: dict[str, str], tags: list[str]) -> ContactOut:
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
        tags=tags,
    )


def _list_to_out(contact_list: ContactList, member_count: int) -> ContactListOut:
    return ContactListOut(
        id=contact_list.id,
        name=contact_list.name,
        description=contact_list.description,
        member_count=member_count,
        created_at=contact_list.created_at,
        updated_at=contact_list.updated_at,
    )


def _segment_to_out(
    segment: Segment, rules: Sequence[SegmentRule], member_count: int
) -> SegmentOut:
    return SegmentOut(
        id=segment.id,
        name=segment.name,
        type=segment.type,
        member_count=member_count,
        created_at=segment.created_at,
        updated_at=segment.updated_at,
        rules=[SegmentRuleOut.model_validate(rule) for rule in rules],
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


@router.get("/tags", response_model=list[TagOut])
async def list_tags_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[Tag]:
    return list(await list_tags_service(session))


@router.post("/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag_route(
    payload: TagIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> Tag:
    try:
        return await create_tag_service(session, name=payload.name)
    except DuplicateTagNameError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A tag with this name already exists"
        ) from exc


@router.get("/lists", response_model=list[ContactListOut])
async def list_lists_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[ContactListOut]:
    lists_with_counts = await list_lists_service(session)
    return [_list_to_out(contact_list, count) for contact_list, count in lists_with_counts]


@router.post("/lists", response_model=ContactListOut, status_code=status.HTTP_201_CREATED)
async def create_list_route(
    payload: ContactListIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactListOut:
    contact_list, count = await create_list_service(
        session, actor_id=actor_id, name=payload.name, description=payload.description
    )
    return _list_to_out(contact_list, count)


@router.get("/lists/{list_id}", response_model=ContactListOut)
async def get_list_route(
    list_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> ContactListOut:
    try:
        contact_list, count = await get_list_service(session, list_id)
    except ContactListNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "List not found") from exc

    return _list_to_out(contact_list, count)


@router.post("/lists/{list_id}/members", response_model=ContactListOut)
async def add_list_member_route(
    list_id: uuid.UUID,
    payload: AddListMemberIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactListOut:
    try:
        contact_list, count = await add_contact_to_list_service(
            session, actor_id=actor_id, list_id=list_id, contact_id=payload.contact_id
        )
    except ContactListNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "List not found") from exc
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc

    return _list_to_out(contact_list, count)


@router.delete("/lists/{list_id}/members/{contact_id}", response_model=ContactListOut)
async def remove_list_member_route(
    list_id: uuid.UUID,
    contact_id: uuid.UUID,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactListOut:
    try:
        contact_list, count = await remove_contact_from_list_service(
            session, actor_id=actor_id, list_id=list_id, contact_id=contact_id
        )
    except ContactListNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "List not found") from exc
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc

    return _list_to_out(contact_list, count)


@router.get("/segments", response_model=list[SegmentOut])
async def list_segments_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[SegmentOut]:
    details = await list_segments_service(session)
    return [_segment_to_out(segment, rules, count) for segment, rules, count in details]


@router.post("/segments", response_model=SegmentOut, status_code=status.HTTP_201_CREATED)
async def create_segment_route(
    payload: SegmentIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> SegmentOut:
    try:
        segment, rules, count = await create_segment_service(
            session,
            actor_id=actor_id,
            name=payload.name,
            type_=payload.type,
            rules=[(r.field, r.operator, r.value) for r in payload.rules],
        )
    except InvalidSegmentRuleError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return _segment_to_out(segment, rules, count)


@router.get("/segments/{segment_id}", response_model=SegmentOut)
async def get_segment_route(
    segment_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> SegmentOut:
    try:
        segment, rules, count = await get_segment_service(session, segment_id)
    except SegmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Segment not found") from exc

    return _segment_to_out(segment, rules, count)


@router.get("/segments/{segment_id}/members", response_model=list[ContactOut])
async def list_segment_members_route(
    segment_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[ContactOut]:
    try:
        snapshots = await list_segment_members_service(session, segment_id)
    except SegmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Segment not found") from exc

    return [_to_out(contact, fields, tags) for contact, fields, tags in snapshots]


@router.get("", response_model=list[ContactOut])
async def list_contacts_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[ContactOut]:
    contacts_with_fields = await list_contacts_service(session)
    return [_to_out(contact, fields, tags) for contact, fields, tags in contacts_with_fields]


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact_route(
    payload: ContactIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields, tags = await create_or_update_service(
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

    return _to_out(contact, fields, tags)


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact_route(
    contact_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields, tags = await get_contact_service(session, contact_id)
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc

    return _to_out(contact, fields, tags)


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact_route(
    contact_id: uuid.UUID,
    payload: ContactUpdateIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields, tags = await update_contact_service(
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

    return _to_out(contact, fields, tags)


@router.patch("/{contact_id}/status", response_model=ContactOut)
async def update_contact_status_route(
    contact_id: uuid.UUID,
    payload: UpdateContactStatusIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields, tags = await update_contact_status_service(
            session, actor_id=actor_id, contact_id=contact_id, status=payload.status
        )
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc

    return _to_out(contact, fields, tags)


@router.post("/{contact_id}/tags", response_model=ContactOut)
async def attach_tag_route(
    contact_id: uuid.UUID,
    payload: AttachTagIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields, tags = await attach_tag_service(
            session, actor_id=actor_id, contact_id=contact_id, tag_id=payload.tag_id
        )
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc
    except TagNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tag not found") from exc

    return _to_out(contact, fields, tags)


@router.delete("/{contact_id}/tags/{tag_id}", response_model=ContactOut)
async def detach_tag_route(
    contact_id: uuid.UUID,
    tag_id: uuid.UUID,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    try:
        contact, fields, tags = await detach_tag_service(
            session, actor_id=actor_id, contact_id=contact_id, tag_id=tag_id
        )
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc
    except TagNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tag not found") from exc

    return _to_out(contact, fields, tags)
