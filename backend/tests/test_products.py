import pytest

from app.services import product_service as ps
from app.utils.errors import BadRequestError, NotFoundError


def ids(items):
    return {p["id"] for p in items}


def test_keyword_search_finds_honey(db):
    items, total = ps.list_products(db, query="honey", category="honey")
    assert total == 8
    assert all(p["category"] == "honey" for p in items)


def test_plural_keyword_matches(db):
    items, _ = ps.list_products(db, query="almonds")
    assert 13 in ids(items)  # Organic Almonds
    items, _ = ps.list_products(db, query="nuts", category="nuts")
    assert ids(items) == {13, 14, 16}


def test_price_filter(db):
    items, _ = ps.list_products(db, category="honey", max_price=12.99)
    assert ids(items) == {2, 4, 8}
    assert all(p["price"] <= 12.99 for p in items)


def test_organic_filter(db):
    organic, _ = ps.list_products(db, category="honey", is_organic=True)
    non_organic, _ = ps.list_products(db, category="honey", is_organic=False)
    assert ids(organic) == {1, 3, 5, 7}
    assert ids(non_organic) == {2, 4, 6, 8}


def test_combined_filters_match_the_mentors_example(db):
    # "organic honey with 4.5+ rating and less than $20"
    items, total = ps.list_products(db, category="honey", is_organic=True, max_price=20, min_rating=4.5)
    assert total == 3
    assert ids(items) == {1, 5, 7}


def test_rating_is_calculated_from_reviews(db):
    # Product 1 has ratings 5.0, 4.0, 5.0, 4.5 -> average 4.625, 4 reviews
    rating = ps.get_product_rating(db, 1)
    assert rating["review_count"] == 4
    assert rating["average_rating"] == pytest.approx(4.625, abs=0.01)
    # Product 3 has 5.0, 4.5, 5.0 -> 4.8333
    assert ps.get_product_rating(db, 3)["average_rating"] == pytest.approx(4.83, abs=0.01)


def test_product_without_reviews_has_zero_rating(db):
    db.execute("INSERT INTO products (id, name, category, price, description, is_organic) VALUES (500, 'New thing', 'snacks', 3.0, 'd', 0)")
    product = ps.get_product(db, 500)
    assert product["average_rating"] == 0.0 and product["review_count"] == 0


def test_invalid_product_id_is_rejected(db):
    with pytest.raises(NotFoundError):
        ps.get_product(db, 9999)
    with pytest.raises(NotFoundError):
        ps.list_reviews(db, 9999)


def test_bad_filters_are_rejected(db):
    with pytest.raises(BadRequestError):
        ps.list_products(db, min_price=20, max_price=5)
    with pytest.raises(BadRequestError):
        ps.list_products(db, sort="drop table")


def test_sql_injection_text_is_treated_as_plain_text(db):
    items, total = ps.list_products(db, query="'; DROP TABLE products; --")
    assert total == 0
    assert db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 32


def test_sorting(db):
    items, _ = ps.list_products(db, category="honey", sort="price_asc")
    prices = [p["price"] for p in items]
    assert prices == sorted(prices)
    items, _ = ps.list_products(db, category="honey", sort="rating_desc")
    ratings = [p["average_rating"] for p in items]
    assert ratings == sorted(ratings, reverse=True)


def test_compare_products(db):
    result = ps.compare_products(db, [13, 14])  # almonds vs cashews
    assert [p["id"] for p in result["products"]] == [13, 14]
    highlights = result["highlights"]
    assert highlights["cheapest_id"] == 14  # 9.99 < 11.99
    assert highlights["highest_rated_id"] == 13  # 4.75 > 4.0
    assert highlights["same_category"] is True
    assert highlights["organic_ids"] == [13]


def test_compare_needs_two_valid_products(db):
    with pytest.raises(BadRequestError):
        ps.compare_products(db, [1])
    with pytest.raises(BadRequestError):
        ps.compare_products(db, [1, 1])  # duplicates collapse to one
    with pytest.raises(NotFoundError):
        ps.compare_products(db, [1, 9999])


def test_recommendations_are_ranked_and_explained(db):
    items = ps.recommend_products(db, category="honey", is_organic=True, max_price=20, limit=3)
    assert [p["id"] for p in items] == [7, 1, 5]
    assert items[0]["average_rating"] >= items[-1]["average_rating"]
    assert "rated" in items[0]["reason"] and "$" in items[0]["reason"]
