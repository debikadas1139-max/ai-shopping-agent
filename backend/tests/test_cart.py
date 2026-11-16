from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cart_validation():
    response = client.post("/api/cart/validate", json={
        "items": [{"product_id": 1, "quantity": 2}]
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["subtotal"] > 0
