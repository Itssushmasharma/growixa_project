import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.services import record_event
from growixa_api.auth.security import hash_password
from growixa_api.auth.tokens import generate_token, hash_token
from growixa_api.config import get_settings
from growixa_api.roles.repositories import get_role_by_name
from growixa_api.users.models import User, UserInvitation, UserRole
from growixa_api.users.repositories import (
    create_invitation,
    create_user,
    get_invitation_by_token_hash,
    get_user_by_email,
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


async def invite_user(
    session: AsyncSession,
    *,
    email: str,
    role_name: str,
    invited_by_user_id: uuid.UUID,
) -> tuple[UserInvitation, str]:
    role = await get_role_by_name(session, role_name)
    if role is None:
        raise RoleNotFoundError

    if await get_user_by_email(session, email) is not None:
        raise EmailAlreadyRegisteredError

    raw_token = generate_token()
    expires_at = datetime.now(UTC) + timedelta(days=get_settings().invitation_ttl_days)
    invitation = await create_invitation(
        session,
        email=email,
        token_hash=hash_token(raw_token),
        role_id=role.id,
        invited_by_user_id=invited_by_user_id,
        expires_at=expires_at,
    )
    await session.commit()

    return invitation, raw_token


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

    user = await create_user(
        session,
        email=invitation.email,
        password_hash=hash_password(password),
        full_name=full_name,
    )
    session.add(
        UserRole(
            user_id=user.id,
            role_id=invitation.role_id,
            assigned_by_user_id=invitation.invited_by_user_id,
        )
    )
    invitation.accepted_at = datetime.now(UTC)

    await record_event(
        session,
        actor_user_id=user.id,
        action="invitation.accepted",
        entity_type="user_invitation",
        entity_id=invitation.id,
        metadata={"email": invitation.email},
    )
    await session.commit()

    return user
