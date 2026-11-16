import sqlite3

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.database import get_db
from app.schemas import HealthOut

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(conn: sqlite3.Connection = Depends(get_db)):
    """Is the server up, is the database readable, and is an AI key configured? (The key itself is never shown.)"""
    try:
        conn.execute("SELECT 1").fetchone()
        database = "ok"
    except sqlite3.Error:
        database = "error"
    ai_ready = get_settings().ai_configured
    return HealthOut(
        status="ok" if database == "ok" else "degraded",
        database=database,
        ai_configured=ai_ready,
        message="Demonstration store with sample data."
        + ("" if ai_ready else " AI assistant is not configured (add GROQ_API_KEY to backend/.env)."),
    )
