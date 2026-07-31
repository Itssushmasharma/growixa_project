import csv
import io
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.services import record_event
from growixa_api.contacts.models import (
    Contact,
    ContactCustomField,
    ContactImport,
    ContactImportRow,
    ContactList,
    Segment,
    SegmentRule,
    Tag,
)
from growixa_api.contacts.repositories import (
    CUSTOM_FIELD_RULE_OPERATORS,
    SEGMENT_RULE_FIELD_OPERATORS,
    add_import_row,
    add_list_member,
    add_segment_members,
    apply_contact_fields,
    attach_tag,
    count_dynamic_segment_members,
    count_list_members,
    count_saved_segment_members,
    create_contact,
    detach_tag,
    evaluate_segment_rules,
    get_contact_by_email,
    get_contact_by_id,
    get_contact_list_by_id,
    get_custom_field_by_key,
    get_import_by_id,
    get_segment_by_id,
    get_tag_by_id,
    get_tag_by_name,
    get_tag_names_for_contact,
    list_import_rows,
    list_imports,
    list_saved_segment_members,
    list_segment_rules,
    remove_list_member,
    upsert_field_value,
)
from growixa_api.contacts.repositories import add_segment_rule as add_segment_rule_row
from growixa_api.contacts.repositories import create_contact_list as create_contact_list_row
from growixa_api.contacts.repositories import create_custom_field as create_custom_field_row
from growixa_api.contacts.repositories import create_import as create_import_row
from growixa_api.contacts.repositories import create_segment as create_segment_row
from growixa_api.contacts.repositories import create_tag as create_tag_row
from growixa_api.contacts.repositories import get_field_values_for_contact as _get_field_values
from growixa_api.contacts.repositories import list_contact_lists as list_contact_lists_rows
from growixa_api.contacts.repositories import list_contacts as list_contacts_rows
from growixa_api.contacts.repositories import list_custom_fields as list_custom_fields_rows
from growixa_api.contacts.repositories import list_segments as list_segments_rows
from growixa_api.contacts.repositories import list_tags as list_tags_rows

ContactSnapshot = tuple[Contact, dict[str, str], list[str]]
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


class InvalidSegmentRuleError(Exception):
    pass


class InvalidColumnMappingError(Exception):
    pass


class ContactImportNotFoundError(Exception):
    pass


class UnknownCustomFieldError(Exception):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Unknown custom field key: {key}")


async def _apply_custom_fields(
    session: AsyncSession, *, contact_id: uuid.UUID, custom_fields: dict[str, str]
) -> None:
    for key, value in custom_fields.items():
        field = await get_custom_field_by_key(session, key)
        if field is None:
            raise UnknownCustomFieldError(key)
        await upsert_field_value(session, contact_id=contact_id, field_id=field.id, value=value)


async def _snapshot(session: AsyncSession, contact: Contact) -> ContactSnapshot:
    field_values = await _get_field_values(session, contact.id)
    tags = await get_tag_names_for_contact(session, contact.id)
    return contact, field_values, tags


