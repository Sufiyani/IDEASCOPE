"""
Tests for user management endpoints.
Owner: Member 2 (Sufiyaan Imran)
"""

import pytest


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_student_requires_roll_no(client, admin_token):
    r = client.post(
        "/users",
        json={"full_name": "No Roll", "role": "student"},
        headers=_auth(admin_token),
    )
    assert r.status_code in (400, 422)


def test_create_student(client, admin_token):
    r = client.post(
        "/users",
        json={"full_name": "New Student", "role": "student", "roll_no": "2023F-BSE-099"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 201
    data = r.json()
    assert data["user"]["username"] == "2023f-bse-099"
    assert "temporary_password" in data


def test_create_admin_requires_username(client, admin_token):
    r = client.post(
        "/users",
        json={"full_name": "No Username Admin", "role": "admin"},
        headers=_auth(admin_token),
    )
    assert r.status_code in (400, 422)


def test_create_admin(client, admin_token):
    r = client.post(
        "/users",
        json={"full_name": "New Admin", "role": "admin", "username": "newadmin"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 201
    data = r.json()
    assert data["user"]["role"] == "admin"


def test_duplicate_roll_no(client, admin_token, student_user):
    r = client.post(
        "/users",
        json={"full_name": "Dupe", "role": "student", "roll_no": student_user.roll_no},
        headers=_auth(admin_token),
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "roll_no_already_exists"


def test_get_user(client, admin_token, student_user):
    r = client.get(f"/users/{student_user.id}", headers=_auth(admin_token))
    assert r.status_code == 200
    assert r.json()["id"] == student_user.id


def test_get_user_not_found(client, admin_token):
    r = client.get("/users/999999", headers=_auth(admin_token))
    assert r.status_code == 404
    assert r.json()["detail"] == "user_not_found"


def test_list_users(client, admin_token, student_user):
    r = client.get("/users", headers=_auth(admin_token))
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_update_user(client, admin_token, student_user):
    r = client.patch(
        f"/users/{student_user.id}",
        json={"full_name": "Updated Name"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated Name"


def test_change_role_to_admin_while_in_group(client, db, admin_token, student_user):
    from app.models.group import Group, GroupMember

    g = Group(name="GRP", batch="2023F", leader_id=student_user.id)
    db.add(g)
    db.flush()
    db.add(GroupMember(group_id=g.id, user_id=student_user.id))
    db.commit()

    r = client.patch(
        f"/users/{student_user.id}/role",
        json={"role": "admin"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "user_in_group"


def test_reset_password(client, admin_token, student_user):
    r = client.post(
        f"/users/{student_user.id}/reset-password",
        headers=_auth(admin_token),
    )
    assert r.status_code == 200
    assert "temporary_password" in r.json()


def test_reset_own_password_blocked(client, admin_token, admin_user):
    r = client.post(
        f"/users/{admin_user.id}/reset-password",
        headers=_auth(admin_token),
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "use_change_password"


def test_set_status(client, main_admin_token, student_user):
    r = client.patch(
        f"/users/{student_user.id}/status",
        json={"is_active": False},
        headers=_auth(main_admin_token),
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_response_has_no_password_hash(client, admin_token, student_user):
    r = client.get(f"/users/{student_user.id}", headers=_auth(admin_token))
    data = r.json()
    assert "password_hash" not in data
    assert "failed_logins" not in data
