import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.dashboard.repositories import (
    count_active_contacts,
    count_scheduled_social_posts,
    get_account_wide_engagement,
    get_ai_credit_balance,
    get_campaign_status_breakdown,
    get_contact_growth,
    get_quota_snapshot,
    list_recent_campaigns_with_stats,
)
from growixa_api.dashboard.schemas import (
    CampaignStatusBreakdownOut,
    ContactGrowthPointOut,
    DashboardOverviewOut,
    QuotaStatusOut,
    RecentCampaignOut,
)

_ACTIVE_CAMPAIGN_STATUSES = ("SCHEDULED", "DISPATCHING", "SENDING")


async def get_dashboard_overview(
    session: AsyncSession, account_id: uuid.UUID
) -> DashboardOverviewOut:
    total_contacts = await count_active_contacts(session, account_id)
    status_breakdown = await get_campaign_status_breakdown(session, account_id)
    scheduled_social_posts = await count_scheduled_social_posts(session, account_id)
    engagement = await get_account_wide_engagement(session, account_id)
    contact_growth = await get_contact_growth(session, account_id)
    recent = await list_recent_campaigns_with_stats(session, account_id)
    quota_snapshot = await get_quota_snapshot(session, account_id)
    ai_credits = await get_ai_credit_balance(session, account_id)

    active_campaigns = sum(status_breakdown.get(s, 0) for s in _ACTIVE_CAMPAIGN_STATUSES)
    delivered = engagement["delivered"]
    open_rate = round(engagement["opened"] / delivered * 100, 1) if delivered > 0 else None
    click_rate = round(engagement["clicked"] / delivered * 100, 1) if delivered > 0 else None

    if quota_snapshot is not None:
        subscription, plan = quota_snapshot
        quota = QuotaStatusOut(
            plan_name=plan.name,
            contact_usage=total_contacts,
            contact_limit=plan.max_contacts,
            email_usage=subscription.period_email_used,
            email_limit=plan.max_monthly_emails,
            ai_usage=subscription.period_ai_used,
            ai_limit=plan.max_monthly_ai_runs,
            ai_credits_remaining=ai_credits,
        )
    else:
        # Every account gets a Free-tier subscription row at registration (DEC-GRX-030)
        # -- this branch is a defensive fallback, not an expected path.
        quota = QuotaStatusOut(
            plan_name="Unknown",
            contact_usage=total_contacts,
            contact_limit=None,
            email_usage=0,
            email_limit=None,
            ai_usage=0,
            ai_limit=None,
            ai_credits_remaining=ai_credits,
        )

    return DashboardOverviewOut(
        total_contacts=total_contacts,
        active_campaigns=active_campaigns,
        scheduled_social_posts=scheduled_social_posts,
        email_open_rate_pct=open_rate,
        email_click_rate_pct=click_rate,
        quota=quota,
        campaign_status_breakdown=CampaignStatusBreakdownOut(
            draft=status_breakdown.get("DRAFT", 0),
            scheduled=status_breakdown.get("SCHEDULED", 0),
            sending=status_breakdown.get("DISPATCHING", 0) + status_breakdown.get("SENDING", 0),
            sent=status_breakdown.get("SENT", 0),
            cancelled=status_breakdown.get("CANCELLED", 0),
            failed=status_breakdown.get("FAILED", 0),
        ),
        contact_growth_6_months=[
            ContactGrowthPointOut(month=month, contacts=count) for month, count in contact_growth
        ],
        recent_campaigns=[
            RecentCampaignOut(
                id=campaign.id,
                name=campaign.name,
                status=campaign.status,
                sent_count=sent,
                open_rate_pct=open_rate,
            )
            for campaign, sent, open_rate in recent
        ],
    )
