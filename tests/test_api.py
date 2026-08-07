from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from console.api import create_app


def test_empty_api_has_explicit_empty_and_not_found_contracts(tmp_path) -> None:
    app = create_app(tmp_path, bootstrap=False)
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {
            "status": "ok",
            "sample_data": True,
            "latest_snapshot": None,
        }
        summary = client.get("/api/account/summary")
        assert summary.status_code == 404
        assert summary.json()["detail"] == "demo snapshot not found"
        assert client.get("/api/account/history").json() == []
        assert client.get("/api/account/holdings").json() == {
            "asof": None,
            "items": [],
            "sample_data": True,
        }
        assert client.get("/api/pipeline/status").json() == {
            "generated_at": None,
            "sample_data": True,
            "stages": [],
        }


def test_seeded_api_returns_only_labelled_sample_data(tmp_path) -> None:
    app = create_app(tmp_path, bootstrap=True)
    with TestClient(app) as client:
        summary = client.get("/api/account/summary")
        assert summary.status_code == 200
        assert summary.json()["sample_data"] is True
        assert summary.json()["asof"]

        history = client.get("/api/account/history", params={"days": 365})
        assert history.status_code == 200
        assert len(history.json()) == 45
        assert [point["asof"] for point in history.json()] == sorted(
            point["asof"] for point in history.json()
        )

        holdings = client.get("/api/account/holdings").json()
        assert holdings["sample_data"] is True
        assert [item["symbol"] for item in holdings["items"]] == [
            "SAMPLE-A",
            "SAMPLE-B",
            "SAMPLE-C",
        ]

        pipeline = client.get("/api/pipeline/status")
        assert pipeline.status_code == 200
        assert pipeline.json()["sample_data"] is True
        assert len(pipeline.json()["stages"]) == 4


@pytest.mark.parametrize("days", ["0", "366", "-1", "not-a-number"])
def test_history_days_are_bounded(tmp_path, days: str) -> None:
    app = create_app(tmp_path, bootstrap=False)
    with TestClient(app) as client:
        response = client.get("/api/account/history", params={"days": days})
    assert response.status_code == 422


def test_corrupt_pipeline_report_returns_controlled_503(tmp_path) -> None:
    app = create_app(tmp_path, bootstrap=False)
    (tmp_path / "pipeline-report.json").write_text("{not-json", encoding="utf-8")
    with TestClient(app) as client:
        response = client.get("/api/pipeline/status")
    assert response.status_code == 503
    assert response.json()["detail"] == "demo pipeline report unavailable"


def test_invalid_pipeline_report_shape_returns_controlled_503(tmp_path) -> None:
    app = create_app(tmp_path, bootstrap=False)
    (tmp_path / "pipeline-report.json").write_text(
        '{"generated_at": [], "sample_data": true, "stages": "invalid"}',
        encoding="utf-8",
    )
    with TestClient(app) as client:
        response = client.get("/api/pipeline/status")
    assert response.status_code == 503
    assert response.json()["detail"] == "demo pipeline report unavailable"


def test_corrupt_snapshot_database_returns_controlled_503(tmp_path) -> None:
    app = create_app(tmp_path, bootstrap=False)
    app.state.snapshot_store.close()
    (tmp_path / "demo.db").write_bytes(b"not a sqlite database")
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json()["detail"] == "demo data store unavailable"
