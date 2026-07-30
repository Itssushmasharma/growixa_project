import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.services import record_event
from growixa_api.contacts.models import Contact, ContactCustomField, ContactList, Tag
from growixa_api.contacts.repositories import (
    add_list_member,
    apply_contact_fields,
    attach_tag,
    count_list_members,
    create_contact,
    detach_tag,
    get_contact_by_email,
    get_contact_by_id,
    get_contact_list_by_id,
    get_custom_field_by_key,
    get_tag_by_id,
    get_tag_by_name,
    get_tag_names_for_contact,
    remove_list_member,
    upsert_field_value,
)
from growixa_api.contacts.repositories import create_contact_list as create_contact_list_row
from growixa_api.contacts.repositories import create_custom_field as create_custom_field_row
from growixa_api.contacts.repositories import create_tag as create_tag_row
from growixa_api.contacts.repositories import get_field_values_for_contact as _get_field_values
from growixa_api.contacts.repositories import list_contact_lists as list_contact_lists_rows
from growixa_api.contacts.repositories import list_contacts as list_contacts_rows
from growixa_api.contacts.repositories import list_custom_fields as list_custom_fields_rows
from growixa_api.contacts.repositories import list_tags as list_tags_rows

ContactSnapshot = tuple[Contact, dict[str, str], list[str]]


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
