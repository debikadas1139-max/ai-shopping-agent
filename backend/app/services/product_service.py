"""Product search, ratings, comparison and recommendations.

Everything here reads the database and returns plain dicts. The REST API and the
AI agent's tools both call these functions, so they always agree with each other.
"""

import re
import sqlite3
from typing import Optional

from app.utils.errors import BadRequestError, NotFoundError

# Allowed sort options (the SQL text is fixed here, never taken from user input).
SORT_OPTIONS = {
    "relevance": "p.id ASC",
    "price_asc": "p.price ASC, p.id ASC",
    "price_desc": "p.price DESC, p.id ASC",
    "rating_desc": "average_rating DESC, review_count DESC, p.id ASC",
    "rating_asc": "average_rating ASC, p.id ASC",
    "name": "p.name COLLATE NOCASE ASC",
}

# Words ignored when a query is split into keywords ("organic honey please" -> organic, honey).
STOPWORDS = {"a", "an", "the", "and", "or", "of", "for", "with", "some", "me", "my", "please", "find", "show", "any"}

_SELECT = """
SELECT p.id, p.name, p.category, p.price, p.description, p.is_organic,
       COALESCE(ROUND(AVG(r.rating), 2), 0.0) AS average_rating,
       COUNT(r.id) AS review_count
FROM products p
LEFT JOIN reviews r ON r.product_id = p.id
"""


def _like_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _row_to_product(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "price": float(row["price"] or 0.0),
        "description": row["description"] or "",
        "is_organic": bool(row["is_organic"]),
        "average_rating": float(row["average_rating"] or 0.0),
        "review_count": int(row["review_count"] or 0),
    }


def _keywords(query: Optional[str]) -> list:
    if not query:
        return []
    words = re.findall(r"[a-z0-9]+", query.lower())
    return [w for w in words if w not in STOPWORDS]


def list_products(
    conn: sqlite3.Connection,
    query: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    is_organic: Optional[bool] = None,
    sort: str = "relevance",
    limit: int = 50,
    offset: int = 0,
) -> tuple:
    """Search products. Returns (items, total_matches).

    Every keyword in `query` must appear in the name, description or category
    (plural "nuts" also matches "nut"). Ratings are computed live from the reviews table.
    """
    if sort not in SORT_OPTIONS:
        raise BadRequestError(f"Unknown sort '{sort}'. Choose one of: {', '.join(SORT_OPTIONS)}.", code="invalid_sort")
    if min_price is not None and max_price is not None and min_price > max_price:
        raise BadRequestError("min_price cannot be greater than max_price.", code="invalid_price_range")

    where, params = [], []

    for word in _keywords(query):
        variants = {word}
        if len(word) > 3 and word.endswith("s"):
            variants.add(word[:-1])
        clauses = []
        for variant in sorted(variants):
            like = f"%{_like_escape(variant)}%"
            clauses.append(
                "(p.name LIKE ? ESCAPE '\\' OR p.description LIKE ? ESCAPE '\\' OR p.category LIKE ? ESCAPE '\\')"
            )
            params.extend([like, like, like])
        where.append("(" + " OR ".join(clauses) + ")")

    if category:
        where.append("LOWER(p.category) = LOWER(?)")
        params.append(category.strip())
    if min_price is not None:
        where.append("p.price >= ?")
        params.append(min_price)
    if max_price is not None:
        where.append("p.price <= ?")
        params.append(max_price)
    if is_organic is not None:
        where.append("p.is_organic = ?")
        params.append(1 if is_organic else 0)

    sql = _SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY p.id"
    having_params = []
    if min_rating is not None and min_rating > 0:
        # Compare the unrounded average (tiny tolerance avoids float surprises like 4.4999999).
        sql += " HAVING COALESCE(AVG(r.rating), 0) >= ?"
        having_params.append(min_rating - 1e-9)

    all_params = params + having_params
    total = conn.execute(f"SELECT COUNT(*) FROM ({sql})", all_params).fetchone()[0]

    sql += f" ORDER BY {SORT_OPTIONS[sort]} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, all_params + [limit, offset]).fetchall()
    return [_row_to_product(r) for r in rows], total


