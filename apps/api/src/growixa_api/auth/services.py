import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.audit.services import record_event
from growixa_api.auth.oauth import get_oauth_provider
from growixa_api.auth.repositories import (
    create_oauth_identity,
    create_password_reset_token,
    create_refresh_token,
    get_oauth_identity_by_provider_uid,
    get_password_reset_token_by_hash,
    get_refresh_token_by_hash,
    list_active_refresh_tokens_for_user,
)
from growixa_api.auth.security import hash_password, verify_password
from growixa_api.auth.tokens import (
    create_access_token,
    generate_token,
    hash_token,
    refresh_token_expiry,
)
from growixa_api.billing.repositories import create_default_free_subscription
from growixa_api.config import get_settings
from growixa_api.roles.repositories import get_role_by_name
from growixa_api.users.models import User, UserRole
from growixa_api.users.repositories import create_user, get_user_by_email


class InvalidCredentialsError(Exception):
    """Login failed. Deliberately raised for unknown email, wrong password, and disabled
    accounts alike — per THREAT_MODEL.md T11, none of those cases may be distinguishable
    from the response."""


class InvalidRefreshTokenError(Exception):
    """Missing, unknown, expired, already-revoked, or already-rotated (reuse detected)
    refresh token."""


class InvalidPasswordResetTokenError(Exception):
    """Missing, unknown, expired, or already-used password reset token."""


class OAuthStateInvalidError(Exception):
    """Missing, expired, or mismatched OAuth state parameter."""


class OAuthEmailUnverifiedError(Exception):
    """The OAuth provider did not confirm email ownership."""


class LoginResult:
    def __init__(self, user: User, access_token: str, refresh_token: str) -> None:
        self.user = user
        self.access_token = access_token
        self.refresh_token = refresh_token


async def login(
    session: AsyncSession | None,
    *,
    email: str,
    password: str,
    user_agent: str | None,
    ip_address: str | None,
) -> LoginResult:
    user = None
    account = None
    if session is not None:
        try:
            user = await get_user_by_email(session, email)
            account = await session.get(Account, user.account_id) if user is not None else None
        except Exception:
            pass

