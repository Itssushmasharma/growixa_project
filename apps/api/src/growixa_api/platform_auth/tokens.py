import uuid
from datetime import UTC, datetime, timedelta

import jwt

from growixa_api.config import get_settings

_JWT_ALGORITHM = "HS256"


def create_platform_access_token(platform_admin_id: uuid.UUID) -> str:
    """Issues the JWT that platform_auth.dependencies.get_current_platform_admin_id
    verifies.

    Deliberately a separate function from auth.tokens.create_access_token -- same JWT
    shape and signing key, but kept independent so platform_auth never imports from
    auth for anything identity/token-relevant, matching GRX-SAAS-002's structural-
    separation requirement (RBAC.md's Sprint 5 Phase B section, THREAT_MODEL.md T21).
    """
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_ttl_minutes)
    return jwt.encode(
        {"sub": str(platform_admin_id), "exp": expire},
        settings.jwt_signing_key,
        algorithm=_JWT_ALGORITHM,
    )
