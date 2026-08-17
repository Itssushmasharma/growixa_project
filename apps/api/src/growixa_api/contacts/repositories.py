import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import ColumnElement, CursorResult, Select, and_, func, select, update
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


async def get_account_id_for_contact(
    session: AsyncSession, contact_id: uuid.UUID
) -> uuid.UUID | None:
    """Resolves a contact's owning account from its id alone -- for internal,
    cross-module callers (email_delivery webhook/unsubscribe handling) that already
    hold a trusted `contact_id` via an FK chain but don't yet have their own account
    context (campaigns/email_delivery aren't account-scoped until the next GRX-SAAS-001
    checkpoint). Not for use from any account-boundary-sensitive lookup."""
    result = await session.execute(select(Contact.account_id).where(Contact.id == contact_id))
    return result.scalar_one_or_none()


async def get_contact_by_email(
    session: AsyncSession, account_id: uuid.UUID, email: str
) -> Contact | None:
    result = await session.execute(
        select(Contact).where(
            Contact.account_id == account_id,
            Contact.email == email,
            Contact.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_contact_by_id(
    session: AsyncSession, account_id: uuid.UUID, contact_id: uuid.UUID
) -> Contact | None:
    result = await session.execute(
        select(Contact).where(
            Contact.account_id == account_id,
            Contact.id == contact_id,
            Contact.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def count_active_contacts(session: AsyncSession, account_id: uuid.UUID) -> int:
    """Feeds the plan's `max_contacts` cap check (`GRX-BILL-005`) -- archived and
    soft-deleted contacts don't count against it, only live active ones."""
    result = await session.execute(
        select(func.count())
        .select_from(Contact)
        .where(
            Contact.account_id == account_id,
            Contact.status == "ACTIVE",
            Contact.deleted_at.is_(None),
        )
    )
    return result.scalar_one()


async def list_contacts(session: AsyncSession, account_id: uuid.UUID) -> Sequence[Contact]:
    result = await session.execute(
        select(Contact)
        .where(Contact.account_id == account_id, Contact.deleted_at.is_(None))
        .order_by(Contact.created_at.desc())
    )
    return result.scalars().all()


async def soft_delete_contact(
    session: AsyncSession, account_id: uuid.UUID, contact_id: uuid.UUID
) -> bool:
    """Soft-deletes a single contact by setting deleted_at to current timestamp."""
    result = await session.execute(
        update(Contact)
        .where(
            Contact.account_id == account_id,
            Contact.id == contact_id,
            Contact.deleted_at.is_(None),
        )
        .values(deleted_at=func.now())
    )
    await session.flush()
    return int(cast(CursorResult[Any], result).rowcount) > 0


async def bulk_soft_delete_contacts(
    session: AsyncSession, account_id: uuid.UUID, contact_ids: Sequence[uuid.UUID]
) -> int:
    """Soft-deletes multiple contacts belonging to the account by setting deleted_at."""
    if not contact_ids:
        return 0
    result = await session.execute(
        update(Contact)
        .where(
            Contact.account_id == account_id,
            Contact.id.in_(contact_ids),
            Contact.deleted_at.is_(None),
        )
        .values(deleted_at=func.now())
    )
    await session.flush()
    return int(cast(CursorResult[Any], result).rowcount)


async def purge_all_contacts_in_account(session: AsyncSession, account_id: uuid.UUID) -> int:
    """Soft-deletes all non-deleted contacts belonging to the account."""
    result = await session.execute(
        update(Contact)
        .where(
            Contact.account_id == account_id,
            Contact.deleted_at.is_(None),
        )
        .values(deleted_at=func.now())
    )
    await session.flush()
    return int(cast(CursorResult[Any], result).rowcount)


async def create_contact(session: AsyncSession, **fields: Any) -> Contact:
    contact = Contact(**fields)
    session.add(contact)
    await session.flush()
    return contact


async def apply_contact_fields(contact: Contact, fields: dict[str, Any]) -> Contact:
    for key, value in fields.items():
        setattr(contact, key, value)
    return contact


async def get_custom_field_by_key(
    session: AsyncSession, account_id: uuid.UUID, key: str
) -> ContactCustomField | None:
    result = await session.execute(
        select(ContactCustomField).where(
            ContactCustomField.account_id == account_id, ContactCustomField.key == key
        )
    )
    return result.scalar_one_or_none()


async def list_custom_fields(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[ContactCustomField]:
    result = await session.execute(
        select(ContactCustomField)
        .where(ContactCustomField.account_id == account_id)
        .order_by(ContactCustomField.key)
    )
    return result.scalars().all()


async def create_custom_field(
    session: AsyncSession, *, account_id: uuid.UUID, key: str, label: str, field_type: str
) -> ContactCustomField:
    field = ContactCustomField(account_id=account_id, key=key, label=label, field_type=field_type)
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
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    contact_id: uuid.UUID,
    field_id: uuid.UUID,
    value: str,
) -> None:
    result = await session.execute(
        select(ContactFieldValue).where(
            ContactFieldValue.contact_id == contact_id, ContactFieldValue.field_id == field_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing is None:
        session.add(
            ContactFieldValue(
                account_id=account_id, contact_id=contact_id, field_id=field_id, value=value
            )
        )
    else:
        existing.value = value


async def get_tag_by_id(
    session: AsyncSession, account_id: uuid.UUID, tag_id: uuid.UUID
) -> Tag | None:
    result = await session.execute(
        select(Tag).where(Tag.account_id == account_id, Tag.id == tag_id)
    )
    return result.scalar_one_or_none()


async def get_tag_by_name(session: AsyncSession, account_id: uuid.UUID, name: str) -> Tag | None:
    result = await session.execute(
        select(Tag).where(Tag.account_id == account_id, Tag.name == name)
    )
    return result.scalar_one_or_none()


async def list_tags(session: AsyncSession, account_id: uuid.UUID) -> Sequence[Tag]:
    result = await session.execute(
        select(Tag).where(Tag.account_id == account_id).order_by(Tag.name)
    )
    return result.scalars().all()


async def create_tag(session: AsyncSession, *, account_id: uuid.UUID, name: str) -> Tag:
    tag = Tag(account_id=account_id, name=name)
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


async def attach_tag(
    session: AsyncSession, *, account_id: uuid.UUID, contact_id: uuid.UUID, tag_id: uuid.UUID
) -> None:
    if await is_tag_attached(session, contact_id=contact_id, tag_id=tag_id):
        return
    session.add(ContactTag(account_id=account_id, contact_id=contact_id, tag_id=tag_id))


async def detach_tag(session: AsyncSession, *, contact_id: uuid.UUID, tag_id: uuid.UUID) -> None:
    result = await session.execute(
        select(ContactTag).where(ContactTag.contact_id == contact_id, ContactTag.tag_id == tag_id)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        await session.delete(existing)


async def get_contact_list_by_id(
    session: AsyncSession, account_id: uuid.UUID, list_id: uuid.UUID
) -> ContactList | None:
    result = await session.execute(
        select(ContactList).where(ContactList.account_id == account_id, ContactList.id == list_id)
    )
    return result.scalar_one_or_none()


async def list_contact_lists(session: AsyncSession, account_id: uuid.UUID) -> Sequence[ContactList]:
    result = await session.execute(
        select(ContactList)
        .where(ContactList.account_id == account_id)
        .order_by(ContactList.created_at.desc())
    )
    return result.scalars().all()


async def create_contact_list(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    name: str,
    description: str | None,
    created_by_user_id: uuid.UUID,
) -> ContactList:
    contact_list = ContactList(
        account_id=account_id,
        name=name,
        description=description,
        created_by_user_id=created_by_user_id,
    )
    session.add(contact_list)
    await session.flush()
    return contact_list


async def count_list_members(session: AsyncSession, list_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count(ContactListMember.contact_id))
        .join(Contact, Contact.id == ContactListMember.contact_id)
        .where(ContactListMember.list_id == list_id, Contact.deleted_at.is_(None))
    )
    return result.scalar_one()


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
    session: AsyncSession, *, account_id: uuid.UUID, list_id: uuid.UUID, contact_id: uuid.UUID
) -> None:
    if await is_list_member(session, list_id=list_id, contact_id=contact_id):
        return
    session.add(ContactListMember(account_id=account_id, list_id=list_id, contact_id=contact_id))


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
    (and parse `created_at` values) before calling this — it assumes valid input.

    The `tag`/`custom_field:` subqueries below aren't themselves account-scoped, but
    every caller intersects the result with an account_id filter on the outer `Contact`
    query (see `_matching_contacts_query`), so a same-named tag/field key in another
    account can never leak a contact into these results.
    """
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


def _matching_contacts_query(
    account_id: uuid.UUID, rules: Sequence[SegmentRule]
) -> Select[tuple[Contact]]:
    conditions = [build_rule_condition(r.field, r.operator, r.value) for r in rules]
    query = select(Contact).where(
        Contact.account_id == account_id,
        Contact.deleted_at.is_(None),
    )
    if conditions:
        query = query.where(and_(*conditions))
    return query


async def evaluate_segment_rules(
    session: AsyncSession, account_id: uuid.UUID, rules: Sequence[SegmentRule]
) -> Sequence[Contact]:
    result = await session.execute(_matching_contacts_query(account_id, rules))
    return result.scalars().all()


async def count_dynamic_segment_members(
    session: AsyncSession, account_id: uuid.UUID, rules: Sequence[SegmentRule]
) -> int:
    conditions = [build_rule_condition(r.field, r.operator, r.value) for r in rules]
    query = (
        select(func.count())
        .select_from(Contact)
        .where(
            Contact.account_id == account_id,
            Contact.deleted_at.is_(None),
        )
    )
    if conditions:
        query = query.where(and_(*conditions))
    result = await session.execute(query)
    return result.scalar_one()


async def get_segment_by_id(
    session: AsyncSession, account_id: uuid.UUID, segment_id: uuid.UUID
) -> Segment | None:
    result = await session.execute(
        select(Segment).where(Segment.account_id == account_id, Segment.id == segment_id)
    )
    return result.scalar_one_or_none()


async def list_segments(session: AsyncSession, account_id: uuid.UUID) -> Sequence[Segment]:
    result = await session.execute(
        select(Segment).where(Segment.account_id == account_id).order_by(Segment.created_at.desc())
    )
    return result.scalars().all()


async def create_segment(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    name: str,
    type_: str,
    created_by_user_id: uuid.UUID,
) -> Segment:
    segment = Segment(
        account_id=account_id, name=name, type=type_, created_by_user_id=created_by_user_id
    )
    session.add(segment)
    await session.flush()
    return segment


async def add_segment_rule(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    segment_id: uuid.UUID,
    field: str,
    operator: str,
    value: str,
) -> SegmentRule:
    rule = SegmentRule(
        account_id=account_id, segment_id=segment_id, field=field, operator=operator, value=value
    )
    session.add(rule)
    await session.flush()
    return rule


async def list_segment_rules(session: AsyncSession, segment_id: uuid.UUID) -> Sequence[SegmentRule]:
    result = await session.execute(select(SegmentRule).where(SegmentRule.segment_id == segment_id))
    return result.scalars().all()


async def add_segment_members(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    segment_id: uuid.UUID,
    contact_ids: Sequence[uuid.UUID],
) -> None:
    for contact_id in contact_ids:
        session.add(
            SegmentMember(account_id=account_id, segment_id=segment_id, contact_id=contact_id)
        )


async def count_saved_segment_members(session: AsyncSession, segment_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count(SegmentMember.contact_id))
        .join(Contact, Contact.id == SegmentMember.contact_id)
        .where(SegmentMember.segment_id == segment_id, Contact.deleted_at.is_(None))
    )
    return result.scalar_one()


async def list_saved_segment_members(
    session: AsyncSession, segment_id: uuid.UUID
) -> Sequence[Contact]:
    result = await session.execute(
        select(Contact)
        .join(SegmentMember, SegmentMember.contact_id == Contact.id)
        .where(SegmentMember.segment_id == segment_id, Contact.deleted_at.is_(None))
    )
    return result.scalars().all()


async def create_import(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    filename: str,
    column_mapping: dict[str, str],
    created_by_user_id: uuid.UUID,
) -> ContactImport:
    contact_import = ContactImport(
        account_id=account_id,
        filename=filename,
        column_mapping=column_mapping,
        created_by_user_id=created_by_user_id,
    )
    session.add(contact_import)
    await session.flush()
    return contact_import


async def get_import_by_id(
    session: AsyncSession, account_id: uuid.UUID, import_id: uuid.UUID
) -> ContactImport | None:
    result = await session.execute(
        select(ContactImport).where(
            ContactImport.account_id == account_id, ContactImport.id == import_id
        )
    )
    return result.scalar_one_or_none()


async def list_imports(session: AsyncSession, account_id: uuid.UUID) -> Sequence[ContactImport]:
    result = await session.execute(
        select(ContactImport)
        .where(ContactImport.account_id == account_id)
        .order_by(ContactImport.created_at.desc())
    )
    return result.scalars().all()


async def add_import_row(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    import_id: uuid.UUID,
    row_number: int,
    email: str | None,
    status: str,
    error_message: str | None,
) -> ContactImportRow:
    row = ContactImportRow(
        account_id=account_id,
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
    account_id: uuid.UUID,
    contact_id: uuid.UUID,
    channel: str,
    status: str,
    source: str | None,
    recorded_by_user_id: uuid.UUID | None,
) -> ConsentRecord:
    record = ConsentRecord(
        account_id=account_id,
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


async def get_suppression_by_email(
    session: AsyncSession, account_id: uuid.UUID, email: str
) -> SuppressionEntry | None:
    result = await session.execute(
        select(SuppressionEntry).where(
            SuppressionEntry.account_id == account_id, SuppressionEntry.email == email
        )
    )
    return result.scalar_one_or_none()


async def list_suppression_entries(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[SuppressionEntry]:
    result = await session.execute(
        select(SuppressionEntry)
        .where(SuppressionEntry.account_id == account_id)
        .order_by(SuppressionEntry.suppressed_at.desc())
    )
    return result.scalars().all()


async def is_email_suppressed(session: AsyncSession, account_id: uuid.UUID, email: str) -> bool:
    return await get_suppression_by_email(session, account_id, email) is not None


async def create_suppression_entry(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    email: str,
    reason: str,
    contact_id: uuid.UUID | None,
    suppressed_by_user_id: uuid.UUID | None,
) -> SuppressionEntry:
    entry = SuppressionEntry(
        account_id=account_id,
        email=email,
        reason=reason,
        contact_id=contact_id,
        suppressed_by_user_id=suppressed_by_user_id,
    )
    session.add(entry)
    await session.flush()
    return entry


async def get_suppression_by_domain(
    session: AsyncSession, account_id: uuid.UUID, domain: str
) -> SuppressionEntry | None:
    result = await session.execute(
        select(SuppressionEntry).where(
            SuppressionEntry.account_id == account_id, SuppressionEntry.domain == domain
        )
    )
    return result.scalar_one_or_none()


async def create_domain_suppression_entry(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    domain: str,
    suppressed_by_user_id: uuid.UUID | None,
) -> SuppressionEntry:
    entry = SuppressionEntry(
        account_id=account_id,
        domain=domain,
        reason="MANUAL",
        suppressed_by_user_id=suppressed_by_user_id,
    )
    session.add(entry)
    await session.flush()
    return entry


async def get_suppression_entry_by_id(
    session: AsyncSession, account_id: uuid.UUID, entry_id: uuid.UUID
) -> SuppressionEntry | None:
    result = await session.execute(
        select(SuppressionEntry).where(
            SuppressionEntry.account_id == account_id, SuppressionEntry.id == entry_id
        )
    )
    return result.scalar_one_or_none()


async def delete_suppression_entry(session: AsyncSession, entry: SuppressionEntry) -> None:
    await session.delete(entry)
    await session.flush()
