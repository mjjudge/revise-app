"""Tests for PIN auth flow — login, session, logout."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.main import app
from app.db.session import get_session
from app.db.seed import hash_pin
from app.models.user import User, Role

# Use an in-memory SQLite for tests with StaticPool so all connections share the same DB
TEST_DATABASE_URL = "sqlite://"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_test_session():
    with Session(test_engine) as session:
        yield session


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables + seed users in the test DB before each test."""
    SQLModel.metadata.create_all(test_engine)
    # Seed test users
    with Session(test_engine) as session:
        if not session.get(User, 1):
            session.add(User(display_name="Anna", role=Role.kid, pin_hash=hash_pin("1234")))
            session.add(User(display_name="Parent", role=Role.admin, pin_hash=hash_pin("9999")))
            session.commit()
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def client():
    """Test client with overridden DB session."""
    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestLogin:
    def test_login_page_loads(self, client):
        r = client.get("/login")
        assert r.status_code == 200
        assert "Revise Quest" in r.text

    def test_login_correct_pin_kid(self, client):
        r = client.post("/auth/login", data={"display_name": "Anna", "pin": "1234"}, follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/"
        assert "revise_session" in r.cookies

    def test_login_correct_pin_admin(self, client):
        r = client.post("/auth/login", data={"display_name": "Parent", "pin": "9999"}, follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/admin"

    def test_login_wrong_pin(self, client):
        r = client.post("/auth/login", data={"display_name": "Anna", "pin": "0000"}, follow_redirects=False)
        assert r.status_code == 303
        assert "error=1" in r.headers["location"]

    def test_login_nonexistent_user(self, client):
        r = client.post("/auth/login", data={"display_name": "Nobody", "pin": "1234"}, follow_redirects=False)
        assert r.status_code == 303
        assert "error=1" in r.headers["location"]


class TestProtectedPages:
    def test_home_requires_auth(self, client):
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/login"

    def test_admin_requires_auth(self, client):
        r = client.get("/admin", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/login"

    def test_home_accessible_after_login(self, client):
        # Login first
        client.post("/auth/login", data={"display_name": "Anna", "pin": "1234"})
        r = client.get("/")
        assert r.status_code == 200
        assert "Quest" in r.text

    def test_admin_requires_admin_role(self, client):
        # Login as kid
        client.post("/auth/login", data={"display_name": "Anna", "pin": "1234"})
        r = client.get("/admin", follow_redirects=False)
        assert r.status_code == 303  # kid can't access admin

    def test_admin_accessible_for_admin(self, client):
        client.post("/auth/login", data={"display_name": "Parent", "pin": "9999"})
        r = client.get("/admin")
        assert r.status_code == 200
        assert "Dashboard" in r.text


class TestLogout:
    def test_logout_clears_session(self, client):
        client.post("/auth/login", data={"display_name": "Anna", "pin": "1234"})
        r = client.get("/auth/logout", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/login"
