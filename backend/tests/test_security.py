"""
Tests for core/security.py – hashing, JWT, token helpers.
Owner: Member 2 (Sufiyaan Imran)
"""

from datetime import UTC

import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_hash_and_verify():
    h = hash_password("Password1")
    assert verify_password("Password1", h)
    assert not verify_password("wrong", h)


def test_73_byte_password_rejected():
    # 73 ASCII chars = 73 bytes – bcrypt limit is 72
    long_pwd = "a" * 73
    h = hash_password("Password1")
    result = verify_password(long_pwd, h)
    assert result is False


def test_73_byte_verify_does_not_raise():
    long_pwd = "a" * 73
    h = hash_password(long_pwd[:72])
    # Must return False, never raise
    assert verify_password(long_pwd, h) is False


def test_access_token_encode_decode():
    token = create_access_token(user_id=42)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_refresh_token_has_jti():
    token = create_refresh_token(user_id=1)
    payload = decode_token(token)
    assert payload is not None
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_expired_token_returns_none():
    from datetime import datetime, timedelta

    payload = {
        "sub": "1",
        "type": "access",
        "exp": datetime.now(UTC) - timedelta(seconds=1),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    assert decode_token(token) is None


def test_wrong_type_access_used_as_refresh(client, student_user):
    access = create_access_token(student_user.id)
    r = client.post("/auth/refresh", json={"refresh_token": access})
    assert r.status_code == 401


def test_hash_token_deterministic():
    h1 = hash_token("sometoken")
    h2 = hash_token("sometoken")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex
