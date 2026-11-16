"""Tests for how agent output is turned into an API response (no AI key or network needed)."""

import json
from types import SimpleNamespace

from app.agent.shopping_agent import build_history, build_result


def msg(kind, content="", name=None):
    return SimpleNamespace(type=kind, content=content, name=name)


PRODUCT = {"id": 1, "name": "Organic Raw Honey", "category": "honey", "price": 14.99, "is_organic": True,
           "average_rating": 4.63, "review_count": 4, "description": "x"}


def test_search_results_become_product_cards():
    messages = [
        msg("human", "old question"),
        msg("ai", "old answer"),
        msg("human", "organic honey under $20"),
        msg("ai", ""),
        msg("tool", json.dumps({"count": 1, "products": [PRODUCT]}), "search_products"),
        msg("ai", "<think>x</think>Organic Raw Honey is $14.99 and rated 4.63."),
    ]
    result = build_result(messages)
    assert result["reply"] == "Organic Raw Honey is $14.99 and rated 4.63."
    assert result["products"][0]["id"] == 1
    assert result["tools_used"] == ["search_products"]
    assert result["order_proposal"] is None


def test_only_the_current_turn_is_used():
    messages = [
        msg("human", "first"),
        msg("tool", json.dumps({"products": [PRODUCT]}), "search_products"),
        msg("ai", "first answer"),
        msg("human", "thanks"),
        msg("ai", "You're welcome!"),
    ]
    result = build_result(messages)
    assert result["products"] == [] and result["tools_used"] == []


def test_order_proposal_is_extracted_and_errors_are_ignored():
    cart = {"items": [], "total": 14.99, "item_count": 1}
    messages = [
        msg("human", "I'll take the honey"),
        msg("tool", json.dumps({"error": "Products not found"}), "search_products"),
        msg("tool", json.dumps({"order_not_placed": True, "summary": cart}), "prepare_order"),
        msg("ai", "Please review and confirm below."),
    ]
    result = build_result(messages)
    assert result["order_proposal"] == cart
    assert result["products"] == []


def test_history_gets_product_ids_and_image_note():
    history = build_history(
        [
            {"role": "user", "content": "organic honey"},
            {"role": "assistant", "content": "Here you go", "shown_products": [{"id": 1, "name": "Organic Raw Honey"}]},
            {"role": "user", "content": "order the first one"},
        ],
        image_id="a" * 32,
    )
    assert "(ID:1)" in history[1]["content"]
    assert "image_id=" + "a" * 32 in history[2]["content"]
