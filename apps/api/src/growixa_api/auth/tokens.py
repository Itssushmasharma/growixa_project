import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from growixa_api.config import get_settings

_JWT_ALGORITHM = "HS256"


def create_access_token(user_id: uuid.UUID) -> str:
    """Issues the JWT that permissions.dependencies.get_current_user_id verifies.

    Same signing key/algorithm as that verify-side code (GRX-RBAC-001) — this is the
    issuing half of the same token.
    """
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_ttl_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire}, settings.jwt_signing_key, algorithm=_JWT_ALGORITHM
    )


def generate_token() -> str:
    """A high-entropy opaque token — used for refresh tokens, invitation tokens, and (once
    GRX-AUTH-005 lands) password-reset tokens alike; see AUTHENTICATION.md's token model."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    # These tokens are high-entropy already (T6) — a fast, deterministic hash is fine for
    # lookup-by-hash; unlike passwords, there is no brute-forceable low-entropy input here.
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days)
