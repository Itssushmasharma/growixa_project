import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import ColumnElement, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_worker.models import (
    Campaign,
    Contact,
    ContactCustomField,
    ContactFieldValue,
    ContactListMember,
    ContactTag,
    Segment,
    SegmentMember,
    SegmentRule,
    Tag,
)


def _build_rule_condition(field: str, operator: str, value: str) -> ColumnElement[bool]:
    """Mirrors growixa_api.contacts.repositories.build_rule_condition — duplicated, not
    imported, since the worker doesn't depend on growixa_api (see models.py's module
    docstring). Must stay in sync with that function's field/operator support."""
    if field == "status":
        return Contact.status == value
    if field == "email":
        return Contact.email == value if operator == "equals" else Contact.email.ilike(f"%{value}%")
    if field == "source":
        return Contact.source == value
    if field == "created_at":
        parsed = datetime.fromisoformat(value)
        return Contact.created_at < parsed if operator == "before" else Contact.created_at > parsed
    if field == "tag":
        return Contact.id.in_(
            select(ContactTag.contact_id)
            .join(Tag, Tag.id == ContactTag.tag_id)
            .where(Tag.name == value)
        )
    if field.startswith("custom_field:"):
        key = field.split(":", 1)[1]
        subquery = (
            select(ContactFieldValue.contact_id)
            .join(ContactCustomField, ContactCustomField.id == ContactFieldValue.field_id)
            .where(ContactCustomField.key == key)
        )
        subquery = subquery.where(
            ContactFieldValue.value == value
            if operator == "equals"
            else ContactFieldValue.value.ilike(f"%{value}%")
        )
        return Contact.id.in_(subquery)
    raise ValueError(f"Unsupported segment rule field: {field}")


async def _resolve_dynamic_segment(
    session: AsyncSession, segment_id: uuid.UUID
) -> Sequence[Contact]:
    rules_result = await session.execute(
        select(SegmentRule).where(SegmentRule.segment_id == segment_id)
    )
    rules = rules_result.scalars().all()
    conditions = [_build_rule_condition(r.field, r.operator, r.value) for r in rules]
    query = select(Contact).where(Contact.status == "ACTIVE")
    if conditions:
        query = query.where(and_(*conditions))
    contacts_result = await session.execute(query)
    return contacts_result.scalars().all()


async def _resolve_saved_segment(session: AsyncSession, segment_id: uuid.UUID) -> Sequence[Contact]:
    result = await session.execute(
        select(Contact)
        .join(SegmentMember, SegmentMember.contact_id == Contact.id)
        .where(SegmentMember.segment_id == segment_id, Contact.status == "ACTIVE")
    )
    return result.scalars().all()


async def _resolve_list(session: AsyncSession, list_id: uuid.UUID) -> Sequence[Contact]:
    result = await session.execute(
        select(Contact)
        .join(ContactListMember, ContactListMember.contact_id == Contact.id)
        .where(ContactListMember.list_id == list_id, Contact.status == "ACTIVE")
    )
    return result.scalars().all()


async def _resolve_all_contacts(session: AsyncSession) -> Sequence[Contact]:
    result = await session.execute(select(Contact).where(Contact.status == "ACTIVE"))
    return result.scalars().all()


async def resolve_recipients(session: AsyncSession, campaign: Campaign) -> Sequence[Contact]:
    """Materializes whichever targeting rule the campaign uses, evaluated at this exact
    moment — a DYNAMIC segment changing later never retroactively alters who a past
    campaign was sent to (DATA_MODEL.md's `campaign_recipients` note)."""
    if campaign.recipient_type == "ALL_CONTACTS":
        return await _resolve_all_contacts(session)
    if campaign.recipient_type == "LIST":
        assert campaign.recipient_list_id is not None
        return await _resolve_list(session, campaign.recipient_list_id)
    assert campaign.recipient_segment_id is not None
    segment = await session.get(Segment, campaign.recipient_segment_id)
    assert segment is not None
    if segment.type == "DYNAMIC":
        return await _resolve_dynamic_segment(session, segment.id)
    return await _resolve_saved_segment(session, segment.id)
