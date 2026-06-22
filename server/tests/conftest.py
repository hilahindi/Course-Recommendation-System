"""Test configuration: isolated SQLite DB, no catalog seeding, fresh schema per test."""

import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

# Configure an isolated test environment BEFORE importing the app.
_TEST_DB = Path(__file__).resolve().parent / "test_app.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["CATALOG_SYNC_MODE"] = "skip"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

if _TEST_DB.exists():
    _TEST_DB.unlink()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402  (importing also runs create_all on the SQLite engine)
import models  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_schema():
    """Each test starts from an empty schema for full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    # No context manager → app lifespan (scheduler/catalog sync) does not run.
    return TestClient(main.app)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def register(client, email, password="pass12345", name="User"):
    return client.post(
        "/api/v1/register", json={"email": email, "name": name, "password": password}
    )


def login(client, email, password="pass12345"):
    return client.post("/api/v1/login", json={"email": email, "password": password})


def register_and_token(client, email, **kwargs):
    register(client, email, **kwargs)
    body = login(client, email).json()
    return body


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def make_admin(email):
    """Promote a user to admin directly in the DB (no admin exists initially)."""
    session = SessionLocal()
    try:
        student = (
            session.query(models.Student)
            .filter(models.Student.email == email)
            .first()
        )
        student.role = "admin"
        session.commit()
    finally:
        session.close()
