import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import (
    ColumnElement,
    CursorResult,
    Select,
    and_,
    delete,
    exists,
    func,
    or_,
    select,
    text,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.campaigns.models import Campaign
from growixa_api.contacts.constants import (
    SegmentRuleField,
    SegmentRuleOperator,
)
from growixa_api.contacts.models import (
    ConsentRecord,
    Contact,
    ContactActivity,
    ContactCustomField,
    ContactFieldValue,
    ContactImport,
    ContactImportRow,
    ContactList,
    ContactListMember,
    ContactTag,
    CRMCompany,
    Segment,
    SegmentMember,
    SegmentRule,
    SuppressionEntry,
    Tag,
)
from growixa_api.pagination import DEFAULT_LIMIT


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


async def get_contact_by_id_including_deleted(
    session: AsyncSession, account_id: uuid.UUID, contact_id: uuid.UUID
) -> Contact | None:
    result = await session.execute(
        select(Contact).where(
            Contact.account_id == account_id,
            Contact.id == contact_id,
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


def _contact_search_condition(search: str) -> ColumnElement[bool]:
    """Free-text search across the same fields the (now-removed) client-side filter used
    to check -- email, first/last name, source -- so server-side search matches the exact
    UX the Contacts page previously implemented in the browser (GRX-PERF-001 follow-up)."""
    like = f"%{search}%"
    return or_(
        Contact.email.ilike(like),
        Contact.first_name.ilike(like),
        Contact.last_name.ilike(like),
        Contact.source.ilike(like),
    )


def _contact_tag_condition(tag_id: uuid.UUID) -> ColumnElement[bool]:
    return Contact.id.in_(select(ContactTag.contact_id).where(ContactTag.tag_id == tag_id))


def _contact_filter_conditions(
    account_id: uuid.UUID,
    *,
    include_deleted: bool,
    deleted_only: bool,
    status: str | None,
    search: str | None,
    tag_id: uuid.UUID | None,
    company_id: uuid.UUID | None = None,
    lifecycle_stage: str | None = None,
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = [Contact.account_id == account_id]
    if deleted_only:
        conditions.append(Contact.deleted_at.is_not(None))
    elif not include_deleted:
        conditions.append(Contact.deleted_at.is_(None))
    if status is not None:
        conditions.append(Contact.status == status)
    if search:
        conditions.append(_contact_search_condition(search))
    if tag_id is not None:
        conditions.append(_contact_tag_condition(tag_id))
    if company_id is not None:
        conditions.append(Contact.company_id == company_id)
    if lifecycle_stage is not None:
        conditions.append(Contact.lifecycle_stage == lifecycle_stage)
    return conditions


async def list_contacts(
    session: AsyncSession,
    account_id: uuid.UUID,
    *,
    include_deleted: bool = False,
    deleted_only: bool = False,
    status: str | None = None,
    search: str | None = None,
    tag_id: uuid.UUID | None = None,
    company_id: uuid.UUID | None = None,
    lifecycle_stage: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Sequence[Contact]:
    conditions = _contact_filter_conditions(
        account_id,
        include_deleted=include_deleted,
        deleted_only=deleted_only,
        status=status,
        search=search,
        tag_id=tag_id,
        company_id=company_id,
        lifecycle_stage=lifecycle_stage,
    )
    query = select(Contact).where(*conditions)
    query = query.order_by(Contact.deleted_at.desc() if deleted_only else Contact.created_at.desc())
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    return result.scalars().all()


async def count_contacts(
    session: AsyncSession,
    account_id: uuid.UUID,
    *,
    include_deleted: bool = False,
    deleted_only: bool = False,
    status: str | None = None,
    search: str | None = None,
    tag_id: uuid.UUID | None = None,
    company_id: uuid.UUID | None = None,
    lifecycle_stage: str | None = None,
) -> int:
    """SQL-level `COUNT(*)` matching the same filters as `list_contacts` -- feeds the
    Contacts page's "total pages" figure without ever fetching the matching rows
    themselves (GRX-PERF-001 follow-up: the frontend used to derive this from
    `.length` on a full unbounded fetch)."""
    conditions = _contact_filter_conditions(
        account_id,
        include_deleted=include_deleted,
        deleted_only=deleted_only,
        status=status,
        search=search,
        tag_id=tag_id,
        company_id=company_id,
        lifecycle_stage=lifecycle_stage,
    )
    result = await session.execute(select(func.count()).select_from(Contact).where(*conditions))
    return result.scalar_one()


async def get_contact_stats(session: AsyncSession, account_id: uuid.UUID) -> dict[str, int]:
    """Account-wide contact status counts via a single `COUNT(*) FILTER (WHERE ...)`
    query -- never fetch-then-count in Python. Feeds the Contacts page's stat badges,
    which previously derived these from `.length` on a full unbounded `/contacts` fetch
    and silently undercounted for any account over the pagination default (GRX-PERF-001
    review finding). Scoped to non-deleted contacts only, matching what the page's
    default `/contacts` fetch (no `deleted_only`) always returned."""
    suppressed_exists = exists(
        select(SuppressionEntry.id).where(
            SuppressionEntry.account_id == account_id,
            func.lower(SuppressionEntry.email) == func.lower(Contact.email),
        )
    )
    result = await session.execute(
        select(
            func.count().label("total"),
            func.count().filter(Contact.status == "ACTIVE").label("active"),
            func.count().filter(Contact.status == "ARCHIVED").label("archived"),
            func.count()
            .filter(
                func.date_trunc("month", Contact.created_at) == func.date_trunc("month", func.now())
            )
            .label("new_this_month"),
            func.count().filter(suppressed_exists).label("suppressed"),
        )
        .select_from(Contact)
        .where(Contact.account_id == account_id, Contact.deleted_at.is_(None))
    )
    row = result.one()
    return {
        "total": row.total,
        "active": row.active,
        "archived": row.archived,
        "new_this_month": row.new_this_month,
        "suppressed": row.suppressed,
    }


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


async def restore_contact(
    session: AsyncSession, account_id: uuid.UUID, contact_id: uuid.UUID
) -> bool:
    """Restores a single soft-deleted contact by clearing deleted_at."""
    result = await session.execute(
        update(Contact)
        .where(
            Contact.account_id == account_id,
            Contact.id == contact_id,
            Contact.deleted_at.is_not(None),
        )
        .values(deleted_at=None)
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


async def bulk_restore_contacts(
    session: AsyncSession, account_id: uuid.UUID, contact_ids: Sequence[uuid.UUID]
) -> int:
    """Restores multiple soft-deleted contacts belonging to the account by clearing deleted_at."""
    if not contact_ids:
        return 0
    result = await session.execute(
        update(Contact)
        .where(
            Contact.account_id == account_id,
            Contact.id.in_(contact_ids),
            Contact.deleted_at.is_not(None),
        )
        .values(deleted_at=None)
    )
    await session.flush()
    return int(cast(CursorResult[Any], result).rowcount)


async def get_deleted_contacts_by_ids(
    session: AsyncSession, account_id: uuid.UUID, contact_ids: Sequence[uuid.UUID]
) -> Sequence[Contact]:
    """Fetches soft-deleted contacts for the given account."""
    if not contact_ids:
        return []
    result = await session.execute(
        select(Contact).where(
            Contact.account_id == account_id,
            Contact.id.in_(contact_ids),
            Contact.deleted_at.is_not(None),
        )
    )
    return result.scalars().all()


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
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    key: str,
    label: str,
    field_type: str,
    is_personalization_usable: bool = True,
) -> ContactCustomField:
    field = ContactCustomField(
        account_id=account_id,
        key=key,
        label=label,
        field_type=field_type,
        is_personalization_usable=is_personalization_usable,
    )
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


async def get_all_field_values_for_account(
    session: AsyncSession, account_id: uuid.UUID
) -> dict[uuid.UUID, dict[str, str]]:
    result = await session.execute(
        select(ContactFieldValue.contact_id, ContactCustomField.key, ContactFieldValue.value)
        .join(ContactCustomField, ContactCustomField.id == ContactFieldValue.field_id)
        .where(ContactFieldValue.account_id == account_id)
    )
    out: dict[uuid.UUID, dict[str, str]] = {}
    for contact_id, key, value in result.all():
        if value is not None:
            if contact_id not in out:
                out[contact_id] = {}
            out[contact_id][key] = value
    return out


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


async def get_all_tag_names_for_account(
    session: AsyncSession, account_id: uuid.UUID
) -> dict[uuid.UUID, list[str]]:
    result = await session.execute(
        select(ContactTag.contact_id, Tag.name)
        .join(Tag, Tag.id == ContactTag.tag_id)
        .where(ContactTag.account_id == account_id)
    )
    out: dict[uuid.UUID, list[str]] = {}
    for contact_id, tag_name in result.all():
        if contact_id not in out:
            out[contact_id] = []
        out[contact_id].append(tag_name)
    return out


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


async def get_all_list_member_counts_for_account(
    session: AsyncSession, account_id: uuid.UUID
) -> dict[uuid.UUID, int]:
    result = await session.execute(
        select(ContactListMember.list_id, func.count(ContactListMember.contact_id))
        .join(Contact, Contact.id == ContactListMember.contact_id)
        .where(
            ContactListMember.account_id == account_id,
            Contact.deleted_at.is_(None),
        )
        .group_by(ContactListMember.list_id)
    )
    return {row[0]: row[1] for row in result.all()}


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


async def list_members_for_contact_list(
    session: AsyncSession, *, account_id: uuid.UUID, list_id: uuid.UUID
) -> Sequence[Contact]:
    result = await session.execute(
        select(Contact)
        .join(ContactListMember, ContactListMember.contact_id == Contact.id)
        .where(
            ContactListMember.account_id == account_id,
            ContactListMember.list_id == list_id,
            Contact.deleted_at.is_(None),
        )
        .order_by(Contact.created_at.desc())
    )
    return result.scalars().all()


def _build_text_op(column: Any, operator: str, value: str) -> ColumnElement[bool]:
    op = operator.lower()
    if op == SegmentRuleOperator.EQUALS:
        return column == value
    if op == SegmentRuleOperator.NOT_EQUALS:
        return or_(column != value, column.is_(None))
    if op == SegmentRuleOperator.CONTAINS:
        return column.ilike(f"%{value}%")
    if op == SegmentRuleOperator.STARTS_WITH:
        return column.ilike(f"{value}%")
    if op == SegmentRuleOperator.ENDS_WITH:
        return column.ilike(f"%{value}")
    if op == SegmentRuleOperator.IS_EMPTY:
        return or_(column.is_(None), column == "")
    if op == SegmentRuleOperator.IS_NOT_EMPTY:
        return and_(column.is_not(None), column != "")
    return column == value


def build_rule_condition(field: str, operator: str, value: str) -> ColumnElement[bool]:
    """Translate one validated (field, operator, value) triple into a SQLAlchemy
    boolean expression over `Contact`."""
    if field == SegmentRuleField.STATUS:
        return _build_text_op(Contact.status, operator, value)
    if field == SegmentRuleField.EMAIL:
        return _build_text_op(Contact.email, operator, value)
    if field == SegmentRuleField.FIRST_NAME:
        return _build_text_op(Contact.first_name, operator, value)
    if field == SegmentRuleField.LAST_NAME:
        return _build_text_op(Contact.last_name, operator, value)
    if field == SegmentRuleField.PHONE:
        return _build_text_op(Contact.phone, operator, value)
    if field == SegmentRuleField.SOURCE:
        return _build_text_op(Contact.source, operator, value)
    if field == SegmentRuleField.LIFECYCLE_STAGE:
        return _build_text_op(Contact.lifecycle_stage, operator, value)
    if field == SegmentRuleField.JOB_TITLE:
        return _build_text_op(Contact.job_title, operator, value)
    if field == SegmentRuleField.COMPANY:
        company_subquery = select(CRMCompany.id).where(
            _build_text_op(CRMCompany.name, operator, value),
            CRMCompany.deleted_at.is_(None),
        )
        return Contact.company_id.in_(company_subquery)
    if field == SegmentRuleField.TAG:
        op = operator.lower()
        if op == SegmentRuleOperator.HAS_NOT_TAG:
            return Contact.id.not_in(
                select(ContactTag.contact_id)
                .join(Tag, Tag.id == ContactTag.tag_id)
                .where(Tag.name == value)
            )
        tag_condition = (
            Tag.name.ilike(f"%{value}%")
            if op == SegmentRuleOperator.CONTAINS
            else Tag.name == value
        )
        return Contact.id.in_(
            select(ContactTag.contact_id)
            .join(Tag, Tag.id == ContactTag.tag_id)
            .where(tag_condition)
        )
    if field == SegmentRuleField.CREATED_AT:
        op = operator.lower()
        if op == SegmentRuleOperator.WITHIN_DAYS:
            try:
                days = int(value)
            except ValueError:
                days = 30
            return Contact.created_at >= func.now() - text(f"INTERVAL '{days} days'")
        parsed = datetime.fromisoformat(value)
        return (
            Contact.created_at < parsed
            if op == SegmentRuleOperator.BEFORE
            else Contact.created_at > parsed
        )

    if field.startswith("custom_field:"):
        key = field.split(":", 1)[1]
        subquery = (
            select(ContactFieldValue.contact_id)
            .join(ContactCustomField, ContactCustomField.id == ContactFieldValue.field_id)
            .where(ContactCustomField.key == key)
        )
        subquery = subquery.where(_build_text_op(ContactFieldValue.value, operator, value))
        return Contact.id.in_(subquery)

    raise ValueError(f"Unsupported segment rule field: {field}")


def _matching_contacts_query(
    account_id: uuid.UUID, rules: Sequence[Any], match_type: str = "ALL"
) -> Select[tuple[Contact]]:
    conditions = [build_rule_condition(r.field, r.operator, r.value) for r in rules]
    query = select(Contact).where(
        Contact.account_id == account_id,
        Contact.deleted_at.is_(None),
    )
    if conditions:
        combined = and_(*conditions) if match_type.upper() == "ALL" else or_(*conditions)
        query = query.where(combined)
    return query


async def evaluate_segment_rules(
    session: AsyncSession, account_id: uuid.UUID, rules: Sequence[Any], match_type: str = "ALL"
) -> Sequence[Contact]:
    result = await session.execute(_matching_contacts_query(account_id, rules, match_type))
    return result.scalars().all()


async def count_dynamic_segment_members(
    session: AsyncSession, account_id: uuid.UUID, rules: Sequence[Any], match_type: str = "ALL"
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
        combined = and_(*conditions) if match_type.upper() == "ALL" else or_(*conditions)
        query = query.where(combined)
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


async def list_active_campaigns_referencing_segment(
    session: AsyncSession, account_id: uuid.UUID, segment_id: uuid.UUID
) -> Sequence[Campaign]:
    """Returns any active/scheduled/dispatching/draft campaigns referencing this segment."""
    result = await session.execute(
        select(Campaign).where(
            Campaign.account_id == account_id,
            Campaign.recipient_segment_id == segment_id,
            Campaign.status.in_(["DRAFT", "SCHEDULED", "DISPATCHING", "SENDING"]),
        )
    )
    return result.scalars().all()


async def unlink_historical_campaigns_referencing_segment(
    session: AsyncSession, account_id: uuid.UUID, segment_id: uuid.UUID
) -> None:
    """Unlinks historical/completed campaigns (SENT, CANCELLED, FAILED) by setting
    recipient_segment_id = NULL."""
    await session.execute(
        update(Campaign)
        .where(
            Campaign.account_id == account_id,
            Campaign.recipient_segment_id == segment_id,
        )
        .values(recipient_segment_id=None)
    )


async def delete_segment_row(
    session: AsyncSession, account_id: uuid.UUID, segment_id: uuid.UUID
) -> None:
    """Deletes segment, its rules, and saved members."""
    await session.execute(
        delete(SegmentRule).where(
            SegmentRule.account_id == account_id,
            SegmentRule.segment_id == segment_id,
        )
    )
    await session.execute(
        delete(SegmentMember).where(
            SegmentMember.account_id == account_id,
            SegmentMember.segment_id == segment_id,
        )
    )
    await session.execute(
        delete(Segment).where(
            Segment.account_id == account_id,
            Segment.id == segment_id,
        )
    )


async def update_segment_row(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    segment_id: uuid.UUID,
    name: str,
    type_: str,
) -> Segment | None:
    segment = await get_segment_by_id(session, account_id, segment_id)
    if segment is None:
        return None
    segment.name = name
    segment.type = type_
    await session.flush()
    return segment


async def replace_segment_rules(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    segment_id: uuid.UUID,
    rules: Sequence[tuple[str, str, str]],
) -> Sequence[SegmentRule]:
    await session.execute(
        delete(SegmentRule).where(
            SegmentRule.account_id == account_id,
            SegmentRule.segment_id == segment_id,
        )
    )
    new_rules = [
        SegmentRule(
            account_id=account_id,
            segment_id=segment_id,
            field=f,
            operator=o,
            value=v,
        )
        for f, o, v in rules
    ]
    session.add_all(new_rules)
    await session.flush()
    return new_rules


async def refresh_saved_segment_members(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    segment_id: uuid.UUID,
    rules: Sequence[SegmentRule],
) -> int:
    await session.execute(
        delete(SegmentMember).where(
            SegmentMember.account_id == account_id,
            SegmentMember.segment_id == segment_id,
        )
    )
    matching_contacts = await evaluate_segment_rules(session, account_id, rules)
    if matching_contacts:
        await add_segment_members(
            session,
            account_id=account_id,
            segment_id=segment_id,
            contact_ids=[c.id for c in matching_contacts],
        )
    return len(matching_contacts)


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


async def get_all_suppressed_emails_for_account(
    session: AsyncSession, account_id: uuid.UUID
) -> set[str]:
    result = await session.execute(
        select(SuppressionEntry.email).where(SuppressionEntry.account_id == account_id)
    )
    return {email.lower() for email in result.scalars().all() if email is not None}


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


# ---------------------------------------------------------------------------
# CRM Companies Repositories
# ---------------------------------------------------------------------------


async def get_company_by_id(
    session: AsyncSession, account_id: uuid.UUID, company_id: uuid.UUID
) -> CRMCompany | None:
    result = await session.execute(
        select(CRMCompany).where(
            CRMCompany.account_id == account_id,
            CRMCompany.id == company_id,
            CRMCompany.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_company_by_domain(
    session: AsyncSession, account_id: uuid.UUID, domain: str
) -> CRMCompany | None:
    result = await session.execute(
        select(CRMCompany).where(
            CRMCompany.account_id == account_id,
            CRMCompany.domain == domain,
            CRMCompany.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_company(session: AsyncSession, **fields: Any) -> CRMCompany:
    company = CRMCompany(**fields)
    session.add(company)
    await session.flush()
    return company


async def apply_company_fields(company: CRMCompany, fields: dict[str, Any]) -> CRMCompany:
    for key, value in fields.items():
        setattr(company, key, value)
    return company


async def soft_delete_company(
    session: AsyncSession, account_id: uuid.UUID, company_id: uuid.UUID
) -> bool:
    result = await session.execute(
        update(CRMCompany)
        .where(
            CRMCompany.account_id == account_id,
            CRMCompany.id == company_id,
            CRMCompany.deleted_at.is_(None),
        )
        .values(deleted_at=func.now())
    )
    await session.flush()
    return int(cast(CursorResult[Any], result).rowcount) > 0


def _company_filter_conditions(
    account_id: uuid.UUID,
    search: str | None = None,
    lifecycle_stage: str | None = None,
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = [
        CRMCompany.account_id == account_id,
        CRMCompany.deleted_at.is_(None),
    ]
    if lifecycle_stage:
        conditions.append(CRMCompany.lifecycle_stage == lifecycle_stage)
    if search:
        like = f"%{search}%"
        conditions.append(
            or_(
                CRMCompany.name.ilike(like),
                CRMCompany.domain.ilike(like),
                CRMCompany.industry.ilike(like),
            )
        )
    return conditions


async def list_companies(
    session: AsyncSession,
    account_id: uuid.UUID,
    *,
    search: str | None = None,
    lifecycle_stage: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Sequence[CRMCompany]:
    conditions = _company_filter_conditions(account_id, search, lifecycle_stage)
    query = (
        select(CRMCompany)
        .where(*conditions)
        .order_by(CRMCompany.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(query)
    return result.scalars().all()


async def count_companies(
    session: AsyncSession,
    account_id: uuid.UUID,
    *,
    search: str | None = None,
    lifecycle_stage: str | None = None,
) -> int:
    conditions = _company_filter_conditions(account_id, search, lifecycle_stage)
    result = await session.execute(select(func.count()).select_from(CRMCompany).where(*conditions))
    return result.scalar_one()


async def get_company_contact_count(
    session: AsyncSession, account_id: uuid.UUID, company_id: uuid.UUID
) -> int:
    result = await session.execute(
        select(func.count(Contact.id)).where(
            Contact.account_id == account_id,
            Contact.company_id == company_id,
            Contact.deleted_at.is_(None),
        )
    )
    return result.scalar_one()


async def get_all_company_contact_counts(
    session: AsyncSession,
    account_id: uuid.UUID,
    company_ids: Sequence[uuid.UUID] | None = None,
) -> dict[uuid.UUID, int]:
    query = select(Contact.company_id, func.count(Contact.id)).where(
        Contact.account_id == account_id,
        Contact.company_id.is_not(None),
        Contact.deleted_at.is_(None),
    )
    if company_ids is not None:
        if not company_ids:
            return {}
        query = query.where(Contact.company_id.in_(company_ids))
    result = await session.execute(query.group_by(Contact.company_id))
    return {row[0]: row[1] for row in result.all() if row[0] is not None}


async def get_company_names_by_ids(
    session: AsyncSession, account_id: uuid.UUID, company_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, str]:
    if not company_ids:
        return {}
    result = await session.execute(
        select(CRMCompany.id, CRMCompany.name).where(
            CRMCompany.account_id == account_id,
            CRMCompany.id.in_(company_ids),
        )
    )
    return {row[0]: row[1] for row in result.all()}


# ---------------------------------------------------------------------------
# Contact Activities Repositories
# ---------------------------------------------------------------------------


async def create_contact_activity(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    contact_id: uuid.UUID,
    activity_type: str,
    title: str,
    description: str | None = None,
    metadata_: dict | None = None,
    user_id: uuid.UUID | None = None,
) -> ContactActivity:
    activity = ContactActivity(
        account_id=account_id,
        contact_id=contact_id,
        activity_type=activity_type,
        title=title,
        description=description,
        metadata_=metadata_ or {},
        created_by_user_id=user_id,
    )
    session.add(activity)
    await session.flush()
    return activity


async def list_contact_activities(
    session: AsyncSession,
    account_id: uuid.UUID,
    contact_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[ContactActivity]:
    result = await session.execute(
        select(ContactActivity)
        .where(
            ContactActivity.account_id == account_id,
            ContactActivity.contact_id == contact_id,
        )
        .order_by(ContactActivity.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def count_contact_activities(
    session: AsyncSession, account_id: uuid.UUID, contact_id: uuid.UUID
) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(ContactActivity)
        .where(
            ContactActivity.account_id == account_id,
            ContactActivity.contact_id == contact_id,
        )
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Tag Management Repositories
# ---------------------------------------------------------------------------


async def update_tag_name(
    session: AsyncSession, account_id: uuid.UUID, tag_id: uuid.UUID, new_name: str
) -> Tag | None:
    tag = await get_tag_by_id(session, account_id, tag_id)
    if tag is None:
        return None
    tag.name = new_name
    await session.flush()
    return tag


async def delete_tag_and_associations(
    session: AsyncSession, account_id: uuid.UUID, tag_id: uuid.UUID
) -> bool:
    tag = await get_tag_by_id(session, account_id, tag_id)
    if tag is None:
        return False
    await session.delete(tag)
    await session.flush()
    return True


async def bulk_attach_tag_to_contacts(
    session: AsyncSession,
    account_id: uuid.UUID,
    contact_ids: Sequence[uuid.UUID],
    tag_id: uuid.UUID,
) -> int:
    if not contact_ids:
        return 0
    existing_result = await session.execute(
        select(ContactTag.contact_id).where(
            ContactTag.account_id == account_id,
            ContactTag.contact_id.in_(contact_ids),
            ContactTag.tag_id == tag_id,
        )
    )
    already_attached = set(existing_result.scalars().all())
    count = 0
    for cid in contact_ids:
        if cid not in already_attached:
            session.add(ContactTag(account_id=account_id, contact_id=cid, tag_id=tag_id))
            count += 1
    await session.flush()
    return count


async def bulk_detach_tag_from_contacts(
    session: AsyncSession,
    account_id: uuid.UUID,
    contact_ids: Sequence[uuid.UUID],
    tag_id: uuid.UUID,
) -> int:
    if not contact_ids:
        return 0
    result = await session.execute(
        delete(ContactTag).where(
            ContactTag.account_id == account_id,
            ContactTag.contact_id.in_(contact_ids),
            ContactTag.tag_id == tag_id,
        )
    )
    await session.flush()
    return int(cast(CursorResult[Any], result).rowcount)


async def get_all_tag_contact_counts(
    session: AsyncSession, account_id: uuid.UUID
) -> dict[uuid.UUID, int]:
    result = await session.execute(
        select(ContactTag.tag_id, func.count(ContactTag.contact_id))
        .join(Contact, Contact.id == ContactTag.contact_id)
        .where(
            ContactTag.account_id == account_id,
            Contact.deleted_at.is_(None),
        )
        .group_by(ContactTag.tag_id)
    )
    return {row[0]: row[1] for row in result.all()}


# ---------------------------------------------------------------------------
# Phone Suppression Repositories
# ---------------------------------------------------------------------------


async def get_suppression_by_phone(
    session: AsyncSession, account_id: uuid.UUID, phone: str
) -> SuppressionEntry | None:
    result = await session.execute(
        select(SuppressionEntry).where(
            SuppressionEntry.account_id == account_id,
            SuppressionEntry.phone == phone,
        )
    )
    return result.scalar_one_or_none()


async def is_phone_suppressed(
    session: AsyncSession, account_id: uuid.UUID, phone: str | None
) -> bool:
    if not phone:
        return False
    entry = await get_suppression_by_phone(session, account_id, phone)
    return entry is not None


async def create_phone_suppression_entry(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    phone: str,
    reason: str = "MANUAL",
    suppressed_by_user_id: uuid.UUID | None = None,
) -> SuppressionEntry:
    entry = SuppressionEntry(
        account_id=account_id,
        phone=phone,
        reason=reason,
        suppressed_by_user_id=suppressed_by_user_id,
    )
    session.add(entry)
    await session.flush()
    return entry


# ---------------------------------------------------------------------------
# Segment Frozen Snapshot
# ---------------------------------------------------------------------------


async def snapshot_segment_members(
    session: AsyncSession, account_id: uuid.UUID, segment_id: uuid.UUID
) -> int:
    segment = await get_segment_by_id(session, account_id, segment_id)
    if segment is None:
        return 0
    rules = await list_segment_rules(session, segment_id)
    matching = await evaluate_segment_rules(
        session, account_id, rules, getattr(segment, "match_type", "ALL")
    )
    await refresh_saved_segment_members(
        session,
        account_id=account_id,
        segment_id=segment_id,
        rules=rules,
    )
    return len(matching)
