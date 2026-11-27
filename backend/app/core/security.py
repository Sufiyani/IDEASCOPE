"""
IdeaScope – JWT creation/verification and bcrypt password hashing.
Owner: Member 2 (Sufiyaan Imran)

Uses pyjwt (import jwt) and bcrypt 5.0.0.
"""

from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from app.core.config import settings


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash; never raises."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        # bcrypt raises ValueError for passwords > 72 bytes
        return False


# ── Token helpers ─────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int) -> str:
    """Create a signed JWT access token."""
    exp = _now_utc() + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": exp,
        "iat": _now_utc(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> str:
    """Create a signed JWT refresh token with a unique jti claim."""
    exp = _now_utc() + timedelta(days=settings.refresh_token_days)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": secrets.token_hex(16),
        "exp": exp,
        "iat": _now_utc(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT; return payload dict or None on any error."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        return None


def hash_token(token: str) -> str:
    """Return a SHA-256 hex digest of the token (for safe DB storage)."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_temp_password() -> str:
    """Return a 12-character random password using letters and digits."""
    alphabet = string.ascii_letters + string.digits
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(12))
        # Ensure at least one letter and one digit
        if any(c.isalpha() for c in pwd) and any(c.isdigit() for c in pwd):
            return pwd
