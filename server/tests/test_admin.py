"""Admin RBAC: only admins may manage courses and user roles."""

from conftest import bearer, make_admin, register_and_token

COURSE = {
    "course_code": 9990001,
    "name": "Test Course",
    "category": "elective",
    "workload": 4,
    "credits": 3.0,
    "skills": "Python, Testing",
}


def test_non_admin_blocked_from_admin_api(client):
    user = register_and_token(client, "plain@example.com")
    resp = client.post(
        "/api/v1/admin/courses", headers=bearer(user["access_token"]), json=COURSE
    )
    assert resp.status_code == 403


def test_admin_api_requires_token(client):
    assert client.get("/api/v1/admin/users").status_code == 401


def test_admin_course_crud(client):
    user = register_and_token(client, "admin@example.com")
    make_admin("admin@example.com")
    # Re-login so the token's user is recognized (role is read live from DB).
    h = bearer(user["access_token"])

    # Create
    r = client.post("/api/v1/admin/courses", headers=h, json=COURSE)
    assert r.status_code == 201, r.text
    assert r.json()["course_code"] == COURSE["course_code"]

    # Duplicate create → conflict
    assert client.post("/api/v1/admin/courses", headers=h, json=COURSE).status_code == 409

    # Update
    r = client.put(
        f"/api/v1/admin/courses/{COURSE['course_code']}",
        headers=h,
        json={"name": "Edited", "workload": 5, "credits": 3.0},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Edited"

    # Appears in public catalog
    codes = [c["course_code"] for c in client.get("/api/v1/courses/").json()]
    assert COURSE["course_code"] in codes

    # Delete
    assert client.delete(
        f"/api/v1/admin/courses/{COURSE['course_code']}", headers=h
    ).status_code == 200
    codes = [c["course_code"] for c in client.get("/api/v1/courses/").json()]
    assert COURSE["course_code"] not in codes


def test_update_missing_course_returns_404(client):
    register_and_token(client, "admin2@example.com")
    make_admin("admin2@example.com")
    body = client.post("/api/v1/login", json={"email": "admin2@example.com", "password": "pass12345"}).json()
    h = bearer(body["access_token"])
    assert client.put("/api/v1/admin/courses/123456", headers=h, json={"name": "x"}).status_code == 404


def test_role_management(client):
    register_and_token(client, "boss@example.com")
    make_admin("boss@example.com")
    boss = client.post("/api/v1/login", json={"email": "boss@example.com", "password": "pass12345"}).json()
    h = bearer(boss["access_token"])

    target = register_and_token(client, "member@example.com")
    uid = target["user_id"]

    # Promote
    r = client.patch(f"/api/v1/admin/users/{uid}/role", headers=h, json={"role": "admin"})
    assert r.status_code == 200 and r.json()["role"] == "admin"

    # Demote
    r = client.patch(f"/api/v1/admin/users/{uid}/role", headers=h, json={"role": "student"})
    assert r.status_code == 200 and r.json()["role"] == "student"

    # Invalid role rejected by validation
    r = client.patch(f"/api/v1/admin/users/{uid}/role", headers=h, json={"role": "wizard"})
    assert r.status_code == 422
