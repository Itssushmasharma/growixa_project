import uuid
from collections.abc import Sequence

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.campaigns.models import Campaign
from growixa_api.usage.models import UsageRecord
from growixa_api.users.models import User


async def list_accounts(session: AsyncSession) -> Sequence[Account]:
    result = await session.execute(select(Account).order_by(Account.created_at))
    return result.scalars().all()


async def get_account_by_id(session: AsyncSession, account_id: uuid.UUID) -> Account | None:
    return await session.get(Account, account_id)


async def count_users_by_account(session: AsyncSession) -> dict[uuid.UUID, int]:
    stmt = select(User.account_id, func.count(User.id)).group_by(User.account_id)
    result = await session.execute(stmt)
    return {account_id: count for account_id, count in result.all()}


async def list_usage_summary(
    session: AsyncSession,
) -> Sequence[Row[tuple[uuid.UUID, str, str, float, str]]]:
    """One row per (account, operation_type) with quantity summed -- GRX-SAAS-008 /
    DEC-GRX-021 point 3: an aggregate, never a raw per-record cross-account dump."""
    stmt = (
        select(
            UsageRecord.account_id,
            Account.name,
            UsageRecord.operation_type,
            func.sum(UsageRecord.quantity).label("total_quantity"),
            UsageRecord.unit,
        )
        .join(Account, Account.id == UsageRecord.account_id)
        .group_by(
            UsageRecord.account_id, Account.name, UsageRecord.operation_type, UsageRecord.unit
        )
        .order_by(Account.name, UsageRecord.operation_type)
    )
    result = await session.execute(stmt)
    return result.all()


async def list_campaigns_by_status(
    session: AsyncSession, *, statuses: Sequence[str]
) -> Sequence[Row[tuple[Campaign, str]]]:
    """Cross-account by design (GRX-SAAS-008) -- never account_id-scoped. Returns only
    scheduling metadata via the Campaign row itself; callers must not surface
    subject/body_html/body_text (THREAT_MODEL.md T37)."""
    stmt = (
        select(Campaign, Account.name)
        .join(Account, Account.id == Campaign.account_id)
        .where(Campaign.status.in_(statuses))
        .order_by(Campaign.updated_at.desc())
    )
    result = await session.execute(stmt)
    return result.all()


async def get_campaign_by_id(session: AsyncSession, campaign_id: uuid.UUID) -> Campaign | None:
    return await session.get(Campaign, campaign_id)
