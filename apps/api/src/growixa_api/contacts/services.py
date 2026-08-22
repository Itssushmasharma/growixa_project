import csv
import io
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.services import record_event
from growixa_api.billing.services import check_plan_limit
from growixa_api.contacts.constants import (
    CUSTOM_FIELD_RULE_OPERATORS,
    SEGMENT_RULE_FIELD_OPERATORS,
)
from growixa_api.contacts.models import (
    ConsentRecord,
    Contact,
    ContactCustomField,
    ContactImport,
    ContactImportRow,
    ContactList,
    Segment,
    SegmentRule,
    SuppressionEntry,
    Tag,
)
from growixa_api.contacts.repositories import (
    add_import_row,
    add_list_member,
    add_segment_members,
    apply_contact_fields,
    attach_tag,
    bulk_soft_delete_contacts,
    count_active_contacts,
    count_dynamic_segment_members,
    count_list_members,
    count_saved_segment_members,
    create_contact,
    delete_segment_row,
    detach_tag,
    evaluate_segment_rules,
    get_all_field_values_for_account,
    get_all_list_member_counts_for_account,
    get_all_suppressed_emails_for_account,
    get_all_tag_names_for_account,
    get_contact_by_email,
    get_contact_by_id,
    get_contact_by_id_including_deleted,
    get_contact_list_by_id,
    get_custom_field_by_key,
    get_deleted_contacts_by_ids,
    get_import_by_id,
    get_segment_by_id,
    get_suppression_by_domain,
    get_suppression_by_email,
    get_suppression_entry_by_id,
    get_tag_by_id,
    get_tag_by_name,
    get_tag_names_for_contact,
    is_email_suppressed,
    list_active_campaigns_referencing_segment,
    list_consent_records,
    list_import_rows,
    list_imports,
    list_members_for_contact_list,
    list_saved_segment_members,
    list_segment_rules,
    list_suppression_entries,
    purge_all_contacts_in_account,
    refresh_saved_segment_members,
    remove_list_member,
    replace_segment_rules,
    soft_delete_contact,
    unlink_historical_campaigns_referencing_segment,
    update_segment_row,
    upsert_field_value,
)
from growixa_api.contacts.repositories import add_segment_rule as add_segment_rule_row
from growixa_api.contacts.repositories import (
    bulk_restore_contacts as bulk_restore_contacts_rows,
)
from growixa_api.contacts.repositories import create_consent_record as create_consent_record_row
from growixa_api.contacts.repositories import create_contact_list as create_contact_list_row
from growixa_api.contacts.repositories import create_custom_field as create_custom_field_row
from growixa_api.contacts.repositories import (
    create_domain_suppression_entry as create_domain_suppression_entry_row,
)
from growixa_api.contacts.repositories import create_import as create_import_row
from growixa_api.contacts.repositories import create_segment as create_segment_row
from growixa_api.contacts.repositories import (
    create_suppression_entry as create_suppression_entry_row,
)
from growixa_api.contacts.repositories import create_tag as create_tag_row
from growixa_api.contacts.repositories import (
    delete_suppression_entry as delete_suppression_entry_row,
)
from growixa_api.contacts.repositories import get_field_values_for_contact as _get_field_values
from growixa_api.contacts.repositories import list_contact_lists as list_contact_lists_rows
from growixa_api.contacts.repositories import list_contacts as list_contacts_rows
from growixa_api.contacts.repositories import list_custom_fields as list_custom_fields_rows
from growixa_api.contacts.repositories import list_segments as list_segments_rows
from growixa_api.contacts.repositories import list_tags as list_tags_rows
from growixa_api.contacts.repositories import (
    restore_contact as restore_contact_row,
)

ContactSnapshot = tuple[Contact, dict[str, str], list[str], bool]
SegmentDetail = tuple[Segment, Sequence[SegmentRule], int]

# Column-mapping target fields a CSV header may be mapped to, beyond `custom_field:<key>`.
CONTACT_IMPORT_FIELD_TARGETS = {"email", "first_name", "last_name", "phone", "source"}


class DuplicateEmailError(Exception):
    pass


class DuplicateFieldKeyError(Exception):
    pass


class DuplicateTagNameError(Exception):
    pass


class ContactNotFoundError(Exception):
    pass


class TagNotFoundError(Exception):
    pass


class ContactListNotFoundError(Exception):
    pass


class SegmentNotFoundError(Exception):
    pass


