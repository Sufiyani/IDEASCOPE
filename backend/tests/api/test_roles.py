"""
Tests for role-based access control.
Owner: Member 2 (Sufiyaan Imran)
"""


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Deactivated user is blocked ───────────────────────────────────────────────


def test_deactivated_user_blocked(client, db, student_user, student_token):
    student_user.is_active = False
    db.commit()
    r = client.get("/auth/me", headers=_auth(student_token))
    assert r.status_code == 401


# ── must_change_password blocks everything except exempted endpoints ──────────


def test_must_change_password_blocks_users(client, db, admin_user, admin_token):
    admin_user.must_change_password = True
    db.commit()
    r = client.get("/users", headers=_auth(admin_token))
    assert r.status_code == 403
    assert r.json()["detail"] == "password_change_required"


def test_must_change_password_allows_me(client, db, student_user, student_token):
    student_user.must_change_password = True
    db.commit()
    r = client.get("/auth/me", headers=_auth(student_token))
    assert r.status_code == 200


def test_must_change_password_allows_change_password(client, db, student_user, student_token):
    student_user.must_change_password = True
    db.commit()
    r = client.post(
        "/auth/change-password",
        json={"current_password": "Password1", "new_password": "NewPass99"},
        headers=_auth(student_token),
    )
    assert r.status_code == 200


def test_must_change_password_allows_logout(client, db, student_user, student_token):
    student_user.must_change_password = True
    db.commit()
    # We need a refresh token
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


# ── Student cannot access admin endpoints ────────────────────────────────────


def test_student_cannot_list_users(client, student_token):
    r = client.get("/users", headers=_auth(student_token))
    assert r.status_code == 403


def test_student_cannot_set_status(client, student_token, student_user):
    r = client.patch(
        f"/users/{student_user.id}/status",
        json={"is_active": False},
        headers=_auth(student_token),
    )
    assert r.status_code == 403


# ── Normal admin cannot change user status (requires main admin) ──────────────


def test_admin_cannot_set_status(client, admin_token, student_user):
    r = client.patch(
        f"/users/{student_user.id}/status",
        json={"is_active": False},
        headers=_auth(admin_token),
    )
    assert r.status_code == 403


# ── Main admin CAN change status ──────────────────────────────────────────────


def test_main_admin_can_set_status(client, main_admin_token, student_user):
    r = client.patch(
        f"/users/{student_user.id}/status",
        json={"is_active": False},
        headers=_auth(main_admin_token),
    )
    assert r.status_code == 200


# ── No token → 401 ───────────────────────────────────────────────────────────


def test_no_token_returns_401(client):
    r = client.get("/users")
    assert r.status_code == 401
