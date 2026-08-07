from __future__ import annotations

import sys

import pytest

from scripts import dashboard, health_check, seed_demo


def test_seed_and_health_scripts_are_repeatable(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["seed_demo", "--root", str(tmp_path), "--asof", "2026-08-07"],
    )
    seed_demo.main()
    seed_demo.main()
    assert "DEMO READY snapshots=45 symbols=5 rows=150 fx_rows=1" in capsys.readouterr().out

    monkeypatch.setattr(
        sys,
        "argv",
        ["health_check", "--root", str(tmp_path), "--asof", "2026-08-07"],
    )
    health_check.main()
    assert "HEALTH OK synthetic=true outbound_requests=0" in capsys.readouterr().out


def test_reset_refuses_to_delete_outside_repository_data(tmp_path, monkeypatch) -> None:
    marker = tmp_path / "keep.txt"
    marker.write_text("safe", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["seed_demo", "--root", str(tmp_path), "--reset"])
    with pytest.raises(SystemExit, match="reset target must be under"):
        seed_demo.main()
    assert marker.read_text(encoding="utf-8") == "safe"


def test_dashboard_rejects_external_bind_and_accepts_localhost(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["dashboard", "--host", "0.0.0.0"])
    with pytest.raises(SystemExit, match="localhost only"):
        dashboard.main()

    sentinel = object()
    called = {}
    monkeypatch.setattr(dashboard, "create_app", lambda _root: sentinel)
    monkeypatch.setattr(
        dashboard.uvicorn,
        "run",
        lambda app, host, port: called.update(app=app, host=host, port=port),
    )
    monkeypatch.setattr(sys, "argv", ["dashboard", "--host", "localhost", "--port", "9000"])
    dashboard.main()
    assert called == {"app": sentinel, "host": "localhost", "port": 9000}
