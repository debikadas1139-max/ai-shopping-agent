import sqlite3
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.schemas import CategoryOut, ProductListOut, ProductOut, ReviewOut
from app.services import product_service

router = APIRouter(prefix="/api/products", tags=["products"])

SortOption = Literal["relevance", "price_asc", "price_desc", "rating_desc", "rating_asc", "name"]


@router.get("", response_model=ProductListOut)
def list_products(
    q: Optional[str] = Query(None, max_length=100, description="Keywords, e.g. 'organic honey'"),
    category: Optional[str] = Query(None, max_length=50),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    is_organic: Optional[bool] = Query(None),
    sort: SortOption = "relevance",
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
):
    items, total = product_service.list_products(
        conn,
        query=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        is_organic=is_organic,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total}


# Defined BEFORE "/{product_id}" so "categories" is not mistaken for an id.
@router.get("/categories", response_model=list[CategoryOut])
def list_categories(conn: sqlite3.Connection = Depends(get_db)):
    return product_service.list_categories(conn)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, conn: sqlite3.Connection = Depends(get_db)):
    return product_service.get_product(conn, product_id)


@router.get("/{product_id}/reviews", response_model=list[ReviewOut])
def get_reviews(product_id: int, conn: sqlite3.Connection = Depends(get_db)):
    return product_service.list_reviews(conn, product_id)
