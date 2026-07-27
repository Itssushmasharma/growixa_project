import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.services import record_event
from growixa_api.auth.repositories import (
    create_refresh_token,
    get_refresh_token_by_hash,
    list_active_refresh_tokens_for_user,
)
from growixa_api.auth.security import verify_password
from growixa_api.auth.tokens import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
)
from growixa_api.users.models import User
from growixa_api.users.repositories import get_user_by_email


class InvalidCredentialsError(Exception):
    """Login failed. Deliberately raised for unknown email, wrong password, and disabled
    accounts alike — per THREAT_MODEL.md T11, none of those cases may be distinguishable
    from the response."""


class InvalidRefreshTokenError(Exception):
    """Missing, unknown, expired, already-revoked, or already-rotated (reuse detected)
    refresh token."""


class LoginResult:
    def __init__(self, user: User, access_token: str, refresh_token: str) -> None:
        self.user = user
        self.access_token = access_token
        self.refresh_token = refresh_token


async def login(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    user_agent: str | None,
    ip_address: str | None,
) -> LoginResult:
    user = await get_user_by_email(session, email)
    valid = (
        user is not None
        and user.status == "ACTIVE"
        and verify_password(password, user.password_hash)
    )

    if not valid:
        await record_event(
            session,
            actor_user_id=None,
            action="user.login_failed",
            entity_type="user",
            entity_id=user.id if user is not None else None,
            metadata={"email": email},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await session.commit()
        raise InvalidCredentialsError

    assert user is not None  # narrows for mypy; `valid` already guarantees this
    user.last_login_at = datetime.now(UTC)

    access_token = create_access_token(user.id)
    raw_refresh_token = generate_refresh_token()
    await create_refresh_token(
        session,
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=refresh_token_expiry(),
        user_agent=user_agent,
        ip_address=ip_address,
    )

    await record_event(
        session,
        actor_user_id=user.id,
        action="user.login",
        entity_type="user",
        entity_id=user.id,
        metadata={},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.commit()

    return LoginResult(user=user, access_token=access_token, refresh_token=raw_refresh_token)


async def logout(session: AsyncSession, *, raw_refresh_token: str | None) -> None:
    if raw_refresh_token is None:
        return

    token = await get_refresh_token_by_hash(session, hash_refresh_token(raw_refresh_token))
    if token is None or token.revoked_at is not None:
        return

    token.revoked_at = datetime.now(UTC)

    await record_event(
        session,
        actor_user_id=token.user_id,
        action="user.logout",
        entity_type="user",
        entity_id=token.user_id,
        metadata={},
    )
    await session.commit()


async def revoke_all_active_sessions(
    session: AsyncSession, user_id: uuid.UUID, *, reason: str
) -> None:
    """Revokes every non-revoked refresh token for a user.

    Public (not `_`-prefixed) so a future account-disable action can call it directly —
    per AUTHENTICATION.md, "disabled users... have their existing refresh tokens revoked"
    is a requirement on account disable, not just on the flows already wired up here
    (reuse detection, logout-all). Does not commit — callers control the transaction
    boundary since this is meant to compose into a larger action (e.g. disabling a user).
    """
    tokens = await list_active_refresh_tokens_for_user(session, user_id)
    if not tokens:
        return

    now = datetime.now(UTC)
    for token in tokens:
        token.revoked_at = now

    await record_event(
        session,
        actor_user_id=user_id,
        action="session.revoked",
        entity_type="user",
        entity_id=user_id,
        metadata={"reason": reason, "count": len(tokens)},
    )


async def refresh(
    session: AsyncSession,
    *,
    raw_refresh_token: str | None,
    user_agent: str | None,
    ip_address: str | None,
) -> LoginResult:
    """Rotates a refresh token: the presented one is revoked and replaced by a new one.

    Presenting a token that was already revoked by a *previous* rotation (not by logout,
    not by explicit revocation) is reuse of an already-rotated token — treated as a
    compromise signal, per AUTHENTICATION.md, and responds by revoking every session for
    that user, not just rejecting this one request.
    """
    if raw_refresh_token is None:
        raise InvalidRefreshTokenError

    token = await get_refresh_token_by_hash(session, hash_refresh_token(raw_refresh_token))
    if token is None:
        raise InvalidRefreshTokenError

    if token.revoked_at is not None:
        await revoke_all_active_sessions(
            session, token.user_id, reason="refresh_token_reuse_detected"
        )
        await session.commit()
        raise InvalidRefreshTokenError

    if token.expires_at < datetime.now(UTC):
        raise InvalidRefreshTokenError

    user = await session.get(User, token.user_id)
    if user is None or user.status != "ACTIVE":
        raise InvalidRefreshTokenError

    new_access_token = create_access_token(user.id)
    raw_new_refresh_token = generate_refresh_token()
    new_token = await create_refresh_token(
        session,
        user_id=user.id,
        token_hash=hash_refresh_token(raw_new_refresh_token),
        expires_at=refresh_token_expiry(),
        user_agent=user_agent,
        ip_address=ip_address,
    )

    token.revoked_at = datetime.now(UTC)
    token.replaced_by_token_id = new_token.id
    await session.commit()

    return LoginResult(
        user=user, access_token=new_access_token, refresh_token=raw_new_refresh_token
    )


async def logout_all(session: AsyncSession, *, raw_refresh_token: str | None) -> None:
    """Logs out every session for the user identified by the presented refresh token —
    consistent with plain `logout()`, identity comes from the token itself, not a separate
    access-token-authenticated dependency."""
    if raw_refresh_token is None:
        return

    token = await get_refresh_token_by_hash(session, hash_refresh_token(raw_refresh_token))
    if token is None:
        return

    await revoke_all_active_sessions(session, token.user_id, reason="logout_all")
    await session.commit()