async def create_or_update_contact(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    email: str,
    first_name: str | None,
    last_name: str | None,
    phone: str | None,
    source: str | None,
    custom_fields: dict[str, str],
) -> ContactSnapshot:
    """Create a contact, or update it in place if the email already exists.

    Email is the sole dedup key in Slice 2 (no fuzzy/name-based matching) — see
    DATA_MODEL.md §Slice 2 entities.
    """
    existing = await get_contact_by_email(session, email)
    if existing is None:
        contact = await create_contact(
            session,
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

    await _apply_custom_fields(session, contact_id=contact.id, custom_fields=custom_fields)
    await record_event(
        session, actor_user_id=actor_id, action=action, entity_type="contact", entity_id=contact.id
    )
    await session.commit()
    # `updated_at`'s server-side onupdate expires the attribute after an UPDATE commit;
    # a synchronous read of it afterward (e.g. in the API layer's response model) would
    # trigger an un-awaited lazy reload and raise MissingGreenlet. Refresh explicitly
    # while still inside an awaited call.
    await session.refresh(contact)

    return await _snapshot(session, contact)


async def update_contact(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    contact_id: uuid.UUID,
    email: str | None,
    first_name: str | None,
    last_name: str | None,
    phone: str | None,
    custom_fields: dict[str, str] | None,
) -> ContactSnapshot:
    contact = await get_contact_by_id(session, contact_id)
    if contact is None:
        raise ContactNotFoundError

    fields: dict[str, object] = {}
    if email is not None and email != contact.email:
        other = await get_contact_by_email(session, email)
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
        await _apply_custom_fields(session, contact_id=contact.id, custom_fields=custom_fields)

    await record_event(
        session,
        actor_user_id=actor_id,
        action="contact.updated",
        entity_type="contact",
        entity_id=contact.id,
    )
    await session.commit()
    await session.refresh(contact)

    return await _snapshot(session, contact)


async def update_contact_status(
    session: AsyncSession, *, actor_id: uuid.UUID, contact_id: uuid.UUID, status: str
) -> ContactSnapshot:
    contact = await get_contact_by_id(session, contact_id)
    if contact is None:
        raise ContactNotFoundError

    old_status = contact.status
    await apply_contact_fields(contact, {"status": status})

    action = "contact.archived" if status == "ARCHIVED" else "contact.updated"
    await record_event(
        session,
        actor_user_id=actor_id,
        action=action,
        entity_type="contact",
        entity_id=contact.id,
        metadata={"old_status": old_status, "new_status": status},
    )
    await session.commit()
    await session.refresh(contact)

    return await _snapshot(session, contact)


async def get_contact_with_fields(session: AsyncSession, contact_id: uuid.UUID) -> ContactSnapshot:
    contact = await get_contact_by_id(session, contact_id)
    if contact is None:
        raise ContactNotFoundError
    return await _snapshot(session, contact)


async def list_contacts_with_fields(session: AsyncSession) -> list[ContactSnapshot]:
    contacts = await list_contacts_rows(session)
    return [await _snapshot(session, contact) for contact in contacts]


async def list_custom_fields(session: AsyncSession) -> Sequence[ContactCustomField]:
    return await list_custom_fields_rows(session)


async def create_custom_field(
    session: AsyncSession, *, key: str, label: str, field_type: str
) -> ContactCustomField:
    existing = await get_custom_field_by_key(session, key)
    if existing is not None:
        raise DuplicateFieldKeyError
    field = await create_custom_field_row(session, key=key, label=label, field_type=field_type)
    await session.commit()
    return field


async def list_tags(session: AsyncSession) -> Sequence[Tag]:
    return await list_tags_rows(session)


async def create_tag(session: AsyncSession, *, name: str) -> Tag:
    existing = await get_tag_by_name(session, name)
    if existing is not None:
        raise DuplicateTagNameError
    tag = await create_tag_row(session, name=name)
    await session.commit()
    return tag


async def attach_tag_to_contact(
    session: AsyncSession, *, actor_id: uuid.UUID, contact_id: uuid.UUID, tag_id: uuid.UUID
) -> ContactSnapshot:
    contact = await get_contact_by_id(session, contact_id)
    if contact is None:
        raise ContactNotFoundError
    tag = await get_tag_by_id(session, tag_id)
    if tag is None:
        raise TagNotFoundError

    await attach_tag(session, contact_id=contact_id, tag_id=tag_id)
    await record_event(
        session,
        actor_user_id=actor_id,
        action="contact.tagged",
        entity_type="contact",
        entity_id=contact_id,
        metadata={"tag": tag.name},
    )
    await session.commit()

    return await _snapshot(session, contact)


async def detach_tag_from_contact(
    session: AsyncSession, *, actor_id: uuid.UUID, contact_id: uuid.UUID, tag_id: uuid.UUID
) -> ContactSnapshot:
    contact = await get_contact_by_id(session, contact_id)
    if contact is None:
        raise ContactNotFoundError
    tag = await get_tag_by_id(session, tag_id)
    if tag is None:
        raise TagNotFoundError

    await detach_tag(session, contact_id=contact_id, tag_id=tag_id)
    await record_event(
        session,
        actor_user_id=actor_id,
        action="contact.tagged",
        entity_type="contact",
        entity_id=contact_id,
        metadata={"untagged": tag.name},
    )
    await session.commit()

    return await _snapshot(session, contact)


async def list_lists_with_counts(session: AsyncSession) -> list[tuple[ContactList, int]]:
    lists = await list_contact_lists_rows(session)
    return [(cl, await count_list_members(session, cl.id)) for cl in lists]


async def get_list_with_count(session: AsyncSession, list_id: uuid.UUID) -> tuple[ContactList, int]:
    contact_list = await get_contact_list_by_id(session, list_id)
    if contact_list is None:
        raise ContactListNotFoundError
    count = await count_list_members(session, list_id)
    return contact_list, count


async def create_list(
    session: AsyncSession, *, actor_id: uuid.UUID, name: str, description: str | None
) -> tuple[ContactList, int]:
    contact_list = await create_contact_list_row(
        session, name=name, description=description, created_by_user_id=actor_id
    )
    await session.commit()
    return contact_list, 0


async def add_contact_to_list(
    session: AsyncSession, *, actor_id: uuid.UUID, list_id: uuid.UUID, contact_id: uuid.UUID
) -> tuple[ContactList, int]:
    contact_list = await get_contact_list_by_id(session, list_id)
    if contact_list is None:
        raise ContactListNotFoundError
    contact = await get_contact_by_id(session, contact_id)
    if contact is None:
        raise ContactNotFoundError

    await add_list_member(session, list_id=list_id, contact_id=contact_id)
    await record_event(
        session,
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
    session: AsyncSession, *, field: str, operator: str, value: str
) -> None:
    if field.startswith("custom_field:"):
        key = field.split(":", 1)[1]
        existing = await get_custom_field_by_key(session, key)
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
    session: AsyncSession, segment: Segment, rules: Sequence[SegmentRule]
) -> int:
    if segment.type == "SAVED":
        return await count_saved_segment_members(session, segment.id)
    return await count_dynamic_segment_members(session, rules)


