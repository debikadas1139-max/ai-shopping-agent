import sqlite3

from app.database import connect
from app.db_init import init_database
from app.seed_data import PRODUCTS, REVIEWS


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_first_init_loads_sample_data(db):
    assert count(db, "products") == len(PRODUCTS) == 32
    assert count(db, "reviews") == len(REVIEWS) == 102


def test_init_is_idempotent(db):
    report = init_database(db)
    init_database(db)
    assert report["products_added"] == 0
    assert report["reviews_added"] == 0
    assert count(db, "products") == 32
    assert count(db, "reviews") == 102


def test_existing_data_survives_init(db):
    db.execute("UPDATE products SET price = 99.5 WHERE id = 1")
    db.execute("INSERT INTO reviews (product_id, rating, reviewer_name, review_text) VALUES (1, 3.0, 'Tester', 'My own review')")
    init_database(db)
    assert db.execute("SELECT price FROM products WHERE id = 1").fetchone()[0] == 99.5
    assert db.execute("SELECT COUNT(*) FROM reviews WHERE reviewer_name = 'Tester'").fetchone()[0] == 1
    assert count(db, "reviews") == 103


def test_legacy_orders_table_is_migrated(tmp_path):
    path = tmp_path / "legacy.db"
    raw = sqlite3.connect(path)
    raw.executescript(
        """
        CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT, price REAL,
                               description TEXT, is_organic INTEGER DEFAULT 0);
        INSERT INTO products VALUES (1, 'Organic Raw Honey', 'honey', 14.99, 'x', 1);
        CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
                             product_name TEXT NOT NULL, price REAL NOT NULL,
                             ordered_at TEXT NOT NULL DEFAULT (datetime('now')));
        INSERT INTO orders (id, product_id, product_name, price, ordered_at)
               VALUES (7, 1, 'Organic Raw Honey', 14.99, '2026-05-13 21:10:53');
        """
    )
    raw.commit()
    raw.close()

    conn = connect(path)
    report = init_database(conn)
    assert report["legacy_orders_migrated"] == 1
    order = conn.execute("SELECT id, total_amount, created_at FROM orders").fetchone()
    assert (order["id"], order["total_amount"], order["created_at"]) == (7, 14.99, "2026-05-13 21:10:53")
    item = conn.execute("SELECT product_name, quantity, line_total FROM order_items WHERE order_id = 7").fetchone()
    assert (item["product_name"], item["quantity"], item["line_total"]) == ("Organic Raw Honey", 1, 14.99)
    # Running again must not migrate twice.
    assert init_database(conn)["legacy_orders_migrated"] == 0
    assert count(conn, "orders") == 1
    conn.close()