class SegmentInUseByActiveCampaignsError(Exception):
    def __init__(self, campaign_details: Sequence[str]) -> None:
        self.campaign_details = campaign_details
        joined = ", ".join(campaign_details)
        super().__init__(
            f"Cannot delete segment because it is targeted by active campaigns: {joined}"
        )


class InvalidSegmentRuleError(Exception):
    pass


class InvalidColumnMappingError(Exception):
    pass


class ContactImportNotFoundError(Exception):
    pass


class SuppressionEntryNotFoundError(Exception):
    pass


class UnknownCustomFieldError(Exception):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Unknown custom field key: {key}")


async def _apply_custom_fields(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    contact_id: uuid.UUID,
    custom_fields: dict[str, str],
) -> None:
    for key, value in custom_fields.items():
        field = await get_custom_field_by_key(session, account_id, key)
        if field is None:
            raise UnknownCustomFieldError(key)
        await upsert_field_value(
            session, account_id=account_id, contact_id=contact_id, field_id=field.id, value=value
        )


async def _snapshot(
    session: AsyncSession, account_id: uuid.UUID, contact: Contact
) -> ContactSnapshot:
    field_values = await _get_field_values(session, contact.id)
    tags = await get_tag_names_for_contact(session, contact.id)
    suppressed = await is_email_suppressed(session, account_id, contact.email)
    return contact, field_values, tags, suppressed


async def create_or_update_contact(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    email: str,
    first_name: str | None,
    last_name: str | None,
    phone: str | None,
    source: str | None,
    custom_fields: dict[str, str],
) -> ContactSnapshot:
    """Create a contact, or update it in place if the email already exists.

    Email is the sole dedup key in Slice 2 (no fuzzy/name-based matching), scoped per
    account since GRX-SAAS-001 — see DATA_MODEL.md §Slice 2 entities.
    """
    existing = await get_contact_by_email(session, account_id, email)
    if existing is None:
        current_count = await count_active_contacts(session, account_id)
        await check_plan_limit(
            session,
            account_id=account_id,
            limit_attr="max_contacts",
            current_count=current_count,
            resource="contacts",
        )
        contact = await create_contact(
            session,
            account_id=account_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            source=source,
            created_by_user_id=actor_id,
        )
        action = "contact.created"
    else:
        contact = await apply_contact_fields(
            existing,
            {"first_name": first_name, "last_name": last_name, "phone": phone, "source": source},
        )
        action = "contact.updated"

    await _apply_custom_fields(
        session, account_id=account_id, contact_id=contact.id, custom_fields=custom_fields
    )
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action=action,
        entity_type="contact",
        entity_id=contact.id,
    )
    await session.commit()
    # `updated_at`'s server-side onupdate expires the attribute after an UPDATE commit;
    # a synchronous read of it afterward (e.g. in the API layer's response model) would
    # trigger an un-awaited lazy reload and raise MissingGreenlet. Refresh explicitly
    # while still inside an awaited call.
    await session.refresh(contact)

    return await _snapshot(session, account_id, contact)


async def update_contact(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    contact_id: uuid.UUID,
    email: str | None,
    first_name: str | None,
    last_name: str | None,
    phone: str | None,
    custom_fields: dict[str, str] | None,
    audit_metadata: dict[str, object] | None = None,
) -> ContactSnapshot:
    """actor_id is Optional and audit_metadata exists for GRX-SAAS-010: a platform admin
    editing a contact through a support session has no users.id to record as the actor
    (DEC-GRX-022 point 4) -- it passes actor_id=None and its own identity in
    audit_metadata instead, the same actor_user_id=None + metadata pattern DEC-GRX-020
    established. Ordinary customer callers are unaffected -- they keep passing a real
    actor_id and audit_metadata defaults to None."""
    contact = await get_contact_by_id(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError

    fields: dict[str, object] = {}
    if email is not None and email != contact.email:
        other = await get_contact_by_email(session, account_id, email)
        if other is not None and other.id != contact.id:
            raise DuplicateEmailError
        fields["email"] = email
    if first_name is not None:
        fields["first_name"] = first_name
    if last_name is not None:
        fields["last_name"] = last_name
    if phone is not None:
        fields["phone"] = phone

    await apply_contact_fields(contact, fields)
    if custom_fields:
        await _apply_custom_fields(
            session, account_id=account_id, contact_id=contact.id, custom_fields=custom_fields
        )

    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.updated",
        entity_type="contact",
        entity_id=contact.id,
        metadata=audit_metadata,
    )
    await session.commit()
    await session.refresh(contact)

    return await _snapshot(session, account_id, contact)


