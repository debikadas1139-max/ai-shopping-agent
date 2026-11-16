"""Create / upgrade the database and load the sample data.

Run from the backend folder:
    python scripts/init_db.py

Safe to run repeatedly; it never deletes existing data.
"""

import sys
from pathlib import Path

# Let this script import the "app" package no matter where it is launched from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.database import connect  # noqa: E402
from app.db_init import init_database  # noqa: E402


def main() -> None:
    settings = get_settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect()
    try:
        report = init_database(conn)
        n_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        n_reviews = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        n_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    finally:
        conn.close()

    print(f"Database ready: {settings.database_path}")
    print(f"  added this run : {report['products_added']} products, {report['reviews_added']} reviews, "
          f"{report['legacy_orders_migrated']} old orders migrated")
    print(f"  totals         : {n_products} products, {n_reviews} reviews, {n_orders} orders")
    print("  (sample data is for demonstration only)")


if __name__ == "__main__":
    main()
