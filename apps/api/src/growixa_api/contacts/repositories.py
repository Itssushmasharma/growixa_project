import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import ColumnElement, Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.contacts.models import (
    ConsentRecord,
    Contact,
    ContactCustomField,
    ContactFieldValue,
    ContactImport,
    ContactImportRow,
    ContactList,
    ContactListMember,
    ContactTag,
    Segment,
    SegmentMember,
    SegmentRule,
    SuppressionEntry,
    Tag,
)


async def get_contact_by_email(session: AsyncSession, email: str) -> Contact | None:
    result = await session.execute(select(Contact).where(Contact.email == email))
    return result.scalar_one_or_none()


async def get_contact_by_id(session: AsyncSession, contact_id: uuid.UUID) -> Contact | None:
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    return result.scalar_one_or_none()


async def list_contacts(session: AsyncSession) -> Sequence[Contact]:
    result = await session.execute(select(Contact).order_by(Contact.created_at.desc()))
    return result.scalars().all()


async def create_contact(session: AsyncSession, **fields: Any) -> Contact:
    contact = Contact(**fields)
    session.add(contact)
    await session.flush()
    return contact


async def apply_contact_fields(contact: Contact, fields: dict[str, Any]) -> Contact:
    for key, value in fields.items():
        setattr(contact, key, value)
    return contact


async def get_custom_field_by_key(session: AsyncSession, key: str) -> ContactCustomField | None:
    result = await session.execute(select(ContactCustomField).where(ContactCustomField.key == key))
    return result.scalar_one_or_none()


async def list_custom_fields(session: AsyncSession) -> Sequence[ContactCustomField]:
    result = await session.execute(select(ContactCustomField).order_by(ContactCustomField.key))
    return result.scalars().all()


async def create_custom_field(
    session: AsyncSession, *, key: str, label: str, field_type: str
) -> ContactCustomField:
    field = ContactCustomField(key=key, label=label, field_type=field_type)
    session.add(field)
    await session.flush()
    return field


async def get_field_values_for_contact(
    session: AsyncSession, contact_id: uuid.UUID
) -> dict[str, str]:
    result = await session.execute(
        select(ContactCustomField.key, ContactFieldValue.value)
        .join(ContactFieldValue, ContactFieldValue.field_id == ContactCustomField.id)
        .where(ContactFieldValue.contact_id == contact_id)
    )
    return {key: value for key, value in result.all() if value is not None}