async def update_contact_status(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    contact_id: uuid.UUID,
    status: str,
) -> ContactSnapshot:
    contact = await get_contact_by_id(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError

    old_status = contact.status
    await apply_contact_fields(contact, {"status": status})

    action = "contact.archived" if status == "ARCHIVED" else "contact.updated"
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action=action,
        entity_type="contact",
        entity_id=contact.id,
        metadata={"old_status": old_status, "new_status": status},
    )
    await session.commit()
    await session.refresh(contact)

    return await _snapshot(session, account_id, contact)


async def get_contact_with_fields(
    session: AsyncSession, account_id: uuid.UUID, contact_id: uuid.UUID
) -> ContactSnapshot:
    contact = await get_contact_by_id(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError
    return await _snapshot(session, account_id, contact)


async def list_contacts_with_fields(
    session: AsyncSession,
    account_id: uuid.UUID,
    *,
    include_deleted: bool = False,
    deleted_only: bool = False,
) -> list[ContactSnapshot]:
    contacts = await list_contacts_rows(
        session, account_id, include_deleted=include_deleted, deleted_only=deleted_only
    )
    if not contacts:
        return []

    field_values_map = await get_all_field_values_for_account(session, account_id)
    tags_map = await get_all_tag_names_for_account(session, account_id)
    suppressed_emails = await get_all_suppressed_emails_for_account(session, account_id)

    return [
        (
            contact,
            field_values_map.get(contact.id, {}),
            tags_map.get(contact.id, []),
            contact.email.lower() in suppressed_emails,
        )
        for contact in contacts
    ]


async def list_custom_fields(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[ContactCustomField]:
    return await list_custom_fields_rows(session, account_id)


async def create_custom_field(
    session: AsyncSession, *, account_id: uuid.UUID, key: str, label: str, field_type: str
) -> ContactCustomField:
    existing = await get_custom_field_by_key(session, account_id, key)
    if existing is not None:
        raise DuplicateFieldKeyError
    field = await create_custom_field_row(
        session, account_id=account_id, key=key, label=label, field_type=field_type
    )
    await session.commit()
    return field


async def list_tags(session: AsyncSession, account_id: uuid.UUID) -> Sequence[Tag]:
    return await list_tags_rows(session, account_id)


async def create_tag(session: AsyncSession, *, account_id: uuid.UUID, name: str) -> Tag:
    existing = await get_tag_by_name(session, account_id, name)
    if existing is not None:
        raise DuplicateTagNameError
    tag = await create_tag_row(session, account_id=account_id, name=name)
    await session.commit()
    return tag


async def attach_tag_to_contact(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    contact_id: uuid.UUID,
    tag_id: uuid.UUID,
) -> ContactSnapshot:
    contact = await get_contact_by_id(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError
    tag = await get_tag_by_id(session, account_id, tag_id)
    if tag is None:
        raise TagNotFoundError

    await attach_tag(session, account_id=account_id, contact_id=contact_id, tag_id=tag_id)
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.tagged",
        entity_type="contact",
        entity_id=contact_id,
        metadata={"tag": tag.name},
    )
    await session.commit()

    return await _snapshot(session, account_id, contact)


async def detach_tag_from_contact(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    contact_id: uuid.UUID,
    tag_id: uuid.UUID,
) -> ContactSnapshot:
    contact = await get_contact_by_id(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError
    tag = await get_tag_by_id(session, account_id, tag_id)
    if tag is None:
        raise TagNotFoundError

    await detach_tag(session, contact_id=contact_id, tag_id=tag_id)
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.tagged",
        entity_type="contact",
        entity_id=contact_id,
        metadata={"untagged": tag.name},
    )
    await session.commit()

    return await _snapshot(session, account_id, contact)


async def list_lists_with_counts(
    session: AsyncSession, account_id: uuid.UUID
) -> list[tuple[ContactList, int]]:
    lists = await list_contact_lists_rows(session, account_id)
    if not lists:
        return []
    counts_map = await get_all_list_member_counts_for_account(session, account_id)
    return [(cl, counts_map.get(cl.id, 0)) for cl in lists]


async def get_list_with_count(
    session: AsyncSession, account_id: uuid.UUID, list_id: uuid.UUID
) -> tuple[ContactList, int]:
    contact_list = await get_contact_list_by_id(session, account_id, list_id)
    if contact_list is None:
        raise ContactListNotFoundError
    count = await count_list_members(session, list_id)
    return contact_list, count


async def list_list_members(
    session: AsyncSession, account_id: uuid.UUID, list_id: uuid.UUID
) -> list[ContactSnapshot]:
    contact_list = await get_contact_list_by_id(session, account_id, list_id)
    if contact_list is None:
        raise ContactListNotFoundError
    contacts = await list_members_for_contact_list(session, account_id=account_id, list_id=list_id)
    return [await _snapshot(session, account_id, contact) for contact in contacts]


async def create_list(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    name: str,
    description: str | None,
) -> tuple[ContactList, int]:
    contact_list = await create_contact_list_row(
        session,
        account_id=account_id,
        name=name,
        description=description,
        created_by_user_id=actor_id,
    )
    await session.commit()
    return contact_list, 0


async def add_contact_to_list(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    list_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> tuple[ContactList, int]:
    contact_list = await get_contact_list_by_id(session, account_id, list_id)
    if contact_list is None:
        raise ContactListNotFoundError
    contact = await get_contact_by_id(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError

    await add_list_member(session, account_id=account_id, list_id=list_id, contact_id=contact_id)
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.list_added",
        entity_type="contact",
        entity_id=contact_id,
        metadata={"list": contact_list.name},
    )
    await session.commit()

    count = await count_list_members(session, list_id)
    return contact_list, count


async def _validate_segment_rule(
    session: AsyncSession, *, account_id: uuid.UUID, field: str, operator: str, value: str
) -> None:
    if field.startswith("custom_field:"):
        key = field.split(":", 1)[1]
        existing = await get_custom_field_by_key(session, account_id, key)
        if existing is None:
            raise InvalidSegmentRuleError(f"Unknown custom field key: {key}")
        allowed = CUSTOM_FIELD_RULE_OPERATORS
    else:
        allowed = SEGMENT_RULE_FIELD_OPERATORS.get(field, set())
        if not allowed:
            raise InvalidSegmentRuleError(f"Unsupported segment rule field: {field}")

    if operator not in allowed:
        raise InvalidSegmentRuleError(f"Unsupported operator '{operator}' for field '{field}'")

    if field == "created_at":
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise InvalidSegmentRuleError(
                f"Invalid ISO-8601 date value for created_at: {value}"
            ) from exc


async def _segment_member_count(
    session: AsyncSession, account_id: uuid.UUID, segment: Segment, rules: Sequence[SegmentRule]
) -> int:
    if segment.type == "SAVED":
        return await count_saved_segment_members(session, segment.id)
    return await count_dynamic_segment_members(session, account_id, rules)


async def create_segment_with_rules(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    name: str,
    type_: str,
    rules: list[tuple[str, str, str]],
) -> SegmentDetail:
    for field, operator, value in rules:
        await _validate_segment_rule(
            session, account_id=account_id, field=field, operator=operator, value=value
        )

    segment = await create_segment_row(
        session, account_id=account_id, name=name, type_=type_, created_by_user_id=actor_id
    )
    rule_rows = [
        await add_segment_rule_row(
            session, account_id=account_id, segment_id=segment.id, field=f, operator=o, value=v
        )
        for f, o, v in rules
    ]

    if type_ == "SAVED":
        matches = await evaluate_segment_rules(session, account_id, rule_rows)
        await add_segment_members(
            session,
            account_id=account_id,
            segment_id=segment.id,
            contact_ids=[c.id for c in matches],
        )

    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="segment.created",
        entity_type="segment",
        entity_id=segment.id,
        metadata={"type": type_, "rule_count": len(rule_rows)},
    )
    await session.commit()

    count = await _segment_member_count(session, account_id, segment, rule_rows)
    return segment, rule_rows, count


async def get_segment_with_details(
    session: AsyncSession, account_id: uuid.UUID, segment_id: uuid.UUID
) -> SegmentDetail:
    segment = await get_segment_by_id(session, account_id, segment_id)
    if segment is None:
        raise SegmentNotFoundError
    rules = await list_segment_rules(session, segment_id)
    count = await _segment_member_count(session, account_id, segment, rules)
    return segment, rules, count


async def list_segments_with_details(
    session: AsyncSession, account_id: uuid.UUID
) -> list[SegmentDetail]:
    segments = await list_segments_rows(session, account_id)
    details = []
    for segment in segments:
        rules = await list_segment_rules(session, segment.id)
        count = await _segment_member_count(session, account_id, segment, rules)
        details.append((segment, rules, count))
    return details


async def list_segment_members(
    session: AsyncSession, account_id: uuid.UUID, segment_id: uuid.UUID
) -> list[ContactSnapshot]:
    segment = await get_segment_by_id(session, account_id, segment_id)
    if segment is None:
        raise SegmentNotFoundError

    if segment.type == "SAVED":
        contacts = await list_saved_segment_members(session, segment_id)
    else:
        rules = await list_segment_rules(session, segment_id)
        contacts = await evaluate_segment_rules(session, account_id, rules)

    return [await _snapshot(session, account_id, contact) for contact in contacts]


async def update_segment_service(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    segment_id: uuid.UUID,
    name: str,
    type_: str,
    rules: Sequence[tuple[str, str, str]],
) -> SegmentDetail:
    segment = await get_segment_by_id(session, account_id, segment_id)
    if segment is None:
        raise SegmentNotFoundError

    for field, operator, value in rules:
        await _validate_segment_rule(
            session, account_id=account_id, field=field, operator=operator, value=value
        )

    updated_segment = await update_segment_row(
        session,
        account_id=account_id,
        segment_id=segment_id,
        name=name,
        type_=type_,
    )
    if updated_segment is None:
        raise SegmentNotFoundError

    new_rules = await replace_segment_rules(
        session,
        account_id=account_id,
        segment_id=segment_id,
        rules=rules,
    )

    if type_ == "SAVED":
        await refresh_saved_segment_members(
            session,
            account_id=account_id,
            segment_id=segment_id,
            rules=new_rules,
        )

    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="segment.updated",
        entity_type="segment",
        entity_id=segment_id,
        metadata={"name": name, "type": type_, "rule_count": len(new_rules)},
    )
    await session.commit()
    await session.refresh(updated_segment)

    count = await _segment_member_count(session, account_id, updated_segment, new_rules)
    return updated_segment, new_rules, count


async def delete_segment_service(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    segment_id: uuid.UUID,
) -> None:
    segment = await get_segment_by_id(session, account_id, segment_id)
    if segment is None:
        raise SegmentNotFoundError

    active_campaigns = await list_active_campaigns_referencing_segment(
        session, account_id, segment_id
    )
    if active_campaigns:
        campaign_details = [f"'{c.name}' ({c.status})" for c in active_campaigns]
        raise SegmentInUseByActiveCampaignsError(campaign_details)

    # Unlink any historical/completed campaigns
    await unlink_historical_campaigns_referencing_segment(session, account_id, segment_id)

    # Delete segment and associated rules / saved members
    await delete_segment_row(session, account_id, segment_id)

    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="segment.deleted",
        entity_type="segment",
        entity_id=segment_id,
        metadata={"name": segment.name},
    )
    await session.commit()


