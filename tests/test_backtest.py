from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _token() -> str:
    response = client.post("/api/auth/login", json={"username": "demo", "password": "demo-pass"})
    return response.json()["access_token"]


def test_backtest_requires_auth() -> None:
    response = client.post("/api/backtests/run", json={"symbol": "DEMO-BTC"})
    assert response.status_code == 401


def test_backtest_returns_curve_and_trades() -> None:
    response = client.post(
        "/api/backtests/run",
        headers={"Authorization": f"Bearer {_token()}"},
        json={"symbol": "DEMO-BTC", "start_cash": 10000, "short_window": 5, "long_window": 20},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["run_id"]
    assert data["symbol"] == "DEMO-BTC"
    assert data["equity_curve"]
    assert "total_return_pct" in data
