"""Tools the AI agent can call.

A "tool" is a normal Python function that the language model may ask us to run.
LangChain shows the model each tool's name, arguments and docstring, so the docstrings
below are written for the MODEL: they tell it when and how to use the tool.

All tools read real data through the same services the REST API uses, and they return
JSON text. Tools never invent data, and NO tool places an order: `prepare_order` only
builds a summary that the person must confirm on the checkout screen.
"""

import json
from typing import Optional

from langchain.tools import tool

from app.config import get_settings
from app.database import db_session
from app.schemas import CartItemIn
from app.services import image_service, order_service, product_service
from app.utils.errors import AppError


def _to_json(fn) -> str:
    """Run fn() and return JSON. Known errors become {"error": "..."} so the agent can explain them."""
    try:
        return json.dumps(fn())
    except AppError as exc:
        return json.dumps({"error": exc.message})


def _with_db(fn) -> str:
    def run():
        with db_session() as conn:
            return fn(conn)

    return _to_json(run)


def _slim(product: dict) -> dict:
    keys = ("id", "name", "category", "price", "is_organic", "average_rating", "review_count", "description", "reason")
    return {k: product[k] for k in keys if k in product}


@tool
def search_products(
    query: str = "",
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_organic: Optional[bool] = None,
    min_rating: Optional[float] = None,
) -> str:
    """Search the store catalog. Every filter is optional.

    - query: keywords such as "almonds" or "olive oil" (matched against name, description and category).
      Do NOT put words like "organic", "cheap" or "under 20" in the query; use the filters instead.
    - category: one exact catalog category (for example "honey", "oil", "nuts") when the user names a product type.
    - min_price / max_price: price limits in dollars.
    - is_organic: true for organic-only, false for non-organic only, omit if the user did not say.
    - min_rating: minimum average star rating (0-5), applied using real review data.

    Returns JSON: {"count": N, "products": [{id, name, category, price, is_organic, average_rating, review_count, description}]}.
    The ratings in the result are already calculated; you do not need another call to get them.
    """

    def run(conn):
        items, total = product_service.list_products(
            conn,
            query=query or None,
            category=category,
            min_price=min_price,
            max_price=max_price,
            is_organic=is_organic,
            min_rating=min_rating,
            sort="rating_desc",
            limit=10,
        )
        result = {"count": len(items), "total_matches": total, "products": [_slim(p) for p in items]}
        if not items:
            result["hint"] = "No products matched. Suggest relaxing one filter (price, rating or organic)."
        return result

    return _with_db(run)


@tool
def get_product_rating(product_id: int) -> str:
    """Get the average customer rating and number of reviews for ONE product by its numeric id.
    Returns JSON: {product_id, name, average_rating, review_count}."""
    return _with_db(lambda conn: product_service.get_product_rating(conn, product_id))


@tool
def compare_products(product_ids: list[int]) -> str:
    """Compare 2 to 4 products side by side using real database values (price, category, rating, reviews, organic).
    First find the products with search_products to get their ids. Returns JSON with "products" and "highlights"
    (cheapest_id, highest_rated_id, most_reviewed_id, price_difference, same_category, organic_ids)."""
    return _with_db(lambda conn: product_service.compare_products(conn, product_ids))


@tool
def recommend_products(
    query: str = "",
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_organic: Optional[bool] = None,
    min_rating: Optional[float] = None,
    limit: int = 3,
) -> str:
    """Recommend the best products for the user's stated preferences. Use this when the user asks you to
    recommend, suggest or pick the best option. Ranking: highest average rating, then most reviews, then lower price.
    Each product includes a "reason" built from real data. Filters work like search_products. limit is 1-5.
    Returns JSON: {"count": N, "products": [...]}."""

    def run(conn):
        items = product_service.recommend_products(
            conn,
            query=query or None,
            category=category,
            min_price=min_price,
            max_price=max_price,
            is_organic=is_organic,
            min_rating=min_rating,
            limit=max(1, min(limit, 5)),
        )
        result = {"count": len(items), "products": [_slim(p) for p in items]}
        if not items:
            result["hint"] = "No products matched. Suggest relaxing one filter."
        return result

    return _with_db(run)


@tool
def analyze_product_image(image_id: str) -> str:
    """Look at a product photo the user uploaded and describe it. Use this only when the user's message says
    they attached an image, and pass the image_id given in that message.
    Returns JSON: {product_type, search_keywords, is_organic, visual_characteristics, description}.
    Afterwards call search_products with these keywords. Image matching is keyword-based, so tell the user
    the matches are approximate."""

    def run():
        data, mime = image_service.load_upload(get_settings().upload_dir, image_id)
        analysis = image_service.analyze_image_bytes(data, mime)
        return analysis.model_dump()

    return _to_json(run)


@tool
def prepare_order(items: list[CartItemIn]) -> str:
    """Prepare an order summary for products the user has chosen. This does NOT place an order and nothing is bought.
    Call it only when the user clearly says they want to buy specific product(s); pass product ids from earlier tool
    results (never guess ids) and quantities (default 1). The app then shows the person an order summary that they
    must confirm themselves on the checkout screen. Returns JSON with the validated summary and real total."""

    def run(conn):
        cart = order_service.validate_cart(conn, [i.model_dump() for i in items])
        return {
            "order_not_placed": True,
            "requires_user_confirmation": True,
            "summary": cart,
            "message": "Summary prepared. The user must review and confirm it on the checkout screen.",
        }

    return _with_db(run)


ALL_TOOLS = [
    search_products,
    get_product_rating,
    compare_products,
    recommend_products,
    analyze_product_image,
    prepare_order,
]
