import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.contacts.models import Contact, ContactCustomField, ContactFieldValue


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
