"""Cart validation and order creation.

The backend is the only source of truth for prices and totals. The browser sends
only product IDs and quantities; everything else is read from the database.

Money is calculated in whole cents (integers) to avoid floating-point rounding errors.
"""

import hashlib
import json
import re
import sqlite3
from typing import Optional

from app.utils.errors import BadRequestError, ConflictError, NotFoundError

MAX_QUANTITY_PER_PRODUCT = 99
MAX_DISTINCT_PRODUCTS = 50
_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,100}$")


def _cents(amount: float) -> int:
    return int(round(float(amount) * 100))


def _normalise_items(items: list) -> dict:
    """Check each {product_id, quantity}; merge duplicate product IDs. Returns {product_id: quantity}."""
    if not items:
        raise BadRequestError("Your cart is empty.", code="empty_cart")
    if len(items) > MAX_DISTINCT_PRODUCTS:
        raise BadRequestError(f"A cart can hold at most {MAX_DISTINCT_PRODUCTS} lines.", code="cart_too_large")

    merged: dict = {}
    for item in items:
        try:
            product_id = item["product_id"]
            quantity = item["quantity"]
        except (KeyError, TypeError):
            raise BadRequestError("Each cart item needs product_id and quantity.", code="invalid_item")
        if isinstance(product_id, bool) or not isinstance(product_id, int) or product_id <= 0:
            raise BadRequestError("product_id must be a positive whole number.", code="invalid_item")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise BadRequestError("quantity must be a whole number of at least 1.", code="invalid_quantity")
        merged[product_id] = merged.get(product_id, 0) + quantity
        if merged[product_id] > MAX_QUANTITY_PER_PRODUCT:
            raise BadRequestError(
                f"You can order at most {MAX_QUANTITY_PER_PRODUCT} of one product.", code="invalid_quantity"
            )
    return merged


def validate_cart(conn: sqlite3.Connection, items: list) -> dict:
    """Look up every product and compute the real line totals and order total."""
    merged = _normalise_items(items)

    placeholders = ",".join("?" * len(merged))
    rows = conn.execute(
        f"SELECT id, name, category, price, is_organic FROM products WHERE id IN ({placeholders})",
        list(merged.keys()),
    ).fetchall()
    found = {row["id"]: row for row in rows}

    missing = [pid for pid in merged if pid not in found]
    if missing:
        raise NotFoundError(f"Products not found: {missing}.", code="product_not_found")

    lines = []
    total_cents = 0
    for product_id, quantity in merged.items():
        row = found[product_id]
        if row["price"] is None or row["price"] <= 0:
            raise BadRequestError(f"'{row['name']}' is not available for purchase.", code="product_unavailable")
        unit_cents = _cents(row["price"])
        line_cents = unit_cents * quantity
        total_cents += line_cents
        lines.append(
            {
                "product_id": product_id,
                "name": row["name"],
                "category": row["category"],
                "is_organic": bool(row["is_organic"]),
                "unit_price": unit_cents / 100,
                "quantity": quantity,
                "line_total": line_cents / 100,
            }
        )
    return {
        "items": lines,
        "total": total_cents / 100,
        "item_count": sum(line["quantity"] for line in lines),
    }


def _fingerprint(cart: dict) -> str:
    """A short hash of 'which products, how many' so a reused key with a different cart is detected."""
    pairs = sorted((line["product_id"], line["quantity"]) for line in cart["items"])
    return hashlib.sha256(json.dumps(pairs).encode()).hexdigest()


def _load_items(conn: sqlite3.Connection, order_ids: list) -> dict:
    if not order_ids:
        return {}
    placeholders = ",".join("?" * len(order_ids))
    rows = conn.execute(
        "SELECT order_id, product_id, product_name, unit_price, quantity, line_total "
        f"FROM order_items WHERE order_id IN ({placeholders}) ORDER BY id",
        order_ids,
    ).fetchall()
    grouped: dict = {}
    for row in rows:
        grouped.setdefault(row["order_id"], []).append(
            {
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "unit_price": row["unit_price"],
                "quantity": row["quantity"],
                "line_total": row["line_total"],
            }
        )
    return grouped


