"""API tests using FastAPI's TestClient (needs fastapi + httpx installed, but no AI key)."""

import uuid

from app.utils.errors import UpstreamError

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok" and body["database"] == "ok"
    assert "groq_api_key" not in str(body).lower()


def test_product_search_and_filters(client):
    response = client.get("/api/products", params={"category": "honey", "is_organic": "true", "max_price": 20, "min_rating": 4.5})
    assert response.status_code == 200
    body = response.json()
    assert {p["id"] for p in body["items"]} == {1, 5, 7}
    assert body["total"] == 3
    assert {"average_rating", "review_count"} <= set(body["items"][0])


def test_categories_route_is_not_shadowed_by_product_id(client):
    response = client.get("/api/products/categories")
    assert response.status_code == 200
    assert "honey" in [c["category"] for c in response.json()]


def test_product_detail_and_reviews(client):
    assert client.get("/api/products/1").json()["name"] == "Organic Raw Honey"
    assert len(client.get("/api/products/1/reviews").json()) == 4


def test_unknown_and_malformed_product_ids(client):
    missing = client.get("/api/products/9999")
    assert missing.status_code == 404 and missing.json()["code"] == "product_not_found"
    assert client.get("/api/products/abc").status_code == 422
    assert client.get("/api/products", params={"min_price": 20, "max_price": 5}).status_code == 400
    assert client.get("/api/products", params={"min_rating": 9}).status_code == 422


def test_compare_endpoint(client):
    response = client.post("/api/compare", json={"product_ids": [13, 14]})
    assert response.status_code == 200
    assert response.json()["highlights"]["cheapest_id"] == 14
    assert client.post("/api/compare", json={"product_ids": [13]}).status_code == 422
    assert client.post("/api/compare", json={"product_ids": [13, 9999]}).status_code == 404


def test_cart_validation_uses_backend_prices(client):
    response = client.post("/api/cart/validate", json={"items": [{"product_id": 1, "quantity": 3}]})
    assert response.status_code == 200 and response.json()["total"] == 44.97
    # A client-supplied price is rejected, never trusted.
    tampered = client.post("/api/cart/validate", json={"items": [{"product_id": 1, "quantity": 1, "price": 0.01}]})
    assert tampered.status_code == 422
    assert client.post("/api/cart/validate", json={"items": [{"product_id": 9999, "quantity": 1}]}).status_code == 404
    assert client.post("/api/cart/validate", json={"items": [{"product_id": 1, "quantity": 0}]}).status_code == 422


def order_payload(**overrides):
    payload = {
        "items": [{"product_id": 1, "quantity": 2}],
        "confirmed": True,
        "confirmed_total": 29.98,
        "idempotency_key": uuid.uuid4().hex,
    }
    payload.update(overrides)
    return payload


def test_order_requires_confirmation(client):
    response = client.post("/api/orders", json=order_payload(confirmed=False))
    assert response.status_code == 400 and response.json()["code"] == "confirmation_required"
    assert client.get("/api/orders").json() == []


def test_order_flow_and_duplicate_protection(client):
    payload = order_payload()
    first = client.post("/api/orders", json=payload)
    assert first.status_code == 201
    order = first.json()
    assert order["total_amount"] == 29.98 and order["items"][0]["quantity"] == 2

    retry = client.post("/api/orders", json=payload)  # same idempotency key
    assert retry.status_code == 200
    assert retry.json()["id"] == order["id"] and retry.json()["duplicate_request"] is True

    assert len(client.get("/api/orders").json()) == 1
    assert client.get(f"/api/orders/{order['id']}").json()["id"] == order["id"]
    assert client.get("/api/orders/9999").status_code == 404


def test_order_with_wrong_total_is_rejected(client):
    response = client.post("/api/orders", json=order_payload(confirmed_total=0.5))
    assert response.status_code == 409 and response.json()["code"] == "total_mismatch"


def test_image_upload_validation(client):
    not_an_image = client.post("/api/image-search", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert not_an_image.status_code == 415
    fake = client.post("/api/image-search", files={"file": ("fake.jpg", b"not really a jpeg", "image/jpeg")})
    assert fake.status_code == 415
    assert client.post("/api/image-search").status_code == 422  # no file at all


def test_image_search_success_with_mocked_vision_model(client, monkeypatch, tmp_path):
    from app.config import get_settings
    from app.schemas import ImageAnalysis

    monkeypatch.setattr("app.api.image_search.get_settings", lambda: _settings_with_upload_dir(get_settings(), tmp_path / "uploads"))
    monkeypatch.setattr(
        "app.api.image_search.analyze_image_bytes",
        lambda data, mime: ImageAnalysis(product_type="honey", search_keywords=["honey"], is_organic=True,
                                         visual_characteristics=["glass jar"], description="A jar of honey."),
    )
    response = client.post("/api/image-search", files={"file": ("jar.jpg", JPEG, "image/jpeg")})
    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["product_type"] == "honey"
    assert body["matches"] and all(m["is_organic"] for m in body["matches"])
    assert "approximate" in body["note"].lower()


def test_image_analysis_failure_is_reported_not_crashed(client, monkeypatch, tmp_path):
    from app.config import get_settings

    monkeypatch.setattr("app.api.image_search.get_settings", lambda: _settings_with_upload_dir(get_settings(), tmp_path / "uploads"))

    def boom(data, mime):
        raise UpstreamError("The AI model request failed. Please try again.")

    monkeypatch.setattr("app.api.image_search.analyze_image_bytes", boom)
    response = client.post("/api/image-search", files={"file": ("jar.jpg", JPEG, "image/jpeg")})
    assert response.status_code == 502
    assert "failed" in response.json()["detail"]
    assert client.get("/api/health").status_code == 200  # server still fine
    assert list((tmp_path / "uploads").iterdir()) == []  # temporary upload cleaned up


def test_chat_without_api_key_returns_clear_error(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("GROQ_API_KEY", "")
    get_settings.cache_clear()
    try:
        response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "organic honey"}]})
        assert response.status_code == 503
        assert response.json()["code"] == "ai_not_configured"
    finally:
        get_settings.cache_clear()


def test_chat_returns_agent_result(client, monkeypatch):
    fake = {"reply": "Here you go", "products": [], "comparison": None, "order_proposal": None, "tools_used": ["search_products"]}
    monkeypatch.setattr("app.api.chat.run_agent", lambda messages, image_id: fake)
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hello"}]})
    assert response.status_code == 200 and response.json()["reply"] == "Here you go"


def test_chat_request_validation(client):
    assert client.post("/api/chat", json={"messages": []}).status_code == 422
    assert client.post("/api/chat", json={"messages": [{"role": "assistant", "content": "hi"}]}).status_code == 422
    assert client.post("/api/chat", json={"messages": [{"role": "user", "content": ""}]}).status_code == 422


def _settings_with_upload_dir(settings, upload_dir):
    from dataclasses import replace

    return replace(settings, upload_dir=upload_dir)
