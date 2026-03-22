"""Shared fixtures for integration tests.

Spins up a dedicated test database in the already-running PostgreSQL and MongoDB
instances (installed via Homebrew) so that tests never touch production data.
"""

import os
import secrets
import sys

import psycopg2
import pytest
from pymongo import MongoClient

# Ensure the backend's internal imports work (mirrors what app.py and uvicorn do)
_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "app"))
_BACKEND_DIR = os.path.join(_APP_DIR, "backend")
for _d in (_BACKEND_DIR, _APP_DIR):
    if _d not in sys.path:
        sys.path.insert(0, _d)

# ---------------------------------------------------------------------------
# Configuration – unique DB names so parallel runs don't collide
# ---------------------------------------------------------------------------
_PG_DSN_ADMIN = os.getenv(
    "TEST_PG_DSN_ADMIN",
    "postgresql://postgres:postgres@localhost:5432/postgres",
)
_PG_TEST_DB = f"budget_test_{secrets.token_hex(4)}"
_MONGO_URI = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017")
_MONGO_TEST_DB = f"budget_test_{secrets.token_hex(4)}"

# ---------------------------------------------------------------------------
# PostgreSQL: create / drop a throwaway database per test session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def pg_test_db():
    """Create a temporary PostgreSQL database and return its DSN."""
    # Connect to the default 'postgres' database to issue CREATE DATABASE
    conn = psycopg2.connect(_PG_DSN_ADMIN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'CREATE DATABASE "{_PG_TEST_DB}"')
    cur.close()
    conn.close()

    dsn = f"postgresql://postgres:postgres@localhost:5432/{_PG_TEST_DB}"
    yield dsn

    # Teardown: drop the test database
    conn = psycopg2.connect(_PG_DSN_ADMIN)
    conn.autocommit = True
    cur = conn.cursor()
    # Terminate any remaining connections
    cur.execute(
        f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{_PG_TEST_DB}' AND pid <> pg_backend_pid()
    """
    )
    cur.execute(f'DROP DATABASE IF EXISTS "{_PG_TEST_DB}"')
    cur.close()
    conn.close()


# ---------------------------------------------------------------------------
# MongoDB: use a throwaway database per test session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def mongo_test_db():
    """Return the name of a temporary MongoDB database."""
    yield _MONGO_TEST_DB

    # Teardown: drop the test database
    client = MongoClient(_MONGO_URI)
    client.drop_database(_MONGO_TEST_DB)
    client.close()


# ---------------------------------------------------------------------------
# FastAPI TestClient wired to the test databases
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def client(pg_test_db, mongo_test_db):
    """Return a FastAPI TestClient backed by the test databases.

    We patch env vars *before* importing the app module so the lifespan
    handler picks up the test DSNs.
    """
    os.environ["POSTGRES_DSN"] = pg_test_db
    os.environ["MONGO_URI"] = _MONGO_URI
    os.environ["MONGO_DB"] = mongo_test_db
    os.environ["TELEGRAM_BOT_USERNAME"] = "test_bot"

    # The backend's app.py lives at app/backend/app.py and uses bare imports
    # (e.g. "from api.request_handler import ..."). With _BACKEND_DIR on sys.path
    # first, `import app` resolves to app/backend/app.py.
    from fastapi.testclient import TestClient

    import app as backend_app_module  # noqa: E402

    app = backend_app_module.app

    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def registered_user(client):
    """Register a user and return (login, password, token, user_id)."""
    login = f"testuser_{secrets.token_hex(4)}"
    password = "testpass123"
    resp = client.post(
        "/auth/register", json={"login": login, "password": password}
    )
    assert resp.status_code == 200
    data = resp.json()
    return {
        "login": login,
        "password": password,
        "token": data["token"],
        "user_id": data["user_id"],
    }


@pytest.fixture(scope="session")
def auth_header(registered_user):
    """Return an Authorization header dict for the registered test user."""
    return {"Authorization": f"Bearer {registered_user['token']}"}


@pytest.fixture()
def fresh_user(client):
    """Register a brand-new user for tests that need isolated state.

    Returns (token, user_id, auth_header).
    """
    login = f"fresh_{secrets.token_hex(4)}"
    password = "freshpass"
    resp = client.post(
        "/auth/register", json={"login": login, "password": password}
    )
    assert resp.status_code == 200
    data = resp.json()
    token = data["token"]
    return {
        "login": login,
        "password": password,
        "token": token,
        "user_id": data["user_id"],
        "header": {"Authorization": f"Bearer {token}"},
    }