async def remove_contact_from_list(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    list_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> tuple[ContactList, int]:
    contact_list = await get_contact_list_by_id(session, account_id, list_id)
    if contact_list is None:
        raise ContactListNotFoundError
    contact = await get_contact_by_id(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError

    await remove_list_member(session, list_id=list_id, contact_id=contact_id)
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.list_added",
        entity_type="contact",
        entity_id=contact_id,
        metadata={"list_removed": contact_list.name},
    )
    await session.commit()

    count = await count_list_members(session, list_id)
    return contact_list, count


async def _validate_column_mapping(
    session: AsyncSession, account_id: uuid.UUID, column_mapping: dict[str, str]
) -> None:
    if not column_mapping:
        raise InvalidColumnMappingError("column_mapping must not be empty")
    if "email" not in column_mapping.values():
        raise InvalidColumnMappingError("column_mapping must map a column to 'email'")

    for target in column_mapping.values():
        if target in CONTACT_IMPORT_FIELD_TARGETS:
            continue
        if target.startswith("custom_field:"):
            key = target.split(":", 1)[1]
            if await get_custom_field_by_key(session, account_id, key) is None:
                raise InvalidColumnMappingError(f"Unknown custom field key: {key}")
            continue
        raise InvalidColumnMappingError(f"Unsupported column mapping target: {target}")


async def import_contacts_from_csv(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    filename: str,
    csv_text: str,
    column_mapping: dict[str, str],
) -> ContactImport:
    await _validate_column_mapping(session, account_id, column_mapping)

    contact_import = await create_import_row(
        session,
        account_id=account_id,
        filename=filename,
        column_mapping=column_mapping,
        created_by_user_id=actor_id,
    )

    imported = updated = skipped = errored = 0
    reader = csv.DictReader(io.StringIO(csv_text))
    for row_number, raw_row in enumerate(reader, start=1):
        if not any((raw_row.get(header) or "").strip() for header in column_mapping):
            await add_import_row(
                session,
                account_id=account_id,
                import_id=contact_import.id,
                row_number=row_number,
                email=None,
                status="SKIPPED",
                error_message=None,
            )
            skipped += 1
            continue

        fields: dict[str, str] = {}
        custom_fields: dict[str, str] = {}
        for header, target in column_mapping.items():
            value = (raw_row.get(header) or "").strip()
            if not value:
                continue
            if target.startswith("custom_field:"):
                custom_fields[target.split(":", 1)[1]] = value
            else:
                fields[target] = value

        email = fields.get("email")
        if not email:
            await add_import_row(
                session,
                account_id=account_id,
                import_id=contact_import.id,
                row_number=row_number,
                email=None,
                status="ERROR",
                error_message="Missing required email value",
            )
            errored += 1
            continue

        existing = await get_contact_by_email(session, account_id, email)
        try:
            await create_or_update_contact(
                session,
                account_id=account_id,
                actor_id=actor_id,
                email=email,
                first_name=fields.get("first_name"),
                last_name=fields.get("last_name"),
                phone=fields.get("phone"),
                source=fields.get("source"),
                custom_fields=custom_fields,
            )
        except UnknownCustomFieldError as exc:
            await add_import_row(
                session,
                account_id=account_id,
                import_id=contact_import.id,
                row_number=row_number,
                email=email,
                status="ERROR",
                error_message=f"Unknown custom field key: {exc.key}",
            )
            errored += 1
            continue

        if existing is None:
            imported += 1
            row_status = "IMPORTED"
        else:
            updated += 1
            row_status = "UPDATED"
        await add_import_row(
            session,
            account_id=account_id,
            import_id=contact_import.id,
            row_number=row_number,
            email=email,
            status=row_status,
            error_message=None,
        )

    contact_import.total_rows = imported + updated + skipped + errored
    contact_import.imported_count = imported
    contact_import.updated_count = updated
    contact_import.skipped_count = skipped
    contact_import.error_count = errored
    contact_import.status = "COMPLETED"
    contact_import.completed_at = datetime.now(UTC)

    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact_import.completed",
        entity_type="contact_import",
        entity_id=contact_import.id,
        metadata={
            "filename": filename,
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "errors": errored,
        },
    )
    await session.commit()
    await session.refresh(contact_import)

    return contact_import


