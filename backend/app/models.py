"""Database table definitions (plain SQL).

products and reviews keep the same columns as the mentor's original database, so an
existing store.db keeps working. orders is new: an order has many order_items.
"""

CREATE_PRODUCTS = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    price REAL,
    description TEXT,
    is_organic INTEGER DEFAULT 0
)
"""

CREATE_REVIEWS = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    rating REAL,
    reviewer_name TEXT,
    review_text TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id)
)
"""

# idempotency_key: the browser sends one per checkout attempt. If the same request is
# retried, the database refuses a second row (UNIQUE) and we return the first order.
CREATE_ORDERS = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    total_amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed',
    idempotency_key TEXT UNIQUE,
    request_fingerprint TEXT
)
"""

# Product name and unit price are copied ("snapshot") so old orders never change
# when a product is renamed or repriced later.
CREATE_ORDER_ITEMS = """
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    line_total REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
)
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)",
]

ALL_TABLES = [CREATE_PRODUCTS, CREATE_REVIEWS, CREATE_ORDERS, CREATE_ORDER_ITEMS]
