import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.services import record_event
from growixa_api.contacts.models import Contact, ContactCustomField
from growixa_api.contacts.repositories import (
    apply_contact_fields,
    create_contact,
    get_contact_by_email,
    get_contact_by_id,
    get_custom_field_by_key,
    upsert_field_value,
)
from growixa_api.contacts.repositories import create_custom_field as create_custom_field_row
from growixa_api.contacts.repositories import get_field_values_for_contact as _get_field_values
from growixa_api.contacts.repositories import list_contacts as list_contacts_rows
from growixa_api.contacts.repositories import list_custom_fields as list_custom_fields_rows


class DuplicateEmailError(Exception):
    pass


class DuplicateFieldKeyError(Exception):
    pass


class ContactNotFoundError(Exception):
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
) -> tuple[Contact, dict[str, str]]:
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

    field_values = await _get_field_values(session, contact.id)
    return contact, field_values


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
) -> tuple[Contact, dict[str, str]]:
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

    field_values = await _get_field_values(session, contact.id)
    return contact, field_values


async def update_contact_status(
    session: AsyncSession, *, actor_id: uuid.UUID, contact_id: uuid.UUID, status: str
) -> tuple[Contact, dict[str, str]]:
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

    field_values = await _get_field_values(session, contact.id)
    return contact, field_values


async def get_contact_with_fields(
    session: AsyncSession, contact_id: uuid.UUID
) -> tuple[Contact, dict[str, str]]:
    contact = await get_contact_by_id(session, contact_id)
    if contact is None:
        raise ContactNotFoundError
    field_values = await _get_field_values(session, contact.id)
    return contact, field_values


async def list_contacts_with_fields(
    session: AsyncSession,
) -> list[tuple[Contact, dict[str, str]]]:
    contacts = await list_contacts_rows(session)
    return [(contact, await _get_field_values(session, contact.id)) for contact in contacts]


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
