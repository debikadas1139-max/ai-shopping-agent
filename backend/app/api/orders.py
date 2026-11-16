import sqlite3

from fastapi import APIRouter, Depends, Query, Response

from app.database import get_db
from app.schemas import OrderCreateRequest, OrderOut
from app.services import order_service

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
def create_order(body: OrderCreateRequest, response: Response, conn: sqlite3.Connection = Depends(get_db)):
    """Create a DEMO order (no payment). Requires confirmed=true and a unique idempotency_key.

    201 = new order created. 200 = this exact request was already processed; the original order is returned.
    """
    order = order_service.create_order(
        conn,
        items=[item.model_dump() for item in body.items],
        confirmed=body.confirmed,
        confirmed_total=body.confirmed_total,
        idempotency_key=body.idempotency_key,
    )
    if order["duplicate_request"]:
        response.status_code = 200
    return order


@router.get("", response_model=list[OrderOut])
def list_orders(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Order history (newest first). This demo has no user accounts, so all orders are listed."""
    return order_service.list_orders(conn, limit=limit, offset=offset)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, conn: sqlite3.Connection = Depends(get_db)):
    return order_service.get_order(conn, order_id)