async def get_import(
    session: AsyncSession, account_id: uuid.UUID, import_id: uuid.UUID
) -> ContactImport:
    contact_import = await get_import_by_id(session, account_id, import_id)
    if contact_import is None:
        raise ContactImportNotFoundError
    return contact_import


async def list_contact_imports(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[ContactImport]:
    return await list_imports(session, account_id)


async def list_contact_import_rows(
    session: AsyncSession, account_id: uuid.UUID, import_id: uuid.UUID
) -> Sequence[ContactImportRow]:
    if await get_import_by_id(session, account_id, import_id) is None:
        raise ContactImportNotFoundError
    return await list_import_rows(session, import_id)


async def record_consent(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    contact_id: uuid.UUID,
    channel: str,
    status: str,
    source: str | None,
) -> ConsentRecord:
    contact = await get_contact_by_id(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError

    record = await create_consent_record_row(
        session,
        account_id=account_id,
        contact_id=contact_id,
        channel=channel,
        status=status,
        source=source,
        recorded_by_user_id=actor_id,
    )
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.consent_changed",
        entity_type="contact",
        entity_id=contact_id,
        metadata={"channel": channel, "status": status},
    )
    await session.commit()

    return record


async def get_consent_history(
    session: AsyncSession, account_id: uuid.UUID, contact_id: uuid.UUID
) -> Sequence[ConsentRecord]:
    if await get_contact_by_id(session, account_id, contact_id) is None:
        raise ContactNotFoundError
    return await list_consent_records(session, contact_id)


async def suppress_email(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    email: str,
    reason: str,
    contact_id: uuid.UUID | None,
) -> SuppressionEntry:
    if contact_id is not None and await get_contact_by_id(session, account_id, contact_id) is None:
        raise ContactNotFoundError

    existing = await get_suppression_by_email(session, account_id, email)
    if existing is None:
        entry = await create_suppression_entry_row(
            session,
            account_id=account_id,
            email=email,
            reason=reason,
            contact_id=contact_id,
            suppressed_by_user_id=actor_id,
        )
    else:
        existing.reason = reason
        existing.suppressed_by_user_id = actor_id
        existing.suppressed_at = datetime.now(UTC)
        if contact_id is not None:
            existing.contact_id = contact_id
        entry = existing

    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.suppressed",
        entity_type="suppression_entry",
        entity_id=entry.id,
        metadata={"email": email, "reason": reason},
    )
    await session.commit()

    return entry


