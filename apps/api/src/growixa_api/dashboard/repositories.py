import uuid
from datetime import UTC, datetime

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.models import AccountCreditBalance, AccountSubscription, SubscriptionPlan
from growixa_api.campaigns.models import Campaign, CampaignRecipient
from growixa_api.contacts.models import Contact
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery
from growixa_api.social.models import SocialPost


def _shift_month(dt: datetime, months: int) -> datetime:
    """Calendar-exact month arithmetic (no timedelta-day approximation, no drift) --
    used to build the 6-point contact-growth series below."""
    total = dt.year * 12 + (dt.month - 1) + months
    year, month = divmod(total, 12)
    return dt.replace(year=year, month=month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


async def count_active_contacts(session: AsyncSession, account_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count(Contact.id)).where(
            Contact.account_id == account_id,
            Contact.status == "ACTIVE",
            Contact.deleted_at.is_(None),
        )
    )
    return result.scalar_one()


async def get_campaign_status_breakdown(
    session: AsyncSession, account_id: uuid.UUID
) -> dict[str, int]:
    result = await session.execute(
        select(Campaign.status, func.count(Campaign.id))
        .where(Campaign.account_id == account_id)
        .group_by(Campaign.status)
    )
    return {row[0]: row[1] for row in result.all()}


async def count_scheduled_social_posts(session: AsyncSession, account_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count(SocialPost.id)).where(
            SocialPost.account_id == account_id, SocialPost.status == "SCHEDULED"
        )
    )
    return result.scalar_one()


async def get_account_wide_engagement(
    session: AsyncSession, account_id: uuid.UUID
) -> dict[str, int]:
    """Delivered/opened/clicked across every campaign this account has ever sent --
    same counting shape as analytics/repositories.py's per-campaign report (delivery
    status for `delivered`, distinct-event-per-delivery for `opened`/`clicked` since a
    redelivered webhook is a new, undeduplicated `email_events` row), just filtered by
    `account_id` directly instead of joining through one `campaign_id`."""
    delivered_result = await session.execute(
        select(func.count(MessageDelivery.id)).where(
            MessageDelivery.account_id == account_id,
            MessageDelivery.status.in_(("SENT", "DELIVERED")),
        )
    )
    delivered = delivered_result.scalar_one()

    event_result = await session.execute(
        select(EmailEvent.event_type, func.count(func.distinct(EmailEvent.message_delivery_id)))
        .where(EmailEvent.account_id == account_id)
        .group_by(EmailEvent.event_type)
    )
    event_counts = {row[0]: row[1] for row in event_result.all()}

    return {
        "delivered": delivered,
        "opened": event_counts.get("OPENED", 0),
        "clicked": event_counts.get("CLICKED", 0),
    }


async def get_contact_growth(
    session: AsyncSession, account_id: uuid.UUID, *, months: int = 6
) -> list[tuple[str, int]]:
    """Cumulative total-contacts curve for the last `months` calendar months: a baseline
    (everyone created before the window) plus a running sum of each month's new
    contacts. Avoids a window-function/generate_series query for a fixed short series."""
    now = datetime.now(UTC)
    window_start = _shift_month(now.replace(day=1), -(months - 1))

    baseline_result = await session.execute(
        select(func.count(Contact.id)).where(
            Contact.account_id == account_id,
            Contact.created_at < window_start,
            Contact.deleted_at.is_(None),
        )
    )
    baseline = baseline_result.scalar_one()

    monthly_result = await session.execute(
        select(
            func.date_trunc("month", Contact.created_at).label("month"),
            func.count(Contact.id),
        )
        .where(
            Contact.account_id == account_id,
            Contact.created_at >= window_start,
            Contact.deleted_at.is_(None),
        )
        .group_by("month")
    )
    monthly_new = {row[0].strftime("%Y-%m"): row[1] for row in monthly_result.all()}

    points: list[tuple[str, int]] = []
    running = baseline
    for i in range(months):
        month_key = _shift_month(window_start, i).strftime("%Y-%m")
        running += monthly_new.get(month_key, 0)
        points.append((month_key, running))
    return points


async def get_quota_snapshot(
    session: AsyncSession, account_id: uuid.UUID
) -> Row[tuple[AccountSubscription, SubscriptionPlan]] | None:
    result = await session.execute(
        select(AccountSubscription, SubscriptionPlan)
        .join(SubscriptionPlan, SubscriptionPlan.id == AccountSubscription.plan_id)
        .where(AccountSubscription.account_id == account_id)
    )
    return result.first()


async def get_ai_credit_balance(session: AsyncSession, account_id: uuid.UUID) -> int:
    result = await session.execute(
        select(AccountCreditBalance.remaining_credits).where(
            AccountCreditBalance.account_id == account_id,
            AccountCreditBalance.credit_type == "AI_RUNS",
        )
    )
    return result.scalar_one_or_none() or 0


async def list_recent_campaigns_with_stats(
    session: AsyncSession, account_id: uuid.UUID, *, limit: int = 5
) -> list[tuple[Campaign, int, float | None]]:
    campaigns_result = await session.execute(
        select(Campaign)
        .where(Campaign.account_id == account_id)
        .order_by(Campaign.created_at.desc())
        .limit(limit)
    )
    campaigns = campaigns_result.scalars().all()
    if not campaigns:
        return []
    ids = [campaign.id for campaign in campaigns]

    sent_result = await session.execute(
        select(CampaignRecipient.campaign_id, func.count(CampaignRecipient.id))
        .where(CampaignRecipient.campaign_id.in_(ids), CampaignRecipient.status == "SENT")
        .group_by(CampaignRecipient.campaign_id)
    )
    sent_counts = {row[0]: row[1] for row in sent_result.all()}

    delivered_result = await session.execute(
        select(CampaignRecipient.campaign_id, func.count(MessageDelivery.id))
        .join(MessageDelivery, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(
            CampaignRecipient.campaign_id.in_(ids),
            MessageDelivery.status.in_(("SENT", "DELIVERED")),
        )
        .group_by(CampaignRecipient.campaign_id)
    )
    delivered_counts = {row[0]: row[1] for row in delivered_result.all()}

    opened_result = await session.execute(
        select(
            CampaignRecipient.campaign_id,
            func.count(func.distinct(EmailEvent.message_delivery_id)),
        )
        .join(MessageDelivery, EmailEvent.message_delivery_id == MessageDelivery.id)
        .join(CampaignRecipient, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(CampaignRecipient.campaign_id.in_(ids), EmailEvent.event_type == "OPENED")
        .group_by(CampaignRecipient.campaign_id)
    )
    opened_counts = {row[0]: row[1] for row in opened_result.all()}

    rows: list[tuple[Campaign, int, float | None]] = []
    for campaign in campaigns:
        sent = sent_counts.get(campaign.id, 0)
        delivered = delivered_counts.get(campaign.id, 0)
        opened = opened_counts.get(campaign.id, 0)
        open_rate = round(opened / delivered * 100, 1) if delivered > 0 else None
        rows.append((campaign, sent, open_rate))
    return rows
