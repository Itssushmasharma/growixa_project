import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.campaigns.models import Campaign
from growixa_api.contacts.services import ContactNotFoundError, DuplicateEmailError
from growixa_api.db import get_session
from growixa_api.platform_admin.models import SupportSession
from growixa_api.platform_admin.schemas import (
    AccountDetailOut,
    AccountListItemOut,
    AccountUserOut,
    AuditEventOut,
    CampaignOversightItemOut,
    SecurityEventOut,
    SupportSessionCompanyOut,
    SupportSessionContactOut,
    SupportSessionContactUpdateIn,
    SupportSessionCreateIn,
    SupportSessionOut,
    SupportSessionOverviewOut,
    UpdateAccountStatusIn,
    UsageSummaryItemOut,
)
from growixa_api.platform_admin.services import (
    AccountNotFoundError,
    CampaignNotPausableError,
    SupportSessionAccessDeniedError,
    SupportSessionExpiredError,
    SupportSessionNotFoundError,
    SupportSessionWriteGateError,
    SupportSessionWriteNotPermittedError,
    list_support_sessions_for_account_service,
)
from growixa_api.platform_admin.services import CampaignNotFoundError as CampaignRowNotFoundError
from growixa_api.platform_admin.services import end_support_session as end_support_session_service
from growixa_api.platform_admin.services import get_account_detail as get_account_detail_service
from growixa_api.platform_admin.services import (
    get_support_session_overview as get_support_session_overview_service,
)
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
    start_support_session as start_support_session_service,
)
from growixa_api.platform_admin.services import (
    update_account_status as update_account_status_service,
)
from growixa_api.platform_admin.services import (
    update_contact_via_support_session as update_contact_via_support_session_service,
)
from growixa_api.platform_auth.dependencies import require_platform_permission

router = APIRouter(prefix="/platform/accounts", tags=["platform_admin"])
usage_router = APIRouter(prefix="/platform", tags=["platform_admin"])
support_session_router = APIRouter(prefix="/platform", tags=["platform_admin"])

_require_manage = require_platform_permission("platform.accounts.manage")
_require_usage_manage = require_platform_permission("platform.usage.manage")
_require_support_session_create = require_platform_permission("platform.support_session.create")
_require_support_session_write = require_platform_permission("platform.support_session.write")


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


def _to_session_out(support_session: SupportSession) -> SupportSessionOut:
    return SupportSessionOut(
        id=support_session.id,
        account_id=support_session.account_id,
        platform_admin_id=support_session.platform_admin_id,
        reason=support_session.reason,
        ticket_number=support_session.ticket_number,
        access_level=support_session.access_level,
        started_at=support_session.started_at,
        expires_at=support_session.expires_at,
        ended_at=support_session.ended_at,
    )


@router.post(
    "/{account_id}/support-sessions",
    response_model=SupportSessionOut,
    status_code=status.HTTP_201_CREATED,
)
async def start_support_session_route(
    account_id: uuid.UUID,
    payload: SupportSessionCreateIn,
    platform_admin_id: uuid.UUID = Depends(_require_support_session_create),
    session: AsyncSession = Depends(get_session),
) -> SupportSessionOut:
    try:
        support_session = await start_support_session_service(
            session,
            account_id=account_id,
            platform_admin_id=platform_admin_id,
            reason=payload.reason,
            ticket_number=payload.ticket_number,
            access_level=payload.access_level,
        )
    except AccountNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found") from exc
    except SupportSessionWriteNotPermittedError as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "platform.support_session.write is required to start a WRITE-access session",
        ) from exc

    return _to_session_out(support_session)


@router.get("/{account_id}/support-sessions", response_model=list[SupportSessionOut])
async def list_support_sessions_route(
    account_id: uuid.UUID,
    _platform_admin_id: uuid.UUID = Depends(_require_support_session_create),
    session: AsyncSession = Depends(get_session),
) -> list[SupportSessionOut]:
    try:
        sessions = await list_support_sessions_for_account_service(session, account_id)
    except AccountNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found") from exc

    return [_to_session_out(support_session) for support_session in sessions]