async def list_suppressions(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[SuppressionEntry]:
    return await list_suppression_entries(session, account_id)


async def import_suppressions_from_csv(
    session: AsyncSession, *, account_id: uuid.UUID, actor_id: uuid.UUID, csv_text: str
) -> tuple[int, int, int]:
    """Synchronous bulk import (GRX-SAAS-015 ad hoc pass) -- suppression lists are
    orders of magnitude smaller than full contact imports, so this skips the
    `ContactImport` async-job machinery entirely (`GRX-CONTACT-*`'s row-by-row progress
    tracking exists for lists that can run to 100k+ rows; a suppression list realistically
    tops out far lower) and just parses + inserts inline in one request. Requires a
    header row with a column literally named "email" (case-insensitive) -- no configurable
    column mapping, unlike the full contact importer, since a suppression CSV only ever
    has the one column that matters. Returns (created, skipped_duplicates, total_rows)."""
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise InvalidColumnMappingError

    email_column = next(
        (name for name in reader.fieldnames if name.strip().lower() == "email"), None
    )
    if email_column is None:
        raise InvalidColumnMappingError

    created = 0
    skipped = 0
    total_rows = 0
    for row in reader:
        raw_email = (row.get(email_column) or "").strip()
        if not raw_email:
            continue
        total_rows += 1
        existing = await get_suppression_by_email(session, account_id, raw_email)
        if existing is not None:
            skipped += 1
            continue
        await create_suppression_entry_row(
            session,
            account_id=account_id,
            email=raw_email,
            reason="MANUAL",
            contact_id=None,
            suppressed_by_user_id=actor_id,
        )
        created += 1

    if created > 0:
        await record_event(
            session,
            account_id=account_id,
            actor_user_id=actor_id,
            action="contact.suppression_bulk_imported",
            entity_type="suppression_entry",
            metadata={"created": created, "skipped": skipped, "total_rows": total_rows},
        )
        await session.commit()

    return created, skipped, total_rows


async def suppress_domain(
    session: AsyncSession, *, account_id: uuid.UUID, actor_id: uuid.UUID, domain: str
) -> SuppressionEntry:
    """Blocks every address at `domain` for this account's future sends (e.g.
    `*@competitor.com`) -- checked in the worker's pre-send suppression pass alongside
    exact-email entries, never both matched by the same row (`domain` is always MANUAL,
    there's no automatic whole-domain unsubscribe/bounce event)."""
    normalized = domain.strip().lower()
    existing = await get_suppression_by_domain(session, account_id, normalized)
    if existing is not None:
        return existing

    entry = await create_domain_suppression_entry_row(
        session, account_id=account_id, domain=normalized, suppressed_by_user_id=actor_id
    )
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.domain_suppressed",
        entity_type="suppression_entry",
        entity_id=entry.id,
        metadata={"domain": normalized},
    )
    await session.commit()
    return entry


