from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from growixa_worker.config import get_settings


@lru_cache
def _fernet() -> Fernet:
    return Fernet(get_settings().encryption_key.encode())


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt secret — wrong key or corrupted value") from exc


def encrypt_secret(plaintext: str) -> str:
    """Needed by GRX-SOCIAL-008's inline token-refresh check -- unlike campaigns
    (decrypt-only, never writes credentials back), the worker re-encrypts a refreshed
    Instagram access token before writing it back to social_connections."""
    return _fernet().encrypt(plaintext.encode()).decode()
