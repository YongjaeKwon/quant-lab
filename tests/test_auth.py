from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_success() -> None:
    response = client.post("/api/auth/login", json={"username": "demo", "password": "demo-pass"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_failure() -> None:
    response = client.post("/api/auth/login", json={"username": "demo", "password": "wrong"})
    assert response.status_code == 401