async def create_segment_with_rules(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    name: str,
    type_: str,
    rules: list[tuple[str, str, str]],
) -> SegmentDetail:
    for field, operator, value in rules:
        await _validate_segment_rule(session, field=field, operator=operator, value=value)

    segment = await create_segment_row(session, name=name, type_=type_, created_by_user_id=actor_id)
    rule_rows = [
        await add_segment_rule_row(session, segment_id=segment.id, field=f, operator=o, value=v)
        for f, o, v in rules
    ]

    if type_ == "SAVED":
        matches = await evaluate_segment_rules(session, rule_rows)
        await add_segment_members(
            session, segment_id=segment.id, contact_ids=[c.id for c in matches]
        )

    await record_event(
        session,
        actor_user_id=actor_id,
        action="segment.created",
        entity_type="segment",
        entity_id=segment.id,
        metadata={"type": type_, "rule_count": len(rule_rows)},
    )
    await session.commit()

    count = await _segment_member_count(session, segment, rule_rows)
    return segment, rule_rows, count


async def get_segment_with_details(session: AsyncSession, segment_id: uuid.UUID) -> SegmentDetail:
    segment = await get_segment_by_id(session, segment_id)
    if segment is None:
        raise SegmentNotFoundError
    rules = await list_segment_rules(session, segment_id)
    count = await _segment_member_count(session, segment, rules)
    return segment, rules, count


async def list_segments_with_details(session: AsyncSession) -> list[SegmentDetail]:
    segments = await list_segments_rows(session)
    details = []
    for segment in segments:
        rules = await list_segment_rules(session, segment.id)
        count = await _segment_member_count(session, segment, rules)
        details.append((segment, rules, count))
    return details


async def list_segment_members(
    session: AsyncSession, segment_id: uuid.UUID
) -> list[ContactSnapshot]:
    segment = await get_segment_by_id(session, segment_id)
    if segment is None:
        raise SegmentNotFoundError

    if segment.type == "SAVED":
        contacts = await list_saved_segment_members(session, segment_id)
    else:
        rules = await list_segment_rules(session, segment_id)
        contacts = await evaluate_segment_rules(session, rules)

    return [await _snapshot(session, contact) for contact in contacts]


async def remove_contact_from_list(
    session: AsyncSession, *, actor_id: uuid.UUID, list_id: uuid.UUID, contact_id: uuid.UUID
) -> tuple[ContactList, int]:
    contact_list = await get_contact_list_by_id(session, list_id)
    if contact_list is None:
        raise ContactListNotFoundError
    contact = await get_contact_by_id(session, contact_id)
    if contact is None:
        raise ContactNotFoundError

    await remove_list_member(session, list_id=list_id, contact_id=contact_id)
    await record_event(
        session,
        actor_user_id=actor_id,
        action="contact.list_added",
        entity_type="contact",
        entity_id=contact_id,
        metadata={"list_removed": contact_list.name},
    )
    await session.commit()

    count = await count_list_members(session, list_id)
    return contact_list, count


async def _validate_column_mapping(session: AsyncSession, column_mapping: dict[str, str]) -> None:
    if not column_mapping:
        raise InvalidColumnMappingError("column_mapping must not be empty")
    if "email" not in column_mapping.values():
        raise InvalidColumnMappingError("column_mapping must map a column to 'email'")

    for target in column_mapping.values():
        if target in CONTACT_IMPORT_FIELD_TARGETS:
            continue
        if target.startswith("custom_field:"):
            key = target.split(":", 1)[1]
            if await get_custom_field_by_key(session, key) is None:
                raise InvalidColumnMappingError(f"Unknown custom field key: {key}")
            continue
        raise InvalidColumnMappingError(f"Unsupported column mapping target: {target}")


async def import_contacts_from_csv(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    filename: str,
    csv_text: str,
    column_mapping: dict[str, str],
) -> ContactImport:
    await _validate_column_mapping(session, column_mapping)

    contact_import = await create_import_row(
        session, filename=filename, column_mapping=column_mapping, created_by_user_id=actor_id
    )

    imported = updated = skipped = errored = 0
    reader = csv.DictReader(io.StringIO(csv_text))
    for row_number, raw_row in enumerate(reader, start=1):
        if not any((raw_row.get(header) or "").strip() for header in column_mapping):
            await add_import_row(
                session,
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
                import_id=contact_import.id,
                row_number=row_number,
                email=None,
                status="ERROR",
                error_message="Missing required email value",
            )
            errored += 1
            continue

        existing = await get_contact_by_email(session, email)
        try:
            await create_or_update_contact(
                session,
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


async def get_import(session: AsyncSession, import_id: uuid.UUID) -> ContactImport:
    contact_import = await get_import_by_id(session, import_id)
    if contact_import is None:
        raise ContactImportNotFoundError
    return contact_import


async def list_contact_imports(session: AsyncSession) -> Sequence[ContactImport]:
    return await list_imports(session)


async def list_contact_import_rows(
    session: AsyncSession, import_id: uuid.UUID
) -> Sequence[ContactImportRow]:
    if await get_import_by_id(session, import_id) is None:
        raise ContactImportNotFoundError
    return await list_import_rows(session, import_id)
