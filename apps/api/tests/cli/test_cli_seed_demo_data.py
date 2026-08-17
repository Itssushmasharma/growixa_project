"""Integration tests for the demo-data seed CLI (apps/api/src/growixa_api/cli/seed_demo_data.py).

Exercises real Postgres via async_session_factory.
"""

import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import delete, select

from growixa_api.accounts.models import Account
from growixa_api.auth.security import hash_password
from growixa_api.campaigns.models import Campaign, CampaignRecipient, CampaignVersion
from growixa_api.cli.seed_demo_data import main
from growixa_api.contacts.models import (
    Contact,
    ContactList,
    ContactListMember,
    ContactTag,
    Tag,
)
from growixa_api.db import async_session_factory
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.social.models import (
    SocialConnection,
    SocialPost,
    SocialPostMedia,
    SocialPostVersion,
)
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion
from growixa_api.users.models import User


@pytest.fixture
async def seed_test_account() -> AsyncIterator[tuple[uuid.UUID, str]]:
    """Creates a temporary account + active admin user for seed testing, cleaning up afterwards."""
    email = f"seed-test-{uuid.uuid4()}@growixa.local"
    account_id = uuid.uuid4()

    async with async_session_factory() as session:
        account = Account(id=account_id, name="Seed Test Company")
        session.add(account)
        await session.flush()

        user = User(
            account_id=account_id,
            email=email,
            password_hash=hash_password("SmokeTest123!"),
            full_name="Seed Test User",
            status="ACTIVE",
        )
        session.add(user)
        await session.commit()

    yield account_id, email

    # Full cleanup in reverse topological order
    async with async_session_factory() as session:
        await session.execute(
            delete(SocialPostMedia).where(SocialPostMedia.account_id == account_id)
        )
        await session.execute(
            delete(SocialPostVersion).where(SocialPostVersion.account_id == account_id)
        )
        await session.execute(delete(SocialPost).where(SocialPost.account_id == account_id))
        await session.execute(
            delete(SocialConnection).where(SocialConnection.account_id == account_id)
        )
        await session.execute(
            delete(CampaignRecipient).where(CampaignRecipient.account_id == account_id)
        )
        await session.execute(
            delete(CampaignVersion).where(CampaignVersion.account_id == account_id)
        )
        await session.execute(delete(Campaign).where(Campaign.account_id == account_id))
        await session.execute(delete(SenderIdentity).where(SenderIdentity.account_id == account_id))
        await session.execute(
            delete(EmailProviderConnection).where(EmailProviderConnection.account_id == account_id)
        )
        await session.execute(
            delete(EmailTemplateVersion).where(EmailTemplateVersion.account_id == account_id)
        )
        await session.execute(delete(EmailTemplate).where(EmailTemplate.account_id == account_id))
        await session.execute(
            delete(ContactListMember).where(ContactListMember.account_id == account_id)
        )
        await session.execute(delete(ContactList).where(ContactList.account_id == account_id))
        await session.execute(delete(ContactTag).where(ContactTag.account_id == account_id))
        await session.execute(delete(Contact).where(Contact.account_id == account_id))
        await session.execute(delete(Tag).where(Tag.account_id == account_id))
        await session.execute(delete(User).where(User.account_id == account_id))
        await session.execute(delete(Account).where(Account.id == account_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_seed_demo_data_populates_all_resources(
    seed_test_account: tuple[uuid.UUID, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account_id, email = seed_test_account
    monkeypatch.setenv("SEED_ACCOUNT_EMAIL", email)
    monkeypatch.delenv("SEED_FORCE", raising=False)

    exit_code = await main()
    assert exit_code == 0

    async with async_session_factory() as session:
        # Contacts
        contacts = (
            (await session.execute(select(Contact).where(Contact.account_id == account_id)))
            .scalars()
            .all()
        )
        assert len(contacts) == 20

        # Tags
        tags = (
            (await session.execute(select(Tag).where(Tag.account_id == account_id))).scalars().all()
        )
        assert len(tags) > 0

        # Contact Lists
        lists = (
            (await session.execute(select(ContactList).where(ContactList.account_id == account_id)))
            .scalars()
            .all()
        )
        assert len(lists) == 3

        # Email Templates
        templates = (
            (
                await session.execute(
                    select(EmailTemplate).where(EmailTemplate.account_id == account_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(templates) == 4

        # Campaigns
        campaigns = (
            (await session.execute(select(Campaign).where(Campaign.account_id == account_id)))
            .scalars()
            .all()
        )
        assert len(campaigns) == 5

        # Social Posts
        posts = (
            (await session.execute(select(SocialPost).where(SocialPost.account_id == account_id)))
            .scalars()
            .all()
        )
        assert len(posts) == 5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_seed_demo_data_is_idempotent(
    seed_test_account: tuple[uuid.UUID, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account_id, email = seed_test_account
    monkeypatch.setenv("SEED_ACCOUNT_EMAIL", email)
    monkeypatch.delenv("SEED_FORCE", raising=False)

    first = await main()
    second = await main()

    assert first == 0
    assert second == 0

    async with async_session_factory() as session:
        contacts = (
            (await session.execute(select(Contact).where(Contact.account_id == account_id)))
            .scalars()
            .all()
        )
        assert len(contacts) == 20


@pytest.mark.asyncio
@pytest.mark.integration
async def test_seed_demo_data_force_reseed(
    seed_test_account: tuple[uuid.UUID, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account_id, email = seed_test_account
    monkeypatch.setenv("SEED_ACCOUNT_EMAIL", email)

    # Initial seed
    monkeypatch.delenv("SEED_FORCE", raising=False)
    exit_1 = await main()
    assert exit_1 == 0

    # Force re-seed
    monkeypatch.setenv("SEED_FORCE", "1")
    exit_2 = await main()
    assert exit_2 == 0

    async with async_session_factory() as session:
        contacts = (
            (await session.execute(select(Contact).where(Contact.account_id == account_id)))
            .scalars()
            .all()
        )
        assert len(contacts) == 20


@pytest.mark.asyncio
@pytest.mark.integration
async def test_seed_demo_data_invalid_user_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SEED_ACCOUNT_EMAIL", f"nonexistent-{uuid.uuid4()}@example.com")
    exit_code = await main()
    assert exit_code == 1
