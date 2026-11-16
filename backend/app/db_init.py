"""Create tables, migrate the old orders table, and load sample data.

Safe to run any number of times:
  * tables use CREATE TABLE IF NOT EXISTS
  * products use INSERT OR IGNORE (existing rows are never overwritten)
  * a sample review is added only if an identical one is not already there
  * nothing is ever deleted
"""

import logging
import sqlite3

from app import models
from app.seed_data import PRODUCTS, REVIEWS

logger = logging.getLogger(__name__)


def _columns(conn: sqlite3.Connection, table: str) -> set:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def migrate_legacy_orders(conn: sqlite3.Connection) -> int:
    """Convert the mentor's one-product-per-row `orders` table to orders + order_items.

    Returns how many old orders were migrated (0 if there was nothing to do).
    """
    cols = _columns(conn, "orders")
    is_legacy = bool(cols) and "product_name" in cols and "total_amount" not in cols
    if not is_legacy:
        return 0

    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("ALTER TABLE orders RENAME TO orders_legacy")
        conn.execute(models.CREATE_ORDERS)
        conn.execute(models.CREATE_ORDER_ITEMS)
        legacy_rows = conn.execute(
            "SELECT id, product_id, product_name, price, ordered_at FROM orders_legacy ORDER BY id"
        ).fetchall()
        for row in legacy_rows:
            conn.execute(
                "INSERT INTO orders (id, created_at, total_amount, status, idempotency_key) "
                "VALUES (?, ?, ?, 'confirmed', ?)",
                (row["id"], row["ordered_at"], row["price"], f"legacy-order-{row['id']}"),
            )
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity, line_total) "
                "VALUES (?, ?, ?, ?, 1, ?)",
                (row["id"], row["product_id"], row["product_name"], row["price"], row["price"]),
            )
        conn.execute("DROP TABLE orders_legacy")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    logger.info("Migrated %d legacy order(s) to the new orders/order_items tables", len(legacy_rows))
    return len(legacy_rows)


def create_tables(conn: sqlite3.Connection) -> None:
    for ddl in models.ALL_TABLES:
        conn.execute(ddl)
    for ddl in models.CREATE_INDEXES:
        conn.execute(ddl)


def seed_sample_data(conn: sqlite3.Connection) -> dict:
    """Insert missing sample products/reviews. Returns how many rows were added."""
    added_products = 0
    added_reviews = 0
    conn.execute("BEGIN IMMEDIATE")
    try:
        for row in PRODUCTS:
            cur = conn.execute(
                "INSERT OR IGNORE INTO products (id, name, category, price, description, is_organic) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                row,
            )
            added_products += cur.rowcount
        for product_id, rating, reviewer, text in REVIEWS:
            cur = conn.execute(
                "INSERT INTO reviews (product_id, rating, reviewer_name, review_text) "
                "SELECT ?, ?, ?, ? WHERE NOT EXISTS ("
                "  SELECT 1 FROM reviews WHERE product_id = ? AND reviewer_name = ? AND review_text = ?)",
                (product_id, rating, reviewer, text, product_id, reviewer, text),
            )
            added_reviews += cur.rowcount
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return {"products_added": added_products, "reviews_added": added_reviews}


def init_database(conn: sqlite3.Connection) -> dict:
    """Full, idempotent initialisation. Returns a small report."""
    migrated = migrate_legacy_orders(conn)
    create_tables(conn)
    report = seed_sample_data(conn)
    report["legacy_orders_migrated"] = migrated
    return report