def get_product(conn: sqlite3.Connection, product_id: int) -> dict:
    row = conn.execute(_SELECT + " WHERE p.id = ? GROUP BY p.id", (product_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Product {product_id} was not found.", code="product_not_found")
    return _row_to_product(row)


def get_product_rating(conn: sqlite3.Connection, product_id: int) -> dict:
    product = get_product(conn, product_id)
    return {
        "product_id": product["id"],
        "name": product["name"],
        "average_rating": product["average_rating"],
        "review_count": product["review_count"],
    }


def list_reviews(conn: sqlite3.Connection, product_id: int, limit: int = 100) -> list:
    get_product(conn, product_id)  # raises NotFoundError for an unknown id
    rows = conn.execute(
        "SELECT id, product_id, rating, reviewer_name, review_text FROM reviews "
        "WHERE product_id = ? ORDER BY id LIMIT ?",
        (product_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def list_categories(conn: sqlite3.Connection) -> list:
    rows = conn.execute(
        "SELECT category, COUNT(*) AS product_count FROM products "
        "WHERE category IS NOT NULL GROUP BY category ORDER BY category"
    ).fetchall()
    return [{"category": r["category"], "product_count": r["product_count"]} for r in rows]


def compare_products(conn: sqlite3.Connection, product_ids: list) -> dict:
    """Compare 2-4 products using real database values."""
    ids = list(dict.fromkeys(product_ids))  # remove duplicates, keep order
    if len(ids) < 2:
        raise BadRequestError("Choose at least 2 different products to compare.", code="compare_too_few")
    if len(ids) > 4:
        raise BadRequestError("You can compare at most 4 products at once.", code="compare_too_many")

    products, missing = [], []
    for pid in ids:
        try:
            products.append(get_product(conn, pid))
        except NotFoundError:
            missing.append(pid)
    if missing:
        raise NotFoundError(f"Products not found: {missing}.", code="product_not_found")

    cheapest = min(products, key=lambda p: (p["price"], p["id"]))
    best_rated = max(products, key=lambda p: (p["average_rating"], p["review_count"], -p["id"]))
    most_reviewed = max(products, key=lambda p: (p["review_count"], -p["id"]))
    prices = [p["price"] for p in products]
    return {
        "products": products,
        "highlights": {
            "cheapest_id": cheapest["id"],
            "highest_rated_id": best_rated["id"],
            "most_reviewed_id": most_reviewed["id"],
            "price_difference": round(max(prices) - min(prices), 2),
            "same_category": len({p["category"] for p in products}) == 1,
            "organic_ids": [p["id"] for p in products if p["is_organic"]],
        },
    }


def recommend_products(
    conn: sqlite3.Connection,
    query: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    is_organic: Optional[bool] = None,
    limit: int = 5,
) -> list:
    """Best matches for the stated preferences: highest rating first, then most reviews, then cheaper.

    Each result has a `reason` built only from real data.
    """
    items, _ = list_products(
        conn,
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        is_organic=is_organic,
        sort="rating_desc",
        limit=50,
    )
    # Products with no reviews should not outrank reviewed ones.
    items.sort(key=lambda p: (-p["average_rating"], -p["review_count"], p["price"], p["id"]))
    top = items[:limit]
    for p in top:
        parts = []
        if p["review_count"]:
            parts.append(f"rated {p['average_rating']:.2f} stars from {p['review_count']} reviews")
        else:
            parts.append("no reviews yet")
        parts.append(f"${p['price']:.2f}")
        if p["is_organic"]:
            parts.append("organic")
        p["reason"] = ", ".join(parts)
    return top
