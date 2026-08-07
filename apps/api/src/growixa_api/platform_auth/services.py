from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.security import verify_password
from growixa_api.platform_auth.models import PlatformAdmin
from growixa_api.platform_auth.repositories import get_platform_admin_by_email
from growixa_api.platform_auth.tokens import create_platform_access_token


class InvalidPlatformCredentialsError(Exception):
    """Login failed. Deliberately raised for unknown email, wrong password, and
    disabled admins alike -- same non-distinguishable-error posture as customer login,
    per THREAT_MODEL.md T11/T22."""


class PlatformLoginResult:
    def __init__(self, admin: PlatformAdmin, access_token: str) -> None:
        self.admin = admin
        self.access_token = access_token


async def login(session: AsyncSession, *, email: str, password: str) -> PlatformLoginResult:
    admin = await get_platform_admin_by_email(session, email)
    valid = (
        admin is not None
        and admin.status == "ACTIVE"
        and verify_password(password, admin.password_hash)
    )

    if not valid:
        raise InvalidPlatformCredentialsError

    assert admin is not None  # narrows for mypy; `valid` already guarantees this
    admin.last_login_at = datetime.now(UTC)
    access_token = create_platform_access_token(admin.id)
    await session.commit()

    return PlatformLoginResult(admin=admin, access_token=access_token)
