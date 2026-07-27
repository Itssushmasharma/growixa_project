from functools import lru_cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError

from growixa_api.config import get_settings


@lru_cache
def _hasher() -> PasswordHasher:
    settings = get_settings()
    return PasswordHasher(
        time_cost=settings.argon2_time_cost,
        memory_cost=settings.argon2_memory_cost,
        parallelism=settings.argon2_parallelism,
    )


def hash_password(plain_password: str) -> str:
    return _hasher().hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        _hasher().verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False
    return True