async def upsert_field_value(
    session: AsyncSession, *, contact_id: uuid.UUID, field_id: uuid.UUID, value: str
) -> None:
    result = await session.execute(
        select(ContactFieldValue).where(
            ContactFieldValue.contact_id == contact_id, ContactFieldValue.field_id == field_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing is None:
        session.add(ContactFieldValue(contact_id=contact_id, field_id=field_id, value=value))
    else:
        existing.value = value


async def get_tag_by_id(session: AsyncSession, tag_id: uuid.UUID) -> Tag | None:
    result = await session.execute(select(Tag).where(Tag.id == tag_id))
    return result.scalar_one_or_none()


async def get_tag_by_name(session: AsyncSession, name: str) -> Tag | None:
    result = await session.execute(select(Tag).where(Tag.name == name))
    return result.scalar_one_or_none()


async def list_tags(session: AsyncSession) -> Sequence[Tag]:
    result = await session.execute(select(Tag).order_by(Tag.name))
    return result.scalars().all()


async def create_tag(session: AsyncSession, *, name: str) -> Tag:
    tag = Tag(name=name)
    session.add(tag)
    await session.flush()
    return tag


async def get_tag_names_for_contact(session: AsyncSession, contact_id: uuid.UUID) -> list[str]:
    result = await session.execute(
        select(Tag.name)
        .join(ContactTag, ContactTag.tag_id == Tag.id)
        .where(ContactTag.contact_id == contact_id)
    )
    return [row[0] for row in result.all()]


async def is_tag_attached(
    session: AsyncSession, *, contact_id: uuid.UUID, tag_id: uuid.UUID
) -> bool:
    result = await session.execute(
        select(ContactTag).where(ContactTag.contact_id == contact_id, ContactTag.tag_id == tag_id)
    )
    return result.scalar_one_or_none() is not None


async def attach_tag(session: AsyncSession, *, contact_id: uuid.UUID, tag_id: uuid.UUID) -> None:
    if await is_tag_attached(session, contact_id=contact_id, tag_id=tag_id):
        return
    session.add(ContactTag(contact_id=contact_id, tag_id=tag_id))


async def detach_tag(session: AsyncSession, *, contact_id: uuid.UUID, tag_id: uuid.UUID) -> None:
    result = await session.execute(
        select(ContactTag).where(ContactTag.contact_id == contact_id, ContactTag.tag_id == tag_id)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        await session.delete(existing)


async def get_contact_list_by_id(session: AsyncSession, list_id: uuid.UUID) -> ContactList | None:
    result = await session.execute(select(ContactList).where(ContactList.id == list_id))
    return result.scalar_one_or_none()


async def list_contact_lists(session: AsyncSession) -> Sequence[ContactList]:
    result = await session.execute(select(ContactList).order_by(ContactList.created_at.desc()))
    return result.scalars().all()


async def create_contact_list(
    session: AsyncSession, *, name: str, description: str | None, created_by_user_id: uuid.UUID
) -> ContactList:
    contact_list = ContactList(
        name=name, description=description, created_by_user_id=created_by_user_id
    )
    session.add(contact_list)
    await session.flush()
    return contact_list


async def count_list_members(session: AsyncSession, list_id: uuid.UUID) -> int:
    result = await session.execute(
        select(ContactListMember).where(ContactListMember.list_id == list_id)
    )
    return len(result.scalars().all())


async def is_list_member(
    session: AsyncSession, *, list_id: uuid.UUID, contact_id: uuid.UUID
) -> bool:
    result = await session.execute(
        select(ContactListMember).where(
            ContactListMember.list_id == list_id, ContactListMember.contact_id == contact_id
        )
    )
    return result.scalar_one_or_none() is not None


async def add_list_member(
    session: AsyncSession, *, list_id: uuid.UUID, contact_id: uuid.UUID
) -> None:
    if await is_list_member(session, list_id=list_id, contact_id=contact_id):
        return
    session.add(ContactListMember(list_id=list_id, contact_id=contact_id))


async def remove_list_member(
    session: AsyncSession, *, list_id: uuid.UUID, contact_id: uuid.UUID
) -> None:
    result = await session.execute(
        select(ContactListMember).where(
            ContactListMember.list_id == list_id, ContactListMember.contact_id == contact_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        await session.delete(existing)


# Field -> allowed operators for segment rules. `custom_field:<key>` fields are validated
# separately (the key must exist in contact_custom_fields) but share the equals/contains
# operator set. Kept intentionally small — see DATA_MODEL.md §Slice 2 entities: all rules
# on a segment are AND-combined only, no OR/grouping in Slice 2.
SEGMENT_RULE_FIELD_OPERATORS: dict[str, set[str]] = {
    "status": {"equals"},
    "email": {"equals", "contains"},
    "source": {"equals"},
    "tag": {"equals"},
    "created_at": {"before", "after"},
}
CUSTOM_FIELD_RULE_OPERATORS = {"equals", "contains"}


def build_rule_condition(field: str, operator: str, value: str) -> ColumnElement[bool]:
    """Translate one validated (field, operator, value) triple into a SQLAlchemy
    boolean expression over `Contact`. Callers must validate field/operator combinations
    (and parse `created_at` values) before calling this — it assumes valid input."""
    if field == "status":
        return Contact.status == value
    if field == "email":
        return Contact.email == value if operator == "equals" else Contact.email.ilike(f"%{value}%")
    if field == "source":
        return Contact.source == value
    if field == "tag":
        return Contact.id.in_(
            select(ContactTag.contact_id)
            .join(Tag, Tag.id == ContactTag.tag_id)
            .where(Tag.name == value)
        )
    if field == "created_at":
        parsed = datetime.fromisoformat(value)
        return Contact.created_at < parsed if operator == "before" else Contact.created_at > parsed
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


def _matching_contacts_query(rules: Sequence[SegmentRule]) -> Select[tuple[Contact]]:
    conditions = [build_rule_condition(r.field, r.operator, r.value) for r in rules]
    query = select(Contact)
    if conditions:
        query = query.where(and_(*conditions))
    return query


async def evaluate_segment_rules(
    session: AsyncSession, rules: Sequence[SegmentRule]
) -> Sequence[Contact]:
    result = await session.execute(_matching_contacts_query(rules))
    return result.scalars().all()


async def count_dynamic_segment_members(session: AsyncSession, rules: Sequence[SegmentRule]) -> int:
    conditions = [build_rule_condition(r.field, r.operator, r.value) for r in rules]
    query = select(func.count()).select_from(Contact)
    if conditions:
        query = query.where(and_(*conditions))
    result = await session.execute(query)
    return result.scalar_one()


async def get_segment_by_id(session: AsyncSession, segment_id: uuid.UUID) -> Segment | None:
    result = await session.execute(select(Segment).where(Segment.id == segment_id))
    return result.scalar_one_or_none()


async def list_segments(session: AsyncSession) -> Sequence[Segment]:
    result = await session.execute(select(Segment).order_by(Segment.created_at.desc()))
    return result.scalars().all()


async def create_segment(
    session: AsyncSession, *, name: str, type_: str, created_by_user_id: uuid.UUID
) -> Segment:
    segment = Segment(name=name, type=type_, created_by_user_id=created_by_user_id)
    session.add(segment)
    await session.flush()
    return segment


async def add_segment_rule(
    session: AsyncSession, *, segment_id: uuid.UUID, field: str, operator: str, value: str
) -> SegmentRule:
    rule = SegmentRule(segment_id=segment_id, field=field, operator=operator, value=value)
    session.add(rule)
    await session.flush()
    return rule


async def list_segment_rules(session: AsyncSession, segment_id: uuid.UUID) -> Sequence[SegmentRule]:
    result = await session.execute(select(SegmentRule).where(SegmentRule.segment_id == segment_id))
    return result.scalars().all()


async def add_segment_members(
    session: AsyncSession, *, segment_id: uuid.UUID, contact_ids: Sequence[uuid.UUID]
) -> None:
    for contact_id in contact_ids:
        session.add(SegmentMember(segment_id=segment_id, contact_id=contact_id))


async def count_saved_segment_members(session: AsyncSession, segment_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(SegmentMember)
        .where(SegmentMember.segment_id == segment_id)
    )
    return result.scalar_one()


async def list_saved_segment_members(
    session: AsyncSession, segment_id: uuid.UUID
) -> Sequence[Contact]:
    result = await session.execute(
        select(Contact)
        .join(SegmentMember, SegmentMember.contact_id == Contact.id)
        .where(SegmentMember.segment_id == segment_id)
    )
    return result.scalars().all()


async def create_import(
    session: AsyncSession,
    *,
    filename: str,
    column_mapping: dict[str, str],
    created_by_user_id: uuid.UUID,
) -> ContactImport:
    contact_import = ContactImport(
        filename=filename, column_mapping=column_mapping, created_by_user_id=created_by_user_id
    )
    session.add(contact_import)
    await session.flush()
    return contact_import


async def get_import_by_id(session: AsyncSession, import_id: uuid.UUID) -> ContactImport | None:
    result = await session.execute(select(ContactImport).where(ContactImport.id == import_id))
    return result.scalar_one_or_none()


async def list_imports(session: AsyncSession) -> Sequence[ContactImport]:
    result = await session.execute(select(ContactImport).order_by(ContactImport.created_at.desc()))
    return result.scalars().all()


async def add_import_row(
    session: AsyncSession,
    *,
    import_id: uuid.UUID,
    row_number: int,
    email: str | None,
    status: str,
    error_message: str | None,
) -> ContactImportRow:
    row = ContactImportRow(
        import_id=import_id,
        row_number=row_number,
        email=email,
        status=status,
        error_message=error_message,
    )
    session.add(row)
    await session.flush()
    return row


async def list_import_rows(
    session: AsyncSession, import_id: uuid.UUID
) -> Sequence[ContactImportRow]:
    result = await session.execute(
        select(ContactImportRow)
        .where(ContactImportRow.import_id == import_id)
        .order_by(ContactImportRow.row_number)
    )
    return result.scalars().all()


async def create_consent_record(
    session: AsyncSession,
    *,
    contact_id: uuid.UUID,
    channel: str,
    status: str,
    source: str | None,
    recorded_by_user_id: uuid.UUID | None,
) -> ConsentRecord:
    record = ConsentRecord(
        contact_id=contact_id,
        channel=channel,
        status=status,
        source=source,
        recorded_by_user_id=recorded_by_user_id,
    )
    session.add(record)
    await session.flush()
    return record


async def list_consent_records(
    session: AsyncSession, contact_id: uuid.UUID
) -> Sequence[ConsentRecord]:
    result = await session.execute(
        select(ConsentRecord)
        .where(ConsentRecord.contact_id == contact_id)
        .order_by(ConsentRecord.recorded_at.desc())
    )
    return result.scalars().all()


async def get_suppression_by_email(session: AsyncSession, email: str) -> SuppressionEntry | None:
    result = await session.execute(select(SuppressionEntry).where(SuppressionEntry.email == email))
    return result.scalar_one_or_none()


async def list_suppression_entries(session: AsyncSession) -> Sequence[SuppressionEntry]:
    result = await session.execute(
        select(SuppressionEntry).order_by(SuppressionEntry.suppressed_at.desc())
    )
    return result.scalars().all()


async def is_email_suppressed(session: AsyncSession, email: str) -> bool:
    return await get_suppression_by_email(session, email) is not None


async def create_suppression_entry(
    session: AsyncSession,
    *,
    email: str,
    reason: str,
    contact_id: uuid.UUID | None,
    suppressed_by_user_id: uuid.UUID | None,
) -> SuppressionEntry:
    entry = SuppressionEntry(
        email=email,
        reason=reason,
        contact_id=contact_id,
        suppressed_by_user_id=suppressed_by_user_id,
    )
    session.add(entry)
    await session.flush()
    return entry
