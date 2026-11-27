"""
Tests for group endpoints.
Owner: Member 2 (Sufiyaan Imran)
"""

from app.core.constants import DEFAULT_MAX_GROUP_SIZE


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _make_student(client, admin_token, roll_no, suffix=""):
    r = client.post(
        "/users",
        json={"full_name": f"Student {suffix}", "role": "student", "roll_no": roll_no},
        headers=_auth(admin_token),
    )
    assert r.status_code == 201
    return r.json()


def test_create_group(client, student_token):
    r = client.post("/groups", json={"name": "Team Alpha"}, headers=_auth(student_token))
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Team Alpha"
    assert data["batch"] == "2023F"
    assert len(data["members"]) == 1


def test_student_already_in_group(client, student_token):
    client.post("/groups", json={"name": "Team A"}, headers=_auth(student_token))
    r = client.post("/groups", json={"name": "Team B"}, headers=_auth(student_token))
    assert r.status_code == 409
    assert r.json()["detail"] == "already_in_group"


def test_get_my_group(client, student_token):
    client.post("/groups", json={"name": "My Team"}, headers=_auth(student_token))
    r = client.get("/groups/me", headers=_auth(student_token))
    assert r.status_code == 200
    assert r.json()["name"] == "My Team"


def test_get_my_group_not_in_group(client, admin_token):
    # Admin with no group
    r = client.get("/groups/me", headers=_auth(admin_token))
    assert r.status_code == 404


def test_add_member(client, student_token, admin_token, db):
    group_r = client.post("/groups", json={"name": "Team"}, headers=_auth(student_token))
    group_id = group_r.json()["id"]

    s2 = _make_student(client, admin_token, "2023F-BSE-002", "2")
    s2_user_id = s2["user"]["id"]
    s2_pass = s2["temporary_password"]
    s2_login = client.post("/auth/login", json={"username": "2023f-bse-002", "password": s2_pass})
    _ = s2_login.json()["access_token"]

    # Student joins himself
    r = client.post(
        f"/groups/{group_id}/members",
        json={"user_id": s2_user_id},
        headers=_auth(student_token),
    )
    assert r.status_code == 201
    assert len(r.json()["members"]) == 2


def test_group_full(client, student_token, admin_token):
    group_r = client.post("/groups", json={"name": "Full Team"}, headers=_auth(student_token))
    group_id = group_r.json()["id"]

    for i in range(2, DEFAULT_MAX_GROUP_SIZE + 1):
        s = _make_student(client, admin_token, f"2023F-BSE-{i:03d}", str(i))
        client.post(
            f"/groups/{group_id}/members",
            json={"user_id": s["user"]["id"]},
            headers=_auth(student_token),
        )

    # One more should fail
    extra = _make_student(
        client, admin_token, f"2023F-BSE-{DEFAULT_MAX_GROUP_SIZE + 1:03d}", "extra"
    )
    r = client.post(
        f"/groups/{group_id}/members",
        json={"user_id": extra["user"]["id"]},
        headers=_auth(student_token),
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "group_full"


def test_admin_cannot_be_group_member(client, admin_token, student_token, admin_user):
    group_r = client.post("/groups", json={"name": "Test"}, headers=_auth(student_token))
    group_id = group_r.json()["id"]

    r = client.post(
        f"/groups/{group_id}/members",
        json={"user_id": admin_user.id},
        headers=_auth(student_token),
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "not_a_student"


def test_leader_transfer_on_leave(client, student_token, admin_token, student_user):
    group_r = client.post("/groups", json={"name": "Transfer"}, headers=_auth(student_token))
    group_id = group_r.json()["id"]

    s2 = _make_student(client, admin_token, "2023F-BSE-010", "10")
    s2_id = s2["user"]["id"]
    s2_pass = s2["temporary_password"]
    s2_login = client.post("/auth/login", json={"username": "2023f-bse-010", "password": s2_pass})
    s2_token = s2_login.json()["access_token"]

    # Leader adds s2
    client.post(
        f"/groups/{group_id}/members",
        json={"user_id": s2_id},
        headers=_auth(student_token),
    )

    # Leader leaves
    r = client.delete(
        f"/groups/{group_id}/members/{student_user.id}",
        headers=_auth(student_token),
    )
    assert r.status_code == 204

    # s2 is now leader
    group_detail = client.get(f"/groups/{group_id}", headers=_auth(s2_token))
    assert group_detail.status_code == 200
    assert group_detail.json()["leader_id"] == s2_id


def test_last_member_leaves_deletes_group(client, student_token, student_user):
    group_r = client.post("/groups", json={"name": "Solo"}, headers=_auth(student_token))
    group_id = group_r.json()["id"]

    r = client.delete(
        f"/groups/{group_id}/members/{student_user.id}",
        headers=_auth(student_token),
    )
    assert r.status_code == 204

    r2 = client.get("/groups/me", headers=_auth(student_token))
    assert r2.status_code == 404


def test_list_groups_admin_only(client, admin_token, student_token, student_user):
    client.post("/groups", json={"name": "Listed"}, headers=_auth(student_token))
    r = client.get("/groups", headers=_auth(admin_token))
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r2 = client.get("/groups", headers=_auth(student_token))
    assert r2.status_code == 403
