"""
Authentication & JWT handler for Vouge.AI.
Provides password hashing/verification, JWT creation/decoding,
and secure refresh token generation.
"""
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Tuple

import bcrypt
import jwt

from app.config import settings


# ── Password utilities ────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hashes a plain-text password with bcrypt (cost factor 12)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plain-text password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def validate_password_strength(password: str) -> None:
    """
    Enforces minimum password requirements.
    Raises ValueError with a descriptive message on failure.
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        raise ValueError("Password must contain at least one special character.")


# ── JWT utilities ─────────────────────────────────────────────────────────────

def create_access_token(user_id: str, email: str) -> str:
    """
    Creates a signed HS256 JWT access token.

    Payload:
      sub   — user UUID string
      email — user email address
      type  — "access"
      exp   — expiry timestamp
      iat   — issued-at timestamp
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decodes and verifies a JWT access token.

    Raises:
      jwt.ExpiredSignatureError  — token has expired
      jwt.InvalidTokenError      — token is malformed or invalid signature
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def create_refresh_token() -> Tuple[str, str]:
    """
    Generates a cryptographically secure refresh token pair.

    Returns:
      (raw_token, token_hash) where:
        raw_token  — 64-byte hex string sent to the client ONCE
        token_hash — SHA-256 hex digest stored in the database
    """
    raw_token = secrets.token_hex(64)
    token_hash = _sha256(raw_token)
    return raw_token, token_hash


def get_token_hash(raw_token: str) -> str:
    """Returns SHA-256 hex digest of a raw refresh token string."""
    return _sha256(raw_token)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
