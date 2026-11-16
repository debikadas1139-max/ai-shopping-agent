import sqlite3

from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas import CartOut, CartValidateRequest
from app.services import order_service

router = APIRouter(prefix="/api/cart", tags=["cart"])


@router.post("/validate", response_model=CartOut)
def validate_cart(body: CartValidateRequest, conn: sqlite3.Connection = Depends(get_db)):
    """Check product ids and quantities and return real prices and totals. Nothing is saved."""
    return order_service.validate_cart(conn, [item.model_dump() for item in body.items])