async def remove_suppression(
    session: AsyncSession, *, account_id: uuid.UUID, actor_id: uuid.UUID, entry_id: uuid.UUID
) -> None:
    entry = await get_suppression_entry_by_id(session, account_id, entry_id)
    if entry is None:
        raise SuppressionEntryNotFoundError

    identifier = entry.email or entry.domain
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.unsuppressed",
        entity_type="suppression_entry",
        entity_id=entry.id,
        metadata={"identifier": identifier, "reason": entry.reason},
    )
    await delete_suppression_entry_row(session, entry)
    await session.commit()


async def delete_contact(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> None:
    """Soft-deletes a single contact (DEC-GRX-034). Enforces account isolation,
    sets deleted_at, and writes an audit event."""
    contact = await get_contact_by_id(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError

    await soft_delete_contact(session, account_id, contact_id)
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.deleted",
        entity_type="contact",
        entity_id=contact.id,
        metadata={"email": contact.email},
    )
    await session.commit()


async def bulk_delete_contacts(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    contact_ids: Sequence[uuid.UUID],
) -> int:
    """Bulk soft-deletes a list of contacts by ID (DEC-GRX-034). Only affects contacts
    belonging to the given account_id that are not already deleted."""
    deleted_count = await bulk_soft_delete_contacts(session, account_id, contact_ids)
    if deleted_count > 0:
        await record_event(
            session,
            account_id=account_id,
            actor_user_id=actor_id,
            action="contact.bulk_deleted",
            entity_type="contact",
            entity_id=None,
            metadata={
                "count": deleted_count,
                "contact_ids": [str(c_id) for c_id in contact_ids],
            },
        )
    await session.commit()
    return deleted_count


async def purge_all_contacts(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> int:
    """Soft-deletes all contacts in an account (audience purge, DEC-GRX-034)."""
    deleted_count = await purge_all_contacts_in_account(session, account_id)
    if deleted_count > 0:
        await record_event(
            session,
            account_id=account_id,
            actor_user_id=actor_id,
            action="contact.purged",
            entity_type="contact",
            entity_id=None,
            metadata={"count": deleted_count},
        )
    await session.commit()
    return deleted_count


async def restore_contact(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> ContactSnapshot:
    """Restores a soft-deleted contact (GRX-CONTACT-016). Enforces plan quota
    if active, prevents duplicate active email conflict, and emits audit event."""
    contact = await get_contact_by_id_including_deleted(session, account_id, contact_id)
    if contact is None:
        raise ContactNotFoundError

    if contact.deleted_at is None:
        return await _snapshot(session, account_id, contact)

    # Check if another active contact exists with the same email in this account
    existing_active = await get_contact_by_email(session, account_id, contact.email)
    if existing_active is not None and existing_active.id != contact.id:
        raise DuplicateEmailError

    # Quota limit check: only active contacts consume max_contacts quota
    if contact.status == "ACTIVE":
        current_count = await count_active_contacts(session, account_id)
        await check_plan_limit(
            session,
            account_id=account_id,
            limit_attr="max_contacts",
            current_count=current_count,
            resource="contacts",
        )

    await restore_contact_row(session, account_id, contact_id)
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="contact.restored",
        entity_type="contact",
        entity_id=contact.id,
        metadata={"email": contact.email},
    )
    await session.commit()
    await session.refresh(contact)
    return await _snapshot(session, account_id, contact)


async def bulk_restore_contacts(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    contact_ids: Sequence[uuid.UUID],
) -> int:
    """Bulk restores soft-deleted contacts by ID (GRX-CONTACT-016). Enforces plan
    quota for any active contacts, prevents duplicate email conflicts, and emits audit event."""
    deleted_contacts = await get_deleted_contacts_by_ids(session, account_id, contact_ids)
    if not deleted_contacts:
        return 0

    # Check duplicate active emails
    for contact in deleted_contacts:
        existing_active = await get_contact_by_email(session, account_id, contact.email)
        if existing_active is not None and existing_active.id != contact.id:
            raise DuplicateEmailError

    # Count how many are status == "ACTIVE" to check plan quota
    active_count = sum(1 for c in deleted_contacts if c.status == "ACTIVE")
    if active_count > 0:
        current_count = await count_active_contacts(session, account_id)
        await check_plan_limit(
            session,
            account_id=account_id,
            limit_attr="max_contacts",
            current_count=current_count + active_count - 1,
            resource="contacts",
        )

    target_ids = [c.id for c in deleted_contacts]
    restored_count = await bulk_restore_contacts_rows(session, account_id, target_ids)
    if restored_count > 0:
        await record_event(
            session,
            account_id=account_id,
            actor_user_id=actor_id,
            action="contact.bulk_restored",
            entity_type="contact",
            entity_id=None,
            metadata={
                "count": restored_count,
                "contact_ids": [str(c_id) for c_id in target_ids],
            },
        )
    await session.commit()
    return restored_count
