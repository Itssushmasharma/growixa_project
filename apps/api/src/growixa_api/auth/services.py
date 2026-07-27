from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.services import record_event
from growixa_api.auth.repositories import create_refresh_token, get_refresh_token_by_hash
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
