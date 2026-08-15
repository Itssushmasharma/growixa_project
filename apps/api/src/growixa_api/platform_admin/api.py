import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.ai.providers.base import AIProviderError
from growixa_api.ai.schemas import PlatformAIProviderConfigIn, PlatformAIProviderConfigOut
from growixa_api.ai.services import (
    InsecureBaseUrlError,
    MissingBaseUrlError,
    get_platform_config,
    set_platform_config,
    test_connection,
)
from growixa_api.billing.models import AccountSubscription
from growixa_api.billing.schemas import AccountSubscriptionOut, CreditBalanceOut, CreditPackOut
from growixa_api.billing.schemas import SubscriptionPlanOut as BillingSubscriptionPlanOut
from growixa_api.billing.services import get_billing_overview
from growixa_api.billing.services import (
    list_credit_pack_catalog_for_admin as list_credit_packs_service,
)
from growixa_api.billing.services import list_plan_catalog as list_plans_service
from growixa_api.campaigns.models import Campaign
from growixa_api.config import get_settings
from growixa_api.contacts.services import ContactNotFoundError, DuplicateEmailError
from growixa_api.db import get_session
from growixa_api.email_validation.providers.base import EmailValidationProviderError
from growixa_api.email_validation.providers.factory import (
    test_connection as test_validation_connection,
)
from growixa_api.email_validation.schemas import (
    PlatformEmailValidationProviderConfigIn,
    PlatformEmailValidationProviderConfigOut,
)
from growixa_api.email_validation.services import (
    get_platform_validation_config,
    set_platform_validation_config,
)
from growixa_api.health import get_queue_depths
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.notifications.schemas import (
    PlatformEmailProviderConfigIn,
    PlatformEmailProviderConfigOut,
)
from growixa_api.notifications.services import (
    get_platform_config as get_platform_email_config,
)
from growixa_api.notifications.services import (
    set_platform_config as set_platform_email_config,
)
from growixa_api.notifications.services import (
    test_platform_config_connection as test_platform_email_config,
)
from growixa_api.platform_admin.models import SupportSession
from growixa_api.platform_admin.schemas import (
    AccountDetailOut,
    AccountListItemOut,
    AccountSubscriptionOverrideIn,
    AccountUserOut,
    AuditEventOut,
    CampaignOversightItemOut,
    CouponCreateIn,
    CouponOut,
    CouponUpdateActiveIn,
    CreditPackCreateIn,
    CreditPackUpdateIn,
    FinancialMetricsOut,
    GrantCreditsIn,
    PlanDistributionItemOut,
    PlatformDashboardSummaryOut,
    QueueDepthsOut,
    SecurityEventOut,
    SubscriptionPlanCreateIn,
    SubscriptionPlanUpdateIn,
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
    CouponCodeConflictError,
    CouponMissingCreditTypeError,
    CouponNotFoundError,
    CreditPackNotFoundError,
    CreditPackSlugConflictError,
    SubscriptionOverrideMissingFieldsError,
    SubscriptionPlanNotFoundError,
    SubscriptionPlanSlugConflictError,
    SupportSessionAccessDeniedError,
    SupportSessionExpiredError,
    SupportSessionNotFoundError,
    SupportSessionWriteGateError,
    SupportSessionWriteNotPermittedError,
    get_financial_metrics,
    list_support_sessions_for_account_service,
)
from growixa_api.platform_admin.services import CampaignNotFoundError as CampaignRowNotFoundError
from growixa_api.platform_admin.services import create_coupon as create_coupon_service
from growixa_api.platform_admin.services import (
    create_credit_pack_catalog_entry as create_credit_pack_service,
)
from growixa_api.platform_admin.services import create_subscription_plan as create_plan_service
from growixa_api.platform_admin.services import end_support_session as end_support_session_service
from growixa_api.platform_admin.services import get_account_detail as get_account_detail_service
from growixa_api.platform_admin.services import (
    get_account_subscription_overview as get_account_subscription_overview_service,
)
from growixa_api.platform_admin.services import (
    get_platform_dashboard_summary as get_platform_dashboard_summary_service,
)
from growixa_api.platform_admin.services import (
    get_support_session_overview as get_support_session_overview_service,
)
from growixa_api.platform_admin.services import grant_account_credits as grant_credits_service
from growixa_api.platform_admin.services import (
    list_accounts_with_user_counts as list_accounts_service,
)
from growixa_api.platform_admin.services import (
    list_campaigns_for_oversight as list_campaigns_for_oversight_service,
)
from growixa_api.platform_admin.services import list_coupons_for_admin as list_coupons_service
from growixa_api.platform_admin.services import (
    list_usage_summary_rows as list_usage_summary_rows_service,
)
from growixa_api.platform_admin.services import (
    override_account_subscription as override_subscription_service,
)
from growixa_api.platform_admin.services import pause_campaign as pause_campaign_service
from growixa_api.platform_admin.services import set_coupon_active as set_coupon_active_service
from growixa_api.platform_admin.services import (
    start_support_session as start_support_session_service,
)
from growixa_api.platform_admin.services import (
    update_account_status as update_account_status_service,
)
from growixa_api.platform_admin.services import (
    update_contact_via_support_session as update_contact_via_support_session_service,
)
from growixa_api.platform_admin.services import (
    update_credit_pack_catalog_entry as update_credit_pack_service,
)
from growixa_api.platform_admin.services import update_subscription_plan as update_plan_service
from growixa_api.platform_auth.dependencies import require_platform_permission

