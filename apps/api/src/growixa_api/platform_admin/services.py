import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.audit.models import AuditLog
from growixa_api.audit.services import list_events, record_event
from growixa_api.auth.services import revoke_all_active_sessions
from growixa_api.platform_admin.repositories import (
    count_users_by_account,
    get_account_by_id,
    list_accounts,
)
from growixa_api.platform_auth.models import PlatformAdmin
from growixa_api.users.models import User
from growixa_api.users.repositories import list_users

# "Login/security activity" (GRX-SAAS-005) is a filtered view over the existing
# audit_logs table, not a new table or a raw dump -- a busy account's audit_logs also
# carries non-security business events (contact edits, campaign sends, ...) that would
# bury the actual signal. See DEC-GRX-020 point 4.
_SECURITY_ACTIONS = frozenset(
    {
        "user.login",
        "user.login_failed",
        "user.logout",
        "session.revoked",
        "user.password_reset_requested",
        "user.password_reset_completed",
        "role.changed",
        "account.registered",
        "user.email_verified",
        "account.suspended",
        "account.reactivated",
        "account.closed",
    }
)

_STATUS_TO_ACTION = {
    "ACTIVE": "account.reactivated",
    "SUSPENDED": "account.suspended",
    "CLOSED": "account.closed",
}


class AccountNotFoundError(Exception):
    """The target account id doesn't match any existing account."""


async def list_accounts_with_user_counts(session: AsyncSession) -> list[tuple[Account, int]]:
    accounts = await list_accounts(session)
    counts = await count_users_by_account(session)
    return [(account, counts.get(account.id, 0)) for account in accounts]


async def get_account_detail(
    session: AsyncSession, *, account_id: uuid.UUID
) -> tuple[Account, list[User], list[AuditLog]]:
    account = await get_account_by_id(session, account_id)
    if account is None:
        raise AccountNotFoundError

    users = await list_users(session, account_id=account_id)
    events = await list_events(session, account_id=account_id, limit=100)
    security_events = [event for event in events if event.action in _SECURITY_ACTIONS]
    return account, list(users), security_events


async def update_account_status(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    platform_admin_id: uuid.UUID,
    status: str,
) -> tuple[Account, int]:
    account = await get_account_by_id(session, account_id)
    if account is None:
        raise AccountNotFoundError

    account.status = status
    users = await list_users(session, account_id=account_id)

    # Per DEC-GRX-020: a suspend/close takes effect immediately, not just at each user's
    # next token refresh -- mirrors GRX-USER-002's existing per-user disable behavior,
    # now applied to every user in the account at once.
    if status in ("SUSPENDED", "CLOSED"):
        for user in users:
            await revoke_all_active_sessions(session, user.id, reason=f"account_{status.lower()}")

    # audit_logs.actor_user_id FKs to users.id and cannot reference platform_admins.id --
    # per DEC-GRX-020, the acting admin is recorded in metadata instead, same
    # actor_user_id=None shape login() already uses for an unresolvable actor.
    admin = await session.get(PlatformAdmin, platform_admin_id)
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=None,
        action=_STATUS_TO_ACTION[status],
        entity_type="account",
        entity_id=account_id,
        metadata={
            "platform_admin_id": str(platform_admin_id),
            "platform_admin_email": admin.email if admin is not None else None,
        },
    )
    await session.commit()

    return account, len(users)
