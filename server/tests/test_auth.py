"""Authentication: registration, login, JWT issuance and validation."""

from conftest import bearer, login, register, register_and_token


def test_register_then_login_returns_jwt(client):
    assert register(client, "a@example.com").status_code == 200
    body = login(client, "a@example.com").json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["role"] == "student"
    assert body["user_id"]


def test_duplicate_registration_rejected(client):
    register(client, "dup@example.com")
    assert register(client, "dup@example.com").status_code == 400


def test_login_wrong_password_rejected(client):
    register(client, "b@example.com", password="rightpass")
    assert login(client, "b@example.com", password="wrongpass").status_code == 400


def test_protected_endpoint_requires_token(client):
    body = register_and_token(client, "c@example.com")
    uid = body["user_id"]
    # No token → 401
    assert client.get(f"/api/v1/profile/{uid}").status_code == 401
    # Garbage token → 401
    assert client.get(f"/api/v1/profile/{uid}", headers=bearer("not.a.jwt")).status_code == 401
    # Valid token → 200
    assert client.get(f"/api/v1/profile/{uid}", headers=bearer(body["access_token"])).status_code == 200
