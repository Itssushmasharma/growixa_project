"""`GET /contacts` pagination tests (GRX-PERF-001).

Integration-tier: exercises real Postgres and the real create_app() app. Contact rows are
inserted directly (bypassing the create-contact API and its plan-limit check) so each test
can cheaply seed the row counts it needs without tripping the free plan's `max_contacts`
quota.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.config import get_settings
from growixa_api.contacts.models import (
    Contact,
    ContactCustomField,
    ContactFieldValue,
    ContactTag,
    SuppressionEntry,
    Tag,
)
from growixa_api.db import async_session_factory
from growixa_api.pagination import DEFAULT_LIMIT, MAX_LIMIT
from growixa_api.users.models import User


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _account_id_for(user_id: uuid.UUID) -> uuid.UUID:
    async with async_session_factory() as session:
        result = await session.execute(select(User.account_id).where(User.id == user_id))
        return result.scalar_one()


async def _seed_contacts(account_id: uuid.UUID, count: int) -> list[uuid.UUID]:
    """Inserts `count` contacts directly, each with a distinct, descending `created_at`
    (newest first, one second apart) so `GET /contacts`'s `ORDER BY created_at DESC` gives
    a deterministic, stable order for offset assertions."""
    base = datetime.now(UTC)
    ids: list[uuid.UUID] = []
    async with async_session_factory() as session:
        for i in range(count):
            contact_id = uuid.uuid4()
            ids.append(contact_id)
            session.add(
                Contact(
                    id=contact_id,
                    account_id=account_id,
                    email=f"{contact_id}@example.com",
                    created_at=base - timedelta(seconds=i),
                )
            )
        await session.commit()
    return ids


async def _cleanup_contacts(*contact_ids: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(ContactFieldValue).where(ContactFieldValue.contact_id.in_(contact_ids))
        )
        await session.execute(delete(ContactTag).where(ContactTag.contact_id.in_(contact_ids)))
        await session.execute(delete(Contact).where(Contact.id.in_(contact_ids)))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_contacts_default_page_size_is_bounded(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Pagination Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    contact_ids = await _seed_contacts(account_id, DEFAULT_LIMIT + 10)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.get("/contacts")

        assert response.status_code == 200
        # Bounded to the default page size, not the full 60-row account -- omitting
        # limit/offset entirely no longer returns everything.
        assert len(response.json()) == DEFAULT_LIMIT
    finally:
        await _cleanup_contacts(*contact_ids)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_contacts_huge_limit_is_clamped_not_honored(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Pagination Clamp Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    contact_ids = await _seed_contacts(account_id, MAX_LIMIT + 10)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.get("/contacts", params={"limit": 100_000})

        assert response.status_code == 200
        # A client requesting an unbounded page size gets the server-enforced max, not
        # everything and not a rejection.
        assert len(response.json()) == MAX_LIMIT
    finally:
        await _cleanup_contacts(*contact_ids)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_contacts_offset_skips_rows_at_sql_level(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Pagination Offset Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    contact_ids = await _seed_contacts(account_id, 12)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            page1 = await client.get("/contacts", params={"limit": 5, "offset": 0})
            page2 = await client.get("/contacts", params={"limit": 5, "offset": 5})

        assert page1.status_code == 200
        assert page2.status_code == 200
        page1_ids = [row["id"] for row in page1.json()]
        page2_ids = [row["id"] for row in page2.json()]
        assert len(page1_ids) == 5
        assert len(page2_ids) == 5
        # offset genuinely skips rows at the SQL level -- the second page is a disjoint,
        # different set, not a truncation of the same first 5 rows.
        assert set(page1_ids).isdisjoint(page2_ids)
    finally:
        await _cleanup_contacts(*contact_ids)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_contacts_pagination_respects_account_isolation(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_a = await user_factory(full_name="Pagination Isolation Admin A", role_name="Admin")
    admin_b = await user_factory(full_name="Pagination Isolation Admin B", role_name="Admin")

    account_a = await _account_id_for(admin_a)
    account_b = await _account_id_for(admin_b)

    contacts_a = await _seed_contacts(account_a, 8)
    contacts_b = await _seed_contacts(account_b, 8)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client:
            # Offset past account A's own 8 rows -- must never spill into account B's rows,
            # even though the SQL LIMIT/OFFSET is unaware of which account "owns" a slot.
            response = await client.get("/contacts", params={"limit": 50, "offset": 5})

        assert response.status_code == 200
        returned_ids = {row["id"] for row in response.json()}
        assert returned_ids.issubset({str(cid) for cid in contacts_a})
        assert returned_ids.isdisjoint({str(cid) for cid in contacts_b})
    finally:
        await _cleanup_contacts(*contacts_a)
        await _cleanup_contacts(*contacts_b)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_contacts_paginated_subset_resolves_tags_and_fields(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """`list_contacts_with_fields`'s batch-loaded tags/field-values must resolve correctly
    for a paginated subset of contacts, not silently apply to the whole account."""
    admin_id = await user_factory(full_name="Pagination Fields Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    contact_ids = await _seed_contacts(account_id, 8)
    # Tag and field-value attached only to the contact that will land on page 2
    # (offset=5, limit=5 -> index 5 of the newest-first ordering).
    target_contact_id = contact_ids[5]
    field_key = f"field_{uuid.uuid4().hex[:8]}"
    tag_name = f"tag_{uuid.uuid4().hex[:8]}"
    field_id = uuid.uuid4()
    tag_id = uuid.uuid4()
    async with async_session_factory() as session:
        session.add(
            ContactCustomField(
                id=field_id, account_id=account_id, key=field_key, label="Field", field_type="TEXT"
            )
        )
        session.add(Tag(id=tag_id, account_id=account_id, name=tag_name))
        await session.flush()
        session.add(
            ContactFieldValue(
                account_id=account_id,
                contact_id=target_contact_id,
                field_id=field_id,
                value="paginated-value",
            )
        )
        session.add(ContactTag(account_id=account_id, contact_id=target_contact_id, tag_id=tag_id))
        await session.commit()

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            page2 = await client.get("/contacts", params={"limit": 5, "offset": 5})

        assert page2.status_code == 200
        rows = {row["id"]: row for row in page2.json()}
        target_row = rows[str(target_contact_id)]
        assert target_row["custom_fields"] == {field_key: "paginated-value"}
        assert target_row["tags"] == [tag_name]
    finally:
        async with async_session_factory() as session:
            await session.execute(
                delete(ContactCustomField).where(ContactCustomField.id == field_id)
            )
            await session.execute(delete(Tag).where(Tag.id == tag_id))
            await session.commit()
        await _cleanup_contacts(*contact_ids)


# ---------------------------------------------------------------------------
# GRX-PERF-001 follow-up (review CHANGES_REQUESTED fix): `/contacts/stats` and
# `/contacts/count` give the Contacts page account-wide numbers that a single bounded
# `/contacts` page can no longer provide, plus server-side search/status/tag filters so
# the page's search box and filters work correctly against the paginated reality instead
# of only ever seeing the first page.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_contact_stats_are_not_bound_by_page_size(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Stats Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    contact_ids = await _seed_contacts(account_id, DEFAULT_LIMIT + 15)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.get("/contacts/stats")

        assert response.status_code == 200
        body = response.json()
        # The account has DEFAULT_LIMIT + 15 contacts -- a stat badge derived from a single
        # bounded /contacts page would undercount at DEFAULT_LIMIT. The stats endpoint must
        # reflect the true account-wide total regardless of pagination.
        assert body["total"] == DEFAULT_LIMIT + 15
        assert body["active"] == DEFAULT_LIMIT + 15
        assert body["archived"] == 0
    finally:
        await _cleanup_contacts(*contact_ids)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_contact_stats_counts_suppressed_and_archived(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Stats Status Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    archived_id = uuid.uuid4()
    suppressed_id = uuid.uuid4()
    active_id = uuid.uuid4()
    suppression_id = uuid.uuid4()
    async with async_session_factory() as session:
        session.add(
            Contact(
                id=archived_id,
                account_id=account_id,
                email=f"{archived_id}@example.com",
                status="ARCHIVED",
            )
        )
        session.add(
            Contact(
                id=suppressed_id,
                account_id=account_id,
                email=f"{suppressed_id}@example.com",
            )
        )
        session.add(Contact(id=active_id, account_id=account_id, email=f"{active_id}@example.com"))
        await session.flush()
        session.add(
            SuppressionEntry(
                id=suppression_id,
                account_id=account_id,
                email=f"{suppressed_id}@example.com",
                reason="MANUAL",
            )
        )
        await session.commit()

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.get("/contacts/stats")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3
        assert body["archived"] == 1
        assert body["active"] == 2
        assert body["suppressed"] == 1
    finally:
        async with async_session_factory() as session:
            await session.execute(
                delete(SuppressionEntry).where(SuppressionEntry.id == suppression_id)
            )
            await session.commit()
        await _cleanup_contacts(archived_id, suppressed_id, active_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_contact_stats_respects_account_isolation(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_a = await user_factory(full_name="Stats Isolation Admin A", role_name="Admin")
    admin_b = await user_factory(full_name="Stats Isolation Admin B", role_name="Admin")
    account_a = await _account_id_for(admin_a)
    account_b = await _account_id_for(admin_b)

    contacts_a = await _seed_contacts(account_a, 3)
    contacts_b = await _seed_contacts(account_b, 9)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client:
            response = await client.get("/contacts/stats")

        assert response.status_code == 200
        # Must reflect only account A's 3 contacts, never account B's 9.
        assert response.json()["total"] == 3
    finally:
        await _cleanup_contacts(*contacts_a)
        await _cleanup_contacts(*contacts_b)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_contact_count_matches_active_page_regardless_of_limit(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Count Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    contact_ids = await _seed_contacts(account_id, DEFAULT_LIMIT + 7)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            list_response = await client.get("/contacts")
            count_response = await client.get("/contacts/count")

        assert list_response.status_code == 200
        assert len(list_response.json()) == DEFAULT_LIMIT
        assert count_response.status_code == 200
        # Total-pages math needs the true match count, not the bounded page length.
        assert count_response.json()["total"] == DEFAULT_LIMIT + 7
    finally:
        await _cleanup_contacts(*contact_ids)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_and_count_contacts_search_filters_at_sql_level(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Search Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    match_id = uuid.uuid4()
    other_ids = await _seed_contacts(account_id, 5)
    async with async_session_factory() as session:
        session.add(
            Contact(
                id=match_id,
                account_id=account_id,
                email="findme-unique-needle@example.com",
                first_name="Findme",
            )
        )
        await session.commit()

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            list_response = await client.get("/contacts", params={"search": "findme-unique"})
            count_response = await client.get("/contacts/count", params={"search": "findme-unique"})

        assert list_response.status_code == 200
        rows = list_response.json()
        assert len(rows) == 1
        assert rows[0]["id"] == str(match_id)
        assert count_response.status_code == 200
        assert count_response.json()["total"] == 1
    finally:
        await _cleanup_contacts(match_id, *other_ids)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_contacts_status_filter_at_sql_level(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Status Filter Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    archived_id = uuid.uuid4()
    active_id = uuid.uuid4()
    async with async_session_factory() as session:
        session.add(
            Contact(
                id=archived_id,
                account_id=account_id,
                email=f"{archived_id}@example.com",
                status="ARCHIVED",
            )
        )
        session.add(Contact(id=active_id, account_id=account_id, email=f"{active_id}@example.com"))
        await session.commit()

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.get("/contacts", params={"status": "ARCHIVED"})

        assert response.status_code == 200
        rows = response.json()
        assert {row["id"] for row in rows} == {str(archived_id)}
    finally:
        await _cleanup_contacts(archived_id, active_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_contacts_tag_filter_at_sql_level(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Tag Filter Admin", role_name="Admin")
    account_id = await _account_id_for(admin_id)

    tagged_id = uuid.uuid4()
    untagged_id = uuid.uuid4()
    tag_id = uuid.uuid4()
    async with async_session_factory() as session:
        session.add(Tag(id=tag_id, account_id=account_id, name=f"tag_{uuid.uuid4().hex[:8]}"))
        session.add(Contact(id=tagged_id, account_id=account_id, email=f"{tagged_id}@example.com"))
        session.add(
            Contact(id=untagged_id, account_id=account_id, email=f"{untagged_id}@example.com")
        )
        await session.flush()
        session.add(ContactTag(account_id=account_id, contact_id=tagged_id, tag_id=tag_id))
        await session.commit()

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.get("/contacts", params={"tag_id": str(tag_id)})

        assert response.status_code == 200
        rows = response.json()
        assert {row["id"] for row in rows} == {str(tagged_id)}
    finally:
        async with async_session_factory() as session:
            await session.execute(delete(Tag).where(Tag.id == tag_id))
            await session.commit()
        await _cleanup_contacts(tagged_id, untagged_id)
