from __future__ import annotations

from datetime import date

from datastore.candle_store import CandleStore
from datastore.snapshot_store import SnapshotStore
from operation.demo_pipeline import business_dates, read_report, seed_demo


def test_business_dates_skip_weekends() -> None:
    dates = business_dates(date(2026, 8, 9), 3)  # Sunday
    assert dates == [date(2026, 8, 5), date(2026, 8, 6), date(2026, 8, 7)]


def test_seed_is_deterministic_date_idempotent_and_offline(tmp_path) -> None:
    asof = date(2026, 8, 7)
    first = seed_demo(tmp_path, asof)
    second = seed_demo(tmp_path, asof)

    assert first == second
    assert first.snapshots == 45
    assert first.candle_symbols == 5
    assert first.candle_rows == 150
    assert first.fx_rows == 1

    snapshots = SnapshotStore(f"sqlite:///{tmp_path / 'demo.db'}")
    try:
        assert snapshots.count() == 45
        assert snapshots.latest() is not None
        assert snapshots.latest().asof == asof
    finally:
        snapshots.close()

    market = CandleStore(tmp_path / "market")
    assert market.status() == {
        "symbols": 5,
        "rows": 150,
        "latest_universe": asof.isoformat(),
        "fx_rows": 1,
    }
    for symbol in ("SAMPLE-A", "SAMPLE-B", "SAMPLE-C", "SAMPLE-D", "SAMPLE-E"):
        frame = market.read(symbol)
        assert frame is not None
        assert frame["date"].is_monotonic_increasing
        assert frame["date"].is_unique

    report = read_report(tmp_path / "pipeline-report.json")
    assert report is not None
    assert report["sample_data"] is True
    assert [stage["status"] for stage in report["stages"]] == ["DONE"] * 4
    assert "외부 네트워크 요청 없음" in report["stages"][0]["detail"]
