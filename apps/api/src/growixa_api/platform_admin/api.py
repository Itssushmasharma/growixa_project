import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.campaigns.models import Campaign
from growixa_api.db import get_session
from growixa_api.platform_admin.schemas import (
    AccountDetailOut,
    AccountListItemOut,
    AccountUserOut,
    CampaignOversightItemOut,
    SecurityEventOut,
    UpdateAccountStatusIn,
    UsageSummaryItemOut,
)
from growixa_api.platform_admin.services import AccountNotFoundError, CampaignNotPausableError
from growixa_api.platform_admin.services import CampaignNotFoundError as CampaignRowNotFoundError
from growixa_api.platform_admin.services import get_account_detail as get_account_detail_service
from growixa_api.platform_admin.services import (
    list_accounts_with_user_counts as list_accounts_service,
)
from growixa_api.platform_admin.services import (
    list_campaigns_for_oversight as list_campaigns_for_oversight_service,
)
from growixa_api.platform_admin.services import (
    list_usage_summary_rows as list_usage_summary_rows_service,
)
from growixa_api.platform_admin.services import pause_campaign as pause_campaign_service
from growixa_api.platform_admin.services import (
    update_account_status as update_account_status_service,
)
from growixa_api.platform_auth.dependencies import require_platform_permission

router = APIRouter(prefix="/platform/accounts", tags=["platform_admin"])
usage_router = APIRouter(prefix="/platform", tags=["platform_admin"])

_require_manage = require_platform_permission("platform.accounts.manage")
_require_usage_manage = require_platform_permission("platform.usage.manage")


def _to_list_item(account: Account, user_count: int) -> AccountListItemOut:
    return AccountListItemOut(
        id=account.id,
        name=account.name,
        status=account.status,
        selected_plan_slug=account.selected_plan_slug,
        created_at=account.created_at,
        user_count=user_count,
    )


@router.get("", response_model=list[AccountListItemOut])
async def list_accounts_route(
    _platform_admin_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> list[AccountListItemOut]:
    accounts_with_counts = await list_accounts_service(session)
    return [_to_list_item(account, count) for account, count in accounts_with_counts]


@router.get("/{account_id}", response_model=AccountDetailOut)
async def get_account_detail_route(
    account_id: uuid.UUID,
    _platform_admin_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> AccountDetailOut:
    try:
        account, users, events = await get_account_detail_service(session, account_id=account_id)
    except AccountNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found") from exc

    return AccountDetailOut(
        id=account.id,
        name=account.name,
        status=account.status,
        selected_plan_slug=account.selected_plan_slug,
        created_at=account.created_at,
        users=[
            AccountUserOut(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                status=user.status,
                last_login_at=user.last_login_at,
            )
            for user in users
        ],
        security_activity=[
            SecurityEventOut(
                id=event.id,
                action=event.action,
                entity_type=event.entity_type,
                actor_user_id=event.actor_user_id,
                event_metadata=event.event_metadata,
                created_at=event.created_at,
            )
            for event in events
        ],
    )


@router.patch("/{account_id}/status", response_model=AccountListItemOut)
async def update_account_status_route(
    account_id: uuid.UUID,
    payload: UpdateAccountStatusIn,
    platform_admin_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> AccountListItemOut:
    try:
        account, user_count = await update_account_status_service(
            session,
            account_id=account_id,
            platform_admin_id=platform_admin_id,
            status=payload.status,
        )
    except AccountNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found") from exc

    return _to_list_item(account, user_count)


def _to_campaign_item(campaign: Campaign, account_name: str) -> CampaignOversightItemOut:
    return CampaignOversightItemOut(
        id=campaign.id,
        account_id=campaign.account_id,
        account_name=account_name,
        name=campaign.name,
        status=campaign.status,
        scheduled_at=campaign.scheduled_at,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


@usage_router.get("/usage", response_model=list[UsageSummaryItemOut])
async def list_usage_summary_route(
    _platform_admin_id: uuid.UUID = Depends(_require_usage_manage),
    session: AsyncSession = Depends(get_session),
) -> list[UsageSummaryItemOut]:
    rows = await list_usage_summary_rows_service(session)
    return [
        UsageSummaryItemOut(
            account_id=account_id,
            account_name=account_name,
            operation_type=operation_type,
            total_quantity=float(total_quantity),
            unit=unit,
        )
        for account_id, account_name, operation_type, total_quantity, unit in rows
    ]


@usage_router.get("/campaigns", response_model=list[CampaignOversightItemOut])
async def list_campaigns_for_oversight_route(
    _platform_admin_id: uuid.UUID = Depends(_require_usage_manage),
    session: AsyncSession = Depends(get_session),
) -> list[CampaignOversightItemOut]:
    rows = await list_campaigns_for_oversight_service(session)
    return [_to_campaign_item(campaign, account_name) for campaign, account_name in rows]


@usage_router.post("/campaigns/{campaign_id}/pause", response_model=CampaignOversightItemOut)
async def pause_campaign_route(
    campaign_id: uuid.UUID,
    platform_admin_id: uuid.UUID = Depends(_require_usage_manage),
    session: AsyncSession = Depends(get_session),
) -> CampaignOversightItemOut:
    try:
        campaign, account_name = await pause_campaign_service(
            session, campaign_id=campaign_id, platform_admin_id=platform_admin_id
        )
    except CampaignRowNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    except CampaignNotPausableError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    return _to_campaign_item(campaign, account_name)
