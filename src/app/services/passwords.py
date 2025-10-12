"""Password hashing and verification utilities (bcrypt_sha256)."""

from __future__ import annotations

from passlib.context import CryptContext

# Use pbkdf2_sha256 to avoid bcrypt backend issues in some environments
_pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd_ctx.verify(plain, hashed)
    except Exception:
        return False


__all__ = ["hash_password", "verify_password"]
