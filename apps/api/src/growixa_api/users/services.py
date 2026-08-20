import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.repositories import get_account_name
from growixa_api.audit.services import record_event
from growixa_api.auth.security import hash_password
from growixa_api.auth.services import revoke_all_active_sessions
from growixa_api.auth.tokens import generate_token, hash_token
from growixa_api.billing.services import check_plan_limit
from growixa_api.config import get_settings
from growixa_api.roles.repositories import get_role_by_name
from growixa_api.users.models import User, UserInvitation, UserRole
from growixa_api.users.repositories import (
    count_active_users,
    create_invitation,
    create_user,
    get_invitation_by_token_hash,
    get_user_by_email,
    get_user_by_id,
    list_role_names_by_user_id,
    list_role_names_for_user,
    list_users,
    replace_user_role,
)


class RoleNotFoundError(Exception):
    """The requested role name doesn't match any seeded role."""


class InvalidInvitationError(Exception):
    """Missing, unknown, expired, or already-accepted invitation token — deliberately one
    exception for all three, matching the same non-distinguishable-error posture used for
    login (THREAT_MODEL.md T11) and refresh-token reuse."""


class EmailAlreadyRegisteredError(Exception):
    """The email already has a user account — checked both when creating an invitation
    (fail fast for the admin) and when accepting one (closes a race between two
    acceptances, or the person registering some other way in between)."""


class UserNotFoundError(Exception):
    """The target user id doesn't match any existing user."""


class SelfActionNotAllowedError(Exception):
    """An admin may not disable their own account through this endpoint — with no
    seed_first_admin CLI yet (GRX-AUTH-001), a self-disable would be an unrecoverable
    lockout if it happened to be the only remaining admin."""


@dataclass(frozen=True)
class InvitationCreated:
    """Everything the caller needs to both answer the request and send the invitation
    email, resolved here rather than in the route: this function already holds the
    session and has looked the role up, so re-fetching the account and inviter upstream
    would just duplicate queries the service is better placed to make."""

    invitation: UserInvitation
    raw_token: str
    account_name: str
    invited_by_name: str
    role_name: str


async def invite_user(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    email: str,
    role_name: str,
    invited_by_user_id: uuid.UUID,
) -> InvitationCreated:
    role = await get_role_by_name(session, role_name)
    if role is None:
        raise RoleNotFoundError

    if await get_user_by_email(session, email) is not None:
        raise EmailAlreadyRegisteredError

    raw_token = generate_token()
    expires_at = datetime.now(UTC) + timedelta(days=get_settings().invitation_ttl_days)
    invitation = await create_invitation(
        session,
        account_id=account_id,
        email=email,
        token_hash=hash_token(raw_token),
        role_id=role.id,
        invited_by_user_id=invited_by_user_id,
        expires_at=expires_at,
    )
    await session.commit()

    inviter = await get_user_by_id(session, invited_by_user_id, account_id=account_id)
    account_name = await get_account_name(session, account_id)

    return InvitationCreated(
        invitation=invitation,
        raw_token=raw_token,
        # Both fall back rather than failing: the invitation is already committed at this
        # point, so a missing display name must not turn a successful invite into an error.
        account_name=account_name or "your team",
        invited_by_name=inviter.full_name if inviter is not None else "An administrator",
        role_name=role.name,
    )


async def accept_invitation(
    session: AsyncSession,
    *,
    raw_token: str,
    password: str,
    full_name: str,
) -> User:
    invitation = await get_invitation_by_token_hash(session, hash_token(raw_token))
    if invitation is None:
        raise InvalidInvitationError
    if invitation.accepted_at is not None:
        raise InvalidInvitationError
    if invitation.expires_at < datetime.now(UTC):
        raise InvalidInvitationError

    if await get_user_by_email(session, invitation.email) is not None:
        raise EmailAlreadyRegisteredError

    current_count = await count_active_users(session, invitation.account_id)
    await check_plan_limit(
        session,
        account_id=invitation.account_id,
        limit_attr="max_user_seats",
        current_count=current_count,
        resource="user_seats",
    )

    user = await create_user(
        session,
        account_id=invitation.account_id,
        email=invitation.email,
        password_hash=hash_password(password),
        full_name=full_name,
    )
    session.add(
        UserRole(
            account_id=invitation.account_id,
            user_id=user.id,
            role_id=invitation.role_id,
            assigned_by_user_id=invitation.invited_by_user_id,
        )
    )
    invitation.accepted_at = datetime.now(UTC)

    await record_event(
        session,
        account_id=invitation.account_id,
        actor_user_id=user.id,
        action="invitation.accepted",
        entity_type="user_invitation",
        entity_id=invitation.id,
        metadata={"email": invitation.email},
    )
    await session.commit()

    return user


async def list_users_with_roles(
    session: AsyncSession, *, account_id: uuid.UUID
) -> list[tuple[User, list[str]]]:
    users = await list_users(session, account_id=account_id)
    role_map = await list_role_names_by_user_id(session, account_id=account_id)
    return [(user, role_map.get(user.id, [])) for user in users]


async def update_user_status(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    user_id: uuid.UUID,
    status: str,
) -> tuple[User, list[str]]:
    if user_id == actor_id and status == "DISABLED":
        raise SelfActionNotAllowedError

    user = await get_user_by_id(session, user_id, account_id=account_id)
    if user is None:
        raise UserNotFoundError

    user.status = status
    if status == "DISABLED":
        # Per AUTHENTICATION.md's account-disable requirement — reuses the same function
        # GRX-AUTH-003's reuse-detection and logout-all flows already call, which itself
        # emits the session.revoked audit event.
        await revoke_all_active_sessions(session, user.id, reason="account_disabled")

    await session.commit()
    roles = await list_role_names_for_user(session, user.id)
    return user, roles


async def update_user_role(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    user_id: uuid.UUID,
    role_name: str,
) -> tuple[User, list[str]]:
    user = await get_user_by_id(session, user_id, account_id=account_id)
    if user is None:
        raise UserNotFoundError

    role = await get_role_by_name(session, role_name)
    if role is None:
        raise RoleNotFoundError

    old_roles = await list_role_names_for_user(session, user_id)
    await replace_user_role(
        session,
        account_id=account_id,
        user_id=user_id,
        role_id=role.id,
        assigned_by_user_id=actor_id,
    )

    await record_event(
        session,
        account_id=account_id,
        actor_user_id=actor_id,
        action="role.changed",
        entity_type="user",
        entity_id=user_id,
        metadata={"old_roles": old_roles, "new_role": role_name},
    )
    await session.commit()

    return user, [role_name]
