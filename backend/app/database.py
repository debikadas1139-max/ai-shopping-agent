"""SQLite connection helpers.

We use Python's built-in sqlite3 module with parameterized queries (the `?` placeholders).
Never build SQL by pasting user input into a string; always pass values as parameters.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from app.config import get_settings


def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a connection. Rows behave like dicts (row["name"]).

    isolation_level=None means "autocommit": we start and finish transactions
    ourselves with BEGIN / COMMIT, which keeps multi-step writes (like orders) explicit.
    """
    path = db_path or get_settings().database_path
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    """`with db_session() as conn:` gives a connection and always closes it."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