def _order_dict(row: sqlite3.Row, items: list) -> dict:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "status": row["status"],
        "total_amount": row["total_amount"],
        "item_count": sum(i["quantity"] for i in items),
        "items": items,
        "duplicate_request": False,
    }


def get_order(conn: sqlite3.Connection, order_id: int) -> dict:
    row = conn.execute(
        "SELECT id, created_at, status, total_amount FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if row is None:
        raise NotFoundError(f"Order {order_id} was not found.", code="order_not_found")
    return _order_dict(row, _load_items(conn, [order_id]).get(order_id, []))


def list_orders(conn: sqlite3.Connection, limit: int = 50, offset: int = 0) -> list:
    rows = conn.execute(
        "SELECT id, created_at, status, total_amount FROM orders ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    items = _load_items(conn, [r["id"] for r in rows])
    return [_order_dict(r, items.get(r["id"], [])) for r in rows]


def _find_by_key(conn: sqlite3.Connection, key: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT id, request_fingerprint FROM orders WHERE idempotency_key = ?", (key,)
    ).fetchone()


def create_order(
    conn: sqlite3.Connection,
    items: list,
    confirmed: bool,
    confirmed_total: float,
    idempotency_key: str,
) -> dict:
    """Create a demo order. Nothing is charged; this only writes to the local database.

    Safety rules:
      1. `confirmed` must be True (the user ticked the confirmation box).
      2. The total the user saw (`confirmed_total`) must equal the total the backend calculates now.
      3. The same idempotency_key + same cart returns the original order instead of creating a second one.
      4. Order and items are written in ONE transaction: all or nothing.
    """
    if confirmed is not True:
        raise BadRequestError(
            "The order was not confirmed. Review the summary and confirm before placing the order.",
            code="confirmation_required",
        )
    if not isinstance(idempotency_key, str) or not _KEY_PATTERN.match(idempotency_key):
        raise BadRequestError(
            "idempotency_key must be 8-100 characters (letters, digits, '-' or '_').", code="invalid_idempotency_key"
        )

    cart = validate_cart(conn, items)
    fingerprint = _fingerprint(cart)

    existing = _find_by_key(conn, idempotency_key)
    if existing is not None:
        return _return_existing(conn, existing, fingerprint)

    if _cents(confirmed_total) != _cents(cart["total"]):
        raise ConflictError(
            f"The total changed from ${confirmed_total:.2f} to ${cart['total']:.2f}. Please review your order again.",
            code="total_mismatch",
        )

    conn.execute("BEGIN IMMEDIATE")
    try:
        # Check again inside the transaction in case two identical requests arrive together.
        existing = _find_by_key(conn, idempotency_key)
        if existing is not None:
            conn.execute("ROLLBACK")
            return _return_existing(conn, existing, fingerprint)

        cur = conn.execute(
            "INSERT INTO orders (total_amount, status, idempotency_key, request_fingerprint) "
            "VALUES (?, 'confirmed', ?, ?)",
            (cart["total"], idempotency_key, fingerprint),
        )
        order_id = cur.lastrowid
        for line in cart["items"]:
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity, line_total) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (order_id, line["product_id"], line["name"], line["unit_price"], line["quantity"], line["line_total"]),
            )
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass  # already rolled back above
        raise

    return get_order(conn, order_id)


def _return_existing(conn: sqlite3.Connection, existing: sqlite3.Row, fingerprint: str) -> dict:
    if existing["request_fingerprint"] not in (None, fingerprint):
        raise ConflictError(
            "This checkout attempt was already used for a different cart. Please start checkout again.",
            code="idempotency_conflict",
        )
    order = get_order(conn, existing["id"])
    order["duplicate_request"] = True
    return order