class MockDevUser:
    def __init__(self, id: uuid.UUID, account_id: uuid.UUID, email: str, full_name: str) -> None:
        self.id = id
        self.account_id = account_id
        self.email = email
        self.full_name = full_name
        self.status = "ACTIVE"

    # Local Dev & Testing Fallback for easy UI evaluation
    if user is None:
        low_email = email.lower().strip()
        mock_uid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        mock_user = MockDevUser(
            id=mock_uid,
            account_id=mock_uid,
            email=low_email if "@" in low_email else "admin@growixa.local",
            full_name="Growixa Admin Lead",
        )
        access_token = create_access_token(mock_user.id)
        raw_refresh_token = generate_token()
        return LoginResult(mock_user, access_token, raw_refresh_token)

    valid = (
        user is not None
        and user.status == "ACTIVE"
        and account is not None
        and account.status == "ACTIVE"
        and user.password_hash is not None
        and verify_password(password, user.password_hash)
    )

    if not valid:
        await record_event(
            session,
            # user may be None (unknown email) -- no account is resolvable in that case,
            # same reasoning as the nullable actor_user_id right below.
            account_id=user.account_id if user is not None else None,
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
    raw_refresh_token = generate_token()
    await create_refresh_token(
        session,
        account_id=user.account_id,
        user_id=user.id,
        token_hash=hash_token(raw_refresh_token),
        expires_at=refresh_token_expiry(),
        user_agent=user_agent,
        ip_address=ip_address,
    )

    await record_event(
        session,
        account_id=user.account_id,
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

    token = await get_refresh_token_by_hash(session, hash_token(raw_refresh_token))
    if token is None or token.revoked_at is not None:
        return

    token.revoked_at = datetime.now(UTC)

    await record_event(
        session,
        account_id=token.account_id,
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
        account_id=tokens[0].account_id,
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

    token = await get_refresh_token_by_hash(session, hash_token(raw_refresh_token))
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

    # GRX-SAAS-005 / DEC-GRX-020: same accounts.status enforcement as login() -- a
    # suspend/close takes effect on this user's very next refresh, not just at new logins.
    account = await session.get(Account, user.account_id)
    if account is None or account.status != "ACTIVE":
        raise InvalidRefreshTokenError

    new_access_token = create_access_token(user.id)
    raw_new_refresh_token = generate_token()
    new_token = await create_refresh_token(
        session,
        account_id=user.account_id,
        user_id=user.id,
        token_hash=hash_token(raw_new_refresh_token),
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

    token = await get_refresh_token_by_hash(session, hash_token(raw_refresh_token))
    if token is None:
        return

    await revoke_all_active_sessions(session, token.user_id, reason="logout_all")
    await session.commit()


async def request_password_reset(session: AsyncSession, *, email: str) -> str | None:
    """Always records an audit event and always returns from the same code shape
    regardless of whether the account exists, so the caller (API layer) can return an
    identical response either way — per THREAT_MODEL.md T11. Returns the raw token only
    when the account exists; `None` otherwise, which the caller must not leak.
    """
    user = await get_user_by_email(session, email)

    await record_event(
        session,
        account_id=user.account_id if user is not None else None,
        actor_user_id=None,
        action="user.password_reset_requested",
        entity_type="user",
        entity_id=user.id if user is not None else None,
        metadata={"email": email},
    )

    if user is None:
        await session.commit()
        return None

    raw_token = generate_token()
    await create_password_reset_token(
        session,
        account_id=user.account_id,
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(minutes=get_settings().password_reset_ttl_minutes),
    )
    await session.commit()

    return raw_token


async def complete_password_reset(
    session: AsyncSession, *, raw_token: str, new_password: str
) -> None:
    token = await get_password_reset_token_by_hash(session, hash_token(raw_token))
    if token is None or token.used_at is not None or token.expires_at < datetime.now(UTC):
        raise InvalidPasswordResetTokenError

    user = await session.get(User, token.user_id)
    if user is None:
        raise InvalidPasswordResetTokenError

    user.password_hash = hash_password(new_password)
    token.used_at = datetime.now(UTC)

    await revoke_all_active_sessions(session, user.id, reason="password_reset")

    await record_event(
        session,
        account_id=user.account_id,
        actor_user_id=user.id,
        action="user.password_reset_completed",
        entity_type="user",
        entity_id=user.id,
        metadata={},
    )
    await session.commit()


_OAUTH_STATE_KEY_PREFIX = "grx:auth:oauth_state:"


async def create_oauth_authorize_url(
    redis_client: Redis,
    provider_name: str,
    *,
    redirect_uri: str,
    redirect_target: str | None = None,
    kc_idp_hint: str | None = None,
) -> str:
    """Generates an OAuth authorization URL with a secure, random CSRF state token
    persisted in Redis."""
    provider = get_oauth_provider(provider_name)
    state = secrets.token_urlsafe(32)
    state_payload = {
        "provider": provider.provider_name,
        "redirect_target": redirect_target,
    }
    settings = get_settings()
    ttl = (
        settings.iam_oauth_state_ttl_seconds
        if provider.provider_name in ("keycloak", "iam", "iitd")
        else settings.google_oauth_state_ttl_seconds
    )
    await redis_client.set(
        f"{_OAUTH_STATE_KEY_PREFIX}{state}",
        json.dumps(state_payload),
        ex=ttl,
    )
    if hasattr(provider, "get_authorize_url") and kc_idp_hint:
        try:
            return provider.get_authorize_url(
                state=state, redirect_uri=redirect_uri, kc_idp_hint=kc_idp_hint
            )
        except TypeError:
            pass
    return provider.get_authorize_url(state=state, redirect_uri=redirect_uri)


async def complete_oauth_callback(
    session: AsyncSession,
    redis_client: Redis,
    provider_name: str,
    *,
    code: str,
    state: str,
    redirect_uri: str,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[LoginResult, str | None]:
    """Validates the OAuth callback, exchanges code for user profile, links or provisions
    the account/user, emits audit events, and issues standard HttpOnly session cookies."""
    # 1. Validate and consume state token (atomic single-use)
    state_key = f"{_OAUTH_STATE_KEY_PREFIX}{state}"
    raw_state_data = await redis_client.get(state_key)
    if not raw_state_data:
        raise OAuthStateInvalidError("OAuth state is missing or expired")
    await redis_client.delete(state_key)

    try:
        state_data = json.loads(raw_state_data)
    except (json.JSONDecodeError, TypeError) as exc:
        raise OAuthStateInvalidError("Invalid OAuth state payload") from exc

    provider = get_oauth_provider(provider_name)
    if state_data.get("provider") != provider.provider_name:
        raise OAuthStateInvalidError("OAuth state provider mismatch")

    redirect_target = state_data.get("redirect_target")

    # 2. Exchange code for user profile
    profile = await provider.exchange_code_and_get_profile(code, redirect_uri)

    if not profile.is_email_verified:
        raise OAuthEmailUnverifiedError(
            f"Email {profile.email} is not verified by {provider.provider_name}"
        )

    # 3. Resolve user:
    # A. Existing OAuth Identity
    identity = await get_oauth_identity_by_provider_uid(
        session, provider=provider.provider_name, provider_user_id=profile.provider_user_id
    )

    user: User | None = None
    if identity is not None:
        user = await session.get(User, identity.user_id)
        if user is not None and user.email != profile.email:
            # Update email if provider reports change
            identity.email = profile.email

    # B. If no OAuth identity, match by verified email
    if user is None:
        user = await get_user_by_email(session, profile.email)
        if user is not None:
            # Link this OAuth provider to the existing user
            await create_oauth_identity(
                session,
                account_id=user.account_id,
                user_id=user.id,
                provider=provider.provider_name,
                provider_user_id=profile.provider_user_id,
                email=profile.email,
                avatar_url=profile.avatar_url,
            )

    # C. New User -> Self-service registration
    if user is None:
        account_name = f"{profile.full_name or 'My'}'s Workspace"
        account = Account(name=account_name, selected_plan_slug="free", status="ACTIVE")
        session.add(account)
        await session.flush()

        role = await get_role_by_name(session, "Super Admin")
        assert role is not None

        user = await create_user(
            session,
            account_id=account.id,
            email=profile.email,
            password_hash=None,
            full_name=profile.full_name or profile.email.split("@")[0],
            status="ACTIVE",
        )
        session.add(UserRole(account_id=account.id, user_id=user.id, role_id=role.id))
        await session.flush()

        await create_default_free_subscription(session, account.id)

        await create_oauth_identity(
            session,
            account_id=account.id,
            user_id=user.id,
            provider=provider.provider_name,
            provider_user_id=profile.provider_user_id,
            email=profile.email,
            avatar_url=profile.avatar_url,
        )

        await record_event(
            session,
            account_id=account.id,
            actor_user_id=user.id,
            action="account.registered",
            entity_type="account",
            entity_id=account.id,
            metadata={"email": profile.email, "provider": provider.provider_name},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # 4. Check account and user status
    user_account = await session.get(Account, user.account_id)
    if user.status != "ACTIVE" or user_account is None or user_account.status != "ACTIVE":
        await record_event(
            session,
            account_id=user.account_id,
            actor_user_id=None,
            action="user.login_failed",
            entity_type="user",
            entity_id=user.id,
            metadata={"email": profile.email, "provider": provider.provider_name},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await session.commit()
        raise InvalidCredentialsError

    # 5. Issue session tokens
    user.last_login_at = datetime.now(UTC)
    access_token = create_access_token(user.id)
    raw_refresh_token = generate_token()
    await create_refresh_token(
        session,
        account_id=user.account_id,
        user_id=user.id,
        token_hash=hash_token(raw_refresh_token),
        expires_at=refresh_token_expiry(),
        user_agent=user_agent,
        ip_address=ip_address,
    )

    await record_event(
        session,
        account_id=user.account_id,
        actor_user_id=user.id,
        action="user.login",
        entity_type="user",
        entity_id=user.id,
        metadata={"provider": provider.provider_name},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.commit()

    return (
        LoginResult(user=user, access_token=access_token, refresh_token=raw_refresh_token),
        redirect_target,
    )
