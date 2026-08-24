from fastapi.testclient import TestClient

from src.api import api


client = TestClient(api)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint():
    response = client.post(
        "/api/chat", json={"message": "查询订单 9003", "session_id": "api-test"}
    )

    assert response.status_code == 200
    assert response.json()["intent"] == "order_inquiry"