router = APIRouter(prefix="/platform/accounts", tags=["platform_admin"])
usage_router = APIRouter(prefix="/platform", tags=["platform_admin"])
support_session_router = APIRouter(prefix="/platform", tags=["platform_admin"])
ai_config_router = APIRouter(prefix="/platform", tags=["platform_admin"])
billing_router = APIRouter(prefix="/platform", tags=["platform_admin"])
email_config_router = APIRouter(prefix="/platform", tags=["platform_admin"])
email_validation_config_router = APIRouter(prefix="/platform", tags=["platform_admin"])
monitoring_router = APIRouter(prefix="/platform", tags=["platform_admin"])

_require_manage = require_platform_permission("platform.accounts.manage")
_require_usage_manage = require_platform_permission("platform.usage.manage")
_require_support_session_create = require_platform_permission("platform.support_session.create")
_require_support_session_write = require_platform_permission("platform.support_session.write")
_require_ai_manage = require_platform_permission("platform.ai.manage")
_require_billing_manage = require_platform_permission("platform.billing.manage")
_require_email_manage = require_platform_permission("platform.email.manage")
_require_validation_manage = require_platform_permission("platform.validation.manage")
_require_monitoring_manage = require_platform_permission("platform.monitoring.manage")


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


def _to_subscription_out(
    subscription: AccountSubscription,
    plan: BillingSubscriptionPlanOut,
    balances: list[CreditBalanceOut],
) -> AccountSubscriptionOut:
    return AccountSubscriptionOut(
        plan=plan,
        status=subscription.status,
        currency=subscription.currency,  # type: ignore[arg-type]
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        period_email_used=subscription.period_email_used,
        period_ai_used=subscription.period_ai_used,
        credit_balances=balances,
    )


