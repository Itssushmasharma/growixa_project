import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.db import get_session
from growixa_api.platform_admin.schemas import (
    AccountDetailOut,
    AccountListItemOut,
    AccountUserOut,
    SecurityEventOut,
    UpdateAccountStatusIn,
)
from growixa_api.platform_admin.services import AccountNotFoundError
from growixa_api.platform_admin.services import get_account_detail as get_account_detail_service
from growixa_api.platform_admin.services import (
    list_accounts_with_user_counts as list_accounts_service,
)
from growixa_api.platform_admin.services import (
    update_account_status as update_account_status_service,
)
from growixa_api.platform_auth.dependencies import require_platform_permission

router = APIRouter(prefix="/platform/accounts", tags=["platform_admin"])

_require_manage = require_platform_permission("platform.accounts.manage")


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
