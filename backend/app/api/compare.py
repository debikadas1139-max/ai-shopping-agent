import sqlite3

from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas import CompareRequest, ComparisonOut
from app.services import product_service

router = APIRouter(prefix="/api", tags=["compare"])


@router.post("/compare", response_model=ComparisonOut)
def compare(body: CompareRequest, conn: sqlite3.Connection = Depends(get_db)):
    """Compare 2-4 products using real database values."""
    return product_service.compare_products(conn, body.product_ids)
