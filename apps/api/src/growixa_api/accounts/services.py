from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.accounts.repositories import (
    create_account_verification_token,
    get_account_verification_token_by_hash,
)
from growixa_api.audit.services import record_event
from growixa_api.auth.security import hash_password
from growixa_api.auth.tokens import generate_token, hash_token
from growixa_api.config import get_settings
from growixa_api.roles.repositories import get_role_by_name
from growixa_api.users.models import User, UserRole
from growixa_api.users.repositories import create_user, get_user_by_email


class EmailAlreadyRegisteredError(Exception):
    """The email already belongs to a user in some account -- users.email is globally
    unique across accounts by design (GRX-SAAS-001, confirmed for registration by
    DEC-GRX-019), same error shape as invite_user/accept_invitation."""


class InvalidVerificationTokenError(Exception):
    """Missing, unknown, expired, or already-used verification token -- one
    non-distinguishable exception for all cases, same posture as password-reset and
    invitation tokens."""


class RegisterResult:
    def __init__(self, account: Account, user: User) -> None:
        self.account = account
        self.user = user


async def register(
    session: AsyncSession,
    *,
    account_name: str,
    full_name: str,
    email: str,
    password: str,
    plan_slug: str,
) -> tuple[RegisterResult, str]:
    """Creates a new account and its first (owner) user, PENDING_VERIFICATION until
    the returned raw token is consumed by verify_email(). Never sets an auth cookie --
    that's a separate, later /auth/login call, per Phase C's own acceptance criteria
    ("register, verify... and log in" as three distinct steps)."""
    if await get_user_by_email(session, email) is not None:
        raise EmailAlreadyRegisteredError

    account = Account(name=account_name, selected_plan_slug=plan_slug)
    session.add(account)
    await session.flush()

    # Seeded role, same one Sprint 1's own first admin holds -- see DEC-GRX-019 for why
    # this isn't a new "customer.owner" role.
    role = await get_role_by_name(session, "Super Admin")
    assert role is not None

    user = await create_user(
        session,
        account_id=account.id,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        status="PENDING_VERIFICATION",
    )
    session.add(UserRole(account_id=account.id, user_id=user.id, role_id=role.id))
    await session.flush()

    raw_token = generate_token()
    expires_at = datetime.now(UTC) + timedelta(hours=get_settings().email_verification_ttl_hours)
    await create_account_verification_token(
        session,
        account_id=account.id,
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=expires_at,
    )

    await record_event(
        session,
        account_id=account.id,
        actor_user_id=user.id,
        action="account.registered",
        entity_type="account",
        entity_id=account.id,
        metadata={"email": email, "plan_slug": plan_slug},
    )
    await session.commit()

    return RegisterResult(account=account, user=user), raw_token


async def verify_email(session: AsyncSession, *, raw_token: str) -> None:
    token = await get_account_verification_token_by_hash(session, hash_token(raw_token))
    if token is None or token.used_at is not None or token.expires_at < datetime.now(UTC):
        raise InvalidVerificationTokenError

    user = await session.get(User, token.user_id)
    if user is None:
        raise InvalidVerificationTokenError

    user.status = "ACTIVE"
    token.used_at = datetime.now(UTC)

    await record_event(
        session,
        account_id=token.account_id,
        actor_user_id=user.id,
        action="user.email_verified",
        entity_type="user",
        entity_id=user.id,
        metadata={},
    )
    await session.commit()
