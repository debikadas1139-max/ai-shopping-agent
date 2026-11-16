import pytest

from app.services import order_service as os_
from app.utils.errors import BadRequestError, ConflictError, NotFoundError

KEY = "test-key-0001"


def order_count(db):
    return db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]


def test_backend_calculates_totals(db):
    cart = os_.validate_cart(db, [{"product_id": 1, "quantity": 3}, {"product_id": 13, "quantity": 2}])
    assert cart["total"] == pytest.approx(14.99 * 3 + 11.99 * 2)  # 44.97 + 23.98 = 68.95
    assert cart["total"] == 68.95
    assert cart["item_count"] == 5
    assert cart["items"][0]["line_total"] == 44.97


def test_duplicate_lines_are_merged(db):
    cart = os_.validate_cart(db, [{"product_id": 1, "quantity": 1}, {"product_id": 1, "quantity": 2}])
    assert len(cart["items"]) == 1 and cart["items"][0]["quantity"] == 3


@pytest.mark.parametrize(
    "items",
    [
        [],
        [{"product_id": 9999, "quantity": 1}],
        [{"product_id": 1, "quantity": 0}],
        [{"product_id": 1, "quantity": -2}],
        [{"product_id": 1, "quantity": 100}],
        [{"product_id": 1, "quantity": 1.5}],
        [{"product_id": "1", "quantity": 1}],
        [{"product_id": 1}],
    ],
)
def test_invalid_carts_are_rejected(db, items):
    with pytest.raises((BadRequestError, NotFoundError)):
        os_.validate_cart(db, items)


def test_order_requires_explicit_confirmation(db):
    with pytest.raises(BadRequestError) as info:
        os_.create_order(db, [{"product_id": 1, "quantity": 1}], confirmed=False, confirmed_total=14.99, idempotency_key=KEY)
    assert info.value.code == "confirmation_required"
    assert order_count(db) == 0


def test_successful_order_is_saved_with_snapshots(db):
    order = os_.create_order(
        db, [{"product_id": 1, "quantity": 2}], confirmed=True, confirmed_total=29.98, idempotency_key=KEY
    )
    assert order["total_amount"] == 29.98 and order["status"] == "confirmed"
    assert order["duplicate_request"] is False
    assert order["items"][0]["product_name"] == "Organic Raw Honey"
    assert order["items"][0]["unit_price"] == 14.99 and order["items"][0]["line_total"] == 29.98
    # Later price changes must not alter the saved order.
    db.execute("UPDATE products SET price = 50 WHERE id = 1")
    assert os_.get_order(db, order["id"])["total_amount"] == 29.98


def test_retry_with_same_key_does_not_create_a_second_order(db):
    items = [{"product_id": 1, "quantity": 2}]
    first = os_.create_order(db, items, True, 29.98, KEY)
    second = os_.create_order(db, items, True, 29.98, KEY)
    assert second["id"] == first["id"]
    assert second["duplicate_request"] is True
    assert order_count(db) == 1
    assert db.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 1


def test_same_key_with_a_different_cart_is_a_conflict(db):
    os_.create_order(db, [{"product_id": 1, "quantity": 1}], True, 14.99, KEY)
    with pytest.raises(ConflictError) as info:
        os_.create_order(db, [{"product_id": 13, "quantity": 1}], True, 11.99, KEY)
    assert info.value.code == "idempotency_conflict"
    assert order_count(db) == 1


def test_wrong_total_from_the_client_is_rejected(db):
    with pytest.raises(ConflictError) as info:
        os_.create_order(db, [{"product_id": 1, "quantity": 1}], True, 1.00, KEY)
    assert info.value.code == "total_mismatch"
    assert order_count(db) == 0


def test_bad_idempotency_key_is_rejected(db):
    with pytest.raises(BadRequestError):
        os_.create_order(db, [{"product_id": 1, "quantity": 1}], True, 14.99, "short")


def test_failed_order_leaves_nothing_behind(db):
    # Force a failure in the middle of the transaction: order row inserted, then item insert fails.
    db.execute("CREATE TRIGGER block_items BEFORE INSERT ON order_items BEGIN SELECT RAISE(ABORT, 'boom'); END")
    with pytest.raises(Exception):
        os_.create_order(db, [{"product_id": 1, "quantity": 1}], True, 14.99, KEY)
    assert order_count(db) == 0


def test_order_history_lists_newest_first(db):
    a = os_.create_order(db, [{"product_id": 1, "quantity": 1}], True, 14.99, "key-aaaaaaaa")
    b = os_.create_order(db, [{"product_id": 13, "quantity": 1}], True, 11.99, "key-bbbbbbbb")
    history = os_.list_orders(db)
    assert [o["id"] for o in history] == [b["id"], a["id"]]
    with pytest.raises(NotFoundError):
        os_.get_order(db, 9999)
