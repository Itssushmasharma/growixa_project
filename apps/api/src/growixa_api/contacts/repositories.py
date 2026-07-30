import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.contacts.models import (
    Contact,
    ContactCustomField,
    ContactFieldValue,
    ContactList,
    ContactListMember,
    ContactTag,
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
