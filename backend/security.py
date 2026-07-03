from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def _fernet():
    key = current_app.config.get("TOKEN_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is required for Google OAuth")
    return Fernet(key.encode())


def encrypt_token(value: str) -> bytes:
    return _fernet().encrypt(value.encode())


def decrypt_token(value: bytes) -> str:
    try:
        return _fernet().decrypt(value).decode()
    except InvalidToken as exc:
        raise RuntimeError("Stored OAuth token cannot be decrypted") from exc