def _map_session_lookup_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SupportSessionNotFoundError | SupportSessionAccessDeniedError):
        # Same 404 for "doesn't exist" and "belongs to someone else" -- a session id
        # alone must never let a caller distinguish the two (THREAT_MODEL.md T38).
        return HTTPException(status.HTTP_404_NOT_FOUND, "Support session not found")
    return HTTPException(status.HTTP_410_GONE, "Support session has expired or ended")


@support_session_router.post(
    "/support-sessions/{support_session_id}/end", response_model=SupportSessionOut
)
async def end_support_session_route(
    support_session_id: uuid.UUID,
    platform_admin_id: uuid.UUID = Depends(_require_support_session_create),
    session: AsyncSession = Depends(get_session),
) -> SupportSessionOut:
    try:
        support_session = await end_support_session_service(
            session, support_session_id=support_session_id, platform_admin_id=platform_admin_id
        )
    except (
        SupportSessionNotFoundError,
        SupportSessionAccessDeniedError,
        SupportSessionExpiredError,
    ) as exc:
        raise _map_session_lookup_error(exc) from exc

    return _to_session_out(support_session)


@support_session_router.get(
    "/support-sessions/{support_session_id}/overview", response_model=SupportSessionOverviewOut
)
async def get_support_session_overview_route(
    support_session_id: uuid.UUID,
    platform_admin_id: uuid.UUID = Depends(_require_support_session_create),
    session: AsyncSession = Depends(get_session),
) -> SupportSessionOverviewOut:
    try:
        (
            support_session,
            company,
            contacts,
            audit_events,
        ) = await get_support_session_overview_service(
            session, support_session_id=support_session_id, platform_admin_id=platform_admin_id
        )
    except (
        SupportSessionNotFoundError,
        SupportSessionAccessDeniedError,
        SupportSessionExpiredError,
    ) as exc:
        raise _map_session_lookup_error(exc) from exc

    return SupportSessionOverviewOut(
        session=_to_session_out(support_session),
        company=(
            SupportSessionCompanyOut(
                name=company.name, website=company.website, industry=company.industry
            )
            if company is not None
            else None
        ),
        contacts=[
            SupportSessionContactOut(
                id=contact.id,
                email=contact.email,
                first_name=contact.first_name,
                last_name=contact.last_name,
                phone=contact.phone,
                status=contact.status,
            )
            for contact, _fields, _tags, _suppressed in contacts
        ],
        audit_events=[
            AuditEventOut(
                id=event.id,
                action=event.action,
                entity_type=event.entity_type,
                actor_user_id=event.actor_user_id,
                event_metadata=event.event_metadata,
                created_at=event.created_at,
            )
            for event in audit_events
        ],
    )


@support_session_router.patch(
    "/support-sessions/{support_session_id}/contacts/{contact_id}",
    response_model=SupportSessionContactOut,
)
async def update_contact_via_support_session_route(
    support_session_id: uuid.UUID,
    contact_id: uuid.UUID,
    payload: SupportSessionContactUpdateIn,
    platform_admin_id: uuid.UUID = Depends(_require_support_session_write),
    session: AsyncSession = Depends(get_session),
) -> SupportSessionContactOut:
    try:
        contact, _fields, _tags, _suppressed = await update_contact_via_support_session_service(
            session,
            support_session_id=support_session_id,
            platform_admin_id=platform_admin_id,
            contact_id=contact_id,
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
        )
    except (
        SupportSessionNotFoundError,
        SupportSessionAccessDeniedError,
        SupportSessionExpiredError,
    ) as exc:
        raise _map_session_lookup_error(exc) from exc
    except SupportSessionWriteGateError as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "This session does not have write access"
        ) from exc
    except ContactNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found") from exc
    except DuplicateEmailError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A contact with this email already exists"
        ) from exc

    return SupportSessionContactOut(
        id=contact.id,
        email=contact.email,
        first_name=contact.first_name,
        last_name=contact.last_name,
        phone=contact.phone,
        status=contact.status,
    )
