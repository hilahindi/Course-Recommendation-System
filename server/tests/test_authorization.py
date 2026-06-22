"""Per-student authorization: a user may only access their own data."""

from conftest import bearer, register_and_token


def test_student_cannot_access_another_students_profile(client):
    a = register_and_token(client, "owner@example.com")
    b = register_and_token(client, "intruder@example.com")

    # Owner reads own profile — allowed.
    assert client.get(
        f"/api/v1/profile/{a['user_id']}", headers=bearer(a["access_token"])
    ).status_code == 200

    # Intruder tries to read owner's profile with their own token — forbidden.
    resp = client.get(
        f"/api/v1/profile/{a['user_id']}", headers=bearer(b["access_token"])
    )
    assert resp.status_code == 403


def test_student_cannot_read_another_students_history(client):
    a = register_and_token(client, "owner2@example.com")
    b = register_and_token(client, "intruder2@example.com")
    resp = client.get(
        f"/api/v1/profile/{a['user_id']}/history", headers=bearer(b["access_token"])
    )
    assert resp.status_code == 403


def test_recommendations_require_authentication(client):
    assert client.post("/api/v1/recommendations/get").status_code == 401
