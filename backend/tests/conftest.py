"""Shared test fixtures. Tests use a temporary database, never your real store.db,
and none of them need a Groq API key."""

import pytest

from app.database import connect
from app.db_init import init_database


@pytest.fixture
def db(tmp_path):
    """A fresh, initialised database (32 sample products, 102 sample reviews)."""
    conn = connect(tmp_path / "test_store.db")
    init_database(conn)
    yield conn
    conn.close()


@pytest.fixture
def client(tmp_path):
    """FastAPI test client wired to a temporary database."""
    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.main import app

    db_path = tmp_path / "api_test.db"
    setup = connect(db_path)
    init_database(setup)
    setup.close()

    def override_get_db():
        conn = connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    # No "with" block: this skips the startup hook, so the real store.db is never touched.
    yield TestClient(app)
    app.dependency_overrides.clear()