@router.get("/{account_id}/subscription", response_model=AccountSubscriptionOut)
async def get_account_subscription_route(
    account_id: uuid.UUID,
    _platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> AccountSubscriptionOut:
    try:
        subscription, plan, balances = await get_account_subscription_overview_service(
            session, account_id=account_id
        )
    except AccountNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found") from exc

    return _to_subscription_out(
        subscription,
        BillingSubscriptionPlanOut.model_validate(plan),
        [CreditBalanceOut.model_validate(b) for b in balances],
    )


@router.patch("/{account_id}/subscription", response_model=AccountSubscriptionOut)
async def override_account_subscription_route(
    account_id: uuid.UUID,
    payload: AccountSubscriptionOverrideIn,
    platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> AccountSubscriptionOut:
    """Manual plan/status override (`GRX-SAAS-006`, `BILLING_SYSTEM_ARCHITECTURE.md`
    §6.1/§6.3) -- bypasses Razorpay entirely, no payment or webhook involved. Used for
    Enterprise activation, trial extensions, support-driven upgrades/downgrades, or
    comping an account."""
    try:
        await override_subscription_service(
            session,
            account_id=account_id,
            platform_admin_id=platform_admin_id,
            plan_slug=payload.plan_slug,
            status=payload.status,
        )
    except AccountNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found") from exc
    except SubscriptionOverrideMissingFieldsError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "At least one of plan_slug/status must be provided"
        ) from exc
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found") from exc

    subscription, plan, balances = await get_billing_overview(session, account_id)
    return _to_subscription_out(
        subscription,
        BillingSubscriptionPlanOut.model_validate(plan),
        [CreditBalanceOut.model_validate(b) for b in balances],
    )


@router.post(
    "/{account_id}/credits/grant",
    response_model=CreditBalanceOut,
    status_code=status.HTTP_201_CREATED,
)
async def grant_account_credits_route(
    account_id: uuid.UUID,
    payload: GrantCreditsIn,
    platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> CreditBalanceOut:
    """Free top-up credit grant (`GRX-SAAS-006` §6.2) -- e.g. support/VIP comps.
    Distinguishable from a real purchase in the receipt history by
    `razorpay_payment_id IS NULL`/`granted_by_platform_admin_id` being set."""
    try:
        balance = await grant_credits_service(
            session,
            account_id=account_id,
            platform_admin_id=platform_admin_id,
            credit_type=payload.credit_type,
            credits=payload.credits,
        )
    except AccountNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found") from exc

    return CreditBalanceOut.model_validate(balance)


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


@usage_router.get("/dashboard/summary", response_model=PlatformDashboardSummaryOut)
async def get_platform_dashboard_summary_route(
    _platform_admin_id: uuid.UUID = Depends(_require_usage_manage),
    session: AsyncSession = Depends(get_session),
) -> PlatformDashboardSummaryOut:
    (
        total_active_accounts,
        mrr_usd,
        mrr_inr,
        emails_used,
        ai_runs_used,
        distribution_rows,
    ) = await get_platform_dashboard_summary_service(session)
    return PlatformDashboardSummaryOut(
        total_active_accounts=total_active_accounts,
        total_mrr_usd=mrr_usd,
        total_mrr_inr=mrr_inr,
        period_emails_used=emails_used,
        period_ai_runs_used=ai_runs_used,
        plan_distribution=[
            PlanDistributionItemOut(plan_slug=slug, plan_name=name, account_count=count)
            for slug, name, count in distribution_rows
        ],
    )


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


@ai_config_router.get("/ai-config", response_model=PlatformAIProviderConfigOut | None)
async def get_platform_ai_config_route(
    _platform_admin_id: uuid.UUID = Depends(_require_ai_manage),
    session: AsyncSession = Depends(get_session),
) -> PlatformAIProviderConfigOut | None:
    config = await get_platform_config(session)
    if config is None:
        return None
    return PlatformAIProviderConfigOut.model_validate(config)


@ai_config_router.put("/ai-config", response_model=PlatformAIProviderConfigOut)
async def set_platform_ai_config_route(
    payload: PlatformAIProviderConfigIn,
    platform_admin_id: uuid.UUID = Depends(_require_ai_manage),
    session: AsyncSession = Depends(get_session),
) -> PlatformAIProviderConfigOut:
    try:
        config = await set_platform_config(session, payload, platform_admin_id)
    except (MissingBaseUrlError, InsecureBaseUrlError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    await session.commit()
    return PlatformAIProviderConfigOut.model_validate(config)


@ai_config_router.post("/ai-config/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_platform_ai_config_route(
    payload: PlatformAIProviderConfigIn,
    _platform_admin_id: uuid.UUID = Depends(_require_ai_manage),
) -> None:
    """Validates credentials via a real, minimal generation call before saving —
    nothing is persisted (GRX-EMAIL-012's SMTP test-connection convention, applied
    here)."""
    try:
        await test_connection(
            provider=payload.provider,
            api_key=payload.api_key,
            base_url=payload.base_url,
            default_model=payload.default_model,
        )
    except (MissingBaseUrlError, InsecureBaseUrlError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Connection test failed: {exc}") from exc


@email_validation_config_router.get(
    "/email-validation-config", response_model=PlatformEmailValidationProviderConfigOut | None
)
async def get_platform_email_validation_config_route(
    _platform_admin_id: uuid.UUID = Depends(_require_validation_manage),
    session: AsyncSession = Depends(get_session),
) -> PlatformEmailValidationProviderConfigOut | None:
    config = await get_platform_validation_config(session)
    if config is None:
        return None
    return PlatformEmailValidationProviderConfigOut.model_validate(config)


@email_validation_config_router.put(
    "/email-validation-config", response_model=PlatformEmailValidationProviderConfigOut
)
async def set_platform_email_validation_config_route(
    payload: PlatformEmailValidationProviderConfigIn,
    platform_admin_id: uuid.UUID = Depends(_require_validation_manage),
    session: AsyncSession = Depends(get_session),
) -> PlatformEmailValidationProviderConfigOut:
    config = await set_platform_validation_config(session, payload, platform_admin_id)
    await session.commit()
    return PlatformEmailValidationProviderConfigOut.model_validate(config)


@email_validation_config_router.post(
    "/email-validation-config/test", status_code=status.HTTP_204_NO_CONTENT
)
async def test_platform_email_validation_config_route(
    payload: PlatformEmailValidationProviderConfigIn,
    _platform_admin_id: uuid.UUID = Depends(_require_validation_manage),
) -> None:
    """Validates credentials via one real verification call before saving — nothing is
    persisted (same test-before-save convention as GRX-EMAIL-012/GRX-AI-005)."""
    try:
        await test_validation_connection(provider_name=payload.provider, api_key=payload.api_key)
    except EmailValidationProviderError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Connection test failed: {exc}") from exc


@billing_router.get("/subscription-plans", response_model=list[BillingSubscriptionPlanOut])
async def list_subscription_plans_route(
    _platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> list[BillingSubscriptionPlanOut]:
    plans = await list_plans_service(session)
    return [BillingSubscriptionPlanOut.model_validate(plan) for plan in plans]


@billing_router.get("/credit-packs", response_model=list[CreditPackOut])
async def list_credit_packs_route(
    _platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> list[CreditPackOut]:
    """Unlike the customer-facing `GET /billing/credit-packs`, this is not filtered to
    `is_active` -- a platform admin editing the catalog needs to see (and reactivate)
    deactivated packs too."""
    packs = await list_credit_packs_service(session)
    return [CreditPackOut.model_validate(pack) for pack in packs]


@billing_router.post(
    "/subscription-plans",
    response_model=BillingSubscriptionPlanOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription_plan_route(
    payload: SubscriptionPlanCreateIn,
    platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> BillingSubscriptionPlanOut:
    """Creates a genuinely new plan tier (`GRX-SAAS-006` §6.4) -- not limited to editing
    the four seeded plans. A new tier isn't automatically self-serve-checkout-able
    (`POST /billing/subscribe`'s `plan_slug` stays a deliberate
    `Literal["starter", "pro"]`) until that's wired in separately."""
    try:
        plan = await create_plan_service(
            session, platform_admin_id=platform_admin_id, fields=payload.model_dump()
        )
    except SubscriptionPlanSlugConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return BillingSubscriptionPlanOut.model_validate(plan)


@billing_router.put("/subscription-plans/{plan_id}", response_model=BillingSubscriptionPlanOut)
async def update_subscription_plan_route(
    plan_id: uuid.UUID,
    payload: SubscriptionPlanUpdateIn,
    platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> BillingSubscriptionPlanOut:
    """Edits a plan's quotas/prices/features platform-wide -- affects every account on
    that plan going forward, does not retroactively touch `account_subscriptions` rows
    already mid-period (§6.4)."""
    try:
        plan = await update_plan_service(
            session,
            plan_id=plan_id,
            platform_admin_id=platform_admin_id,
            fields=payload.model_dump(),
        )
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found") from exc
    return BillingSubscriptionPlanOut.model_validate(plan)


@billing_router.post(
    "/credit-packs", response_model=CreditPackOut, status_code=status.HTTP_201_CREATED
)
async def create_credit_pack_route(
    payload: CreditPackCreateIn,
    platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> CreditPackOut:
    try:
        pack = await create_credit_pack_service(
            session, platform_admin_id=platform_admin_id, fields=payload.model_dump()
        )
    except CreditPackSlugConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return CreditPackOut.model_validate(pack)


@billing_router.put("/credit-packs/{pack_id}", response_model=CreditPackOut)
async def update_credit_pack_route(
    pack_id: uuid.UUID,
    payload: CreditPackUpdateIn,
    platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> CreditPackOut:
    try:
        pack = await update_credit_pack_service(
            session,
            pack_id=pack_id,
            platform_admin_id=platform_admin_id,
            fields=payload.model_dump(),
        )
    except CreditPackNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Credit pack not found") from exc
    return CreditPackOut.model_validate(pack)


@billing_router.get("/coupons", response_model=list[CouponOut])
async def list_coupons_route(
    _platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> list[CouponOut]:
    coupons = await list_coupons_service(session)
    return [CouponOut.model_validate(coupon) for coupon in coupons]


@billing_router.post("/coupons", response_model=CouponOut, status_code=status.HTTP_201_CREATED)
async def create_coupon_route(
    payload: CouponCreateIn,
    platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> CouponOut:
    """Percentage/fixed-amount coupons apply at `POST /billing/topup` only --
    Razorpay's Checkout.js documents no discount parameter for subscription checkout
    (`GRX-SAAS-012`, verified against Razorpay's own docs). `CREDIT_GRANT` coupons are
    redeemed via `POST /billing/redeem-coupon`."""
    try:
        coupon = await create_coupon_service(
            session, platform_admin_id=platform_admin_id, fields=payload.model_dump()
        )
    except CouponCodeConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except CouponMissingCreditTypeError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "credit_type is required for CREDIT_GRANT coupons"
        ) from exc
    return CouponOut.model_validate(coupon)


@billing_router.patch("/coupons/{coupon_id}", response_model=CouponOut)
async def set_coupon_active_route(
    coupon_id: uuid.UUID,
    payload: CouponUpdateActiveIn,
    platform_admin_id: uuid.UUID = Depends(_require_billing_manage),
    session: AsyncSession = Depends(get_session),
) -> CouponOut:
    try:
        coupon = await set_coupon_active_service(
            session,
            coupon_id=coupon_id,
            platform_admin_id=platform_admin_id,
            is_active=payload.is_active,
        )
    except CouponNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Coupon not found") from exc
    return CouponOut.model_validate(coupon)


@email_config_router.get("/email-config", response_model=PlatformEmailProviderConfigOut | None)
async def get_platform_email_config_route(
    _platform_admin_id: uuid.UUID = Depends(_require_email_manage),
    session: AsyncSession = Depends(get_session),
) -> PlatformEmailProviderConfigOut | None:
    config = await get_platform_email_config(session)
    if config is None:
        return None
    return PlatformEmailProviderConfigOut.model_validate(config)


@email_config_router.put("/email-config", response_model=PlatformEmailProviderConfigOut)
async def set_platform_email_config_route(
    payload: PlatformEmailProviderConfigIn,
    platform_admin_id: uuid.UUID = Depends(_require_email_manage),
    session: AsyncSession = Depends(get_session),
) -> PlatformEmailProviderConfigOut:
    config = await set_platform_email_config(session, payload, platform_admin_id)
    await session.commit()
    return PlatformEmailProviderConfigOut.model_validate(config)


@email_config_router.post("/email-config/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_platform_email_config_route(
    payload: PlatformEmailProviderConfigIn,
    _platform_admin_id: uuid.UUID = Depends(_require_email_manage),
) -> None:
    """Connects and authenticates with the given credentials before saving -- nothing
    is persisted, no message is sent (same convention as /platform/ai-config/test)."""
    try:
        await test_platform_email_config(payload)
    except EmailSendError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Connection test failed: {exc}") from exc


@monitoring_router.get("/monitoring/queues", response_model=QueueDepthsOut)
async def get_queue_depths_route(
    _platform_admin_id: uuid.UUID = Depends(_require_monitoring_manage),
) -> QueueDepthsOut:
    depths = await get_queue_depths(get_settings())
    return QueueDepthsOut(queues=depths)


@monitoring_router.get("/monitoring/financials", response_model=FinancialMetricsOut)
async def get_financial_metrics_route(
    _platform_admin_id: uuid.UUID = Depends(_require_monitoring_manage),
    session: AsyncSession = Depends(get_session),
) -> FinancialMetricsOut:
    metrics = await get_financial_metrics(session)
    return FinancialMetricsOut(
        mrr_by_currency=metrics.mrr_by_currency,
        arr_by_currency=metrics.arr_by_currency,
        active_subscription_count=metrics.active_subscription_count,
        churned_last_30_days=metrics.churned_last_30_days,
        churn_rate_percent=metrics.churn_rate_percent,
    )
