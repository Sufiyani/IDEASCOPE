"""
Tests for auth endpoints.
Owner: Member 2 (Sufiyaan Imran)
"""

import pytest

from app.core.constants import MAX_FAILED_LOGINS


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_success(client, student_user):
    r = client.post("/auth/login", json={"username": student_user.username, "password": "Password1"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data


def test_login_wrong_password(client, student_user):
    r = client.post("/auth/login", json={"username": student_user.username, "password": "wrong"})
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_credentials"


def test_login_unknown_user(client):
    r = client.post("/auth/login", json={"username": "nobody", "password": "Password1"})
    assert r.status_code == 401


def test_lockout_after_max_failures(client, student_user):
    for _ in range(MAX_FAILED_LOGINS):
        r = client.post(
            "/auth/login", json={"username": student_user.username, "password": "wrong"}
        )
        assert r.status_code == 401

    # Even the correct password now returns 423
    r = client.post(
        "/auth/login", json={"username": student_user.username, "password": "Password1"}
    )
    assert r.status_code == 423
    assert r.json()["detail"] == "account_locked"


def test_refresh_rotation(client, student_user):
    login = client.post(
        "/auth/login", json={"username": student_user.username, "password": "Password1"}
    )
    tokens = login.json()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    new_tokens = r.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


def test_refresh_reuse_fails(client, student_user):
    login = client.post(
        "/auth/login", json={"username": student_user.username, "password": "Password1"}
    )
    old_refresh = login.json()["refresh_token"]

    # Use it once
    client.post("/auth/refresh", json={"refresh_token": old_refresh})

    # Using the old one again must fail
    r = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 401


def test_logout(client, student_user, student_token):
    login = client.post(
        "/auth/login", json={"username": student_user.username, "password": "Password1"}
    )
    refresh = login.json()["refresh_token"]
    r = client.post(
        "/auth/logout",
        json={"refresh_token": refresh},
        headers=_auth(student_token),
    )
    assert r.status_code == 204

    # Refresh after logout must fail
    r2 = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 401


def test_change_password(client, student_user, student_token):
    r = client.post(
        "/auth/change-password",
        json={"current_password": "Password1", "new_password": "NewPass99"},
        headers=_auth(student_token),
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data

    # Old refresh tokens must be revoked
    old_login = client.post(
        "/auth/login", json={"username": student_user.username, "password": "Password1"}
    )
    assert old_login.status_code == 401

    # New password works
    new_login = client.post(
        "/auth/login", json={"username": student_user.username, "password": "NewPass99"}
    )
    assert new_login.status_code == 200


def test_change_password_wrong_current(client, student_token):
    r = client.post(
        "/auth/change-password",
        json={"current_password": "wrong", "new_password": "NewPass99"},
        headers=_auth(student_token),
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "wrong_current_password"


def test_me(client, student_user, student_token):
    r = client.get("/auth/me", headers=_auth(student_token))
    assert r.status_code == 200
    assert r.json()["username"] == student_user.username


def test_inactive_user_cannot_login(client, db, student_user):
    student_user.is_active = False
    db.commit()
    r = client.post("/auth/login", json={"username": student_user.username, "password": "Password1"})
    assert r.status_code == 403
    assert r.json()["detail"] == "account_deactivated"
