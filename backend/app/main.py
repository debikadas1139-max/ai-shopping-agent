"""FastAPI application entry point.

Run from the backend folder:
    uvicorn app.main:app --reload --port 8000
Interactive API docs: http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import cart, chat, compare, health, image_search, orders, products
from app.config import get_settings
from app.database import connect
from app.db_init import init_database
from app.utils.errors import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and add any missing sample data. Never deletes existing data.
    settings = get_settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect()
    try:
        report = init_database(conn)
    finally:
        conn.close()
    logger.info("Database ready at %s (%s)", settings.database_path, report)
    if not settings.ai_configured:
        logger.warning("GROQ_API_KEY is not set: the catalog and cart work, but chat and image search will not.")
    yield


app = FastAPI(
    title="AI Shopping Agent (demo store)",
    description="Demonstration store with sample data. No real payments or shipping.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().frontend_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})


for module in (health, products, compare, cart, orders, chat, image_search):
    app.include_router(module.router)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "AI Shopping Agent API (demo store). See /docs for the interactive API."}
