from __future__ import annotations

from datetime import date

import pytest

from datastore.snapshot_store import SnapshotStore
from operation.models import AccountSnapshot, Holding


def snapshot(
    asof: date,
    total: float,
    *symbols: str,
) -> AccountSnapshot:
    holdings = tuple(
        Holding(
            symbol=symbol,
            name=f"샘플 {symbol}",
            market="DEMO",
            quantity=index + 1,
            last_price=1_000 + index * 100,
            average_price=900 + index * 100,
        )
        for index, symbol in enumerate(symbols)
    )
    return AccountSnapshot(
        asof=asof,
        total_krw=total,
        cash_krw=total * 0.2,
        invested_krw=total * 0.8,
        pnl_rate=0.1,
        daily_pnl_rate=0.01,
        holdings=holdings,
    )


def test_same_date_save_replaces_summary_and_holdings_atomically(tmp_path) -> None:
    db_path = tmp_path / "snapshots.db"
    store = SnapshotStore(f"sqlite:///{db_path}")
    try:
        asof = date(2026, 8, 7)
        store.save(snapshot(asof, 10_000, "SAMPLE-A", "SAMPLE-B"))
        store.save(snapshot(asof, 12_500, "SAMPLE-C"))

        latest = store.latest()
        assert latest is not None
        assert store.count() == 1
        assert latest.total_krw == 12_500
        assert [holding.symbol for holding in latest.holdings] == ["SAMPLE-C"]
    finally:
        store.close()

    # NullPool releases the SQLite file on Windows as well as POSIX.
    db_path.unlink()
    assert not db_path.exists()


def test_duplicate_holding_symbols_are_rejected_without_destroying_previous_data(tmp_path) -> None:
    store = SnapshotStore(f"sqlite:///{tmp_path / 'snapshots.db'}")
    try:
        asof = date(2026, 8, 7)
        original = snapshot(asof, 10_000, "SAMPLE-A")
        duplicate = AccountSnapshot(
            asof=asof,
            total_krw=20_000,
            cash_krw=4_000,
            invested_krw=16_000,
            pnl_rate=0.2,
            daily_pnl_rate=0.02,
            holdings=(original.holdings[0], original.holdings[0]),
        )
        store.save(original)

        with pytest.raises(ValueError, match="unique"):
            store.save(duplicate)

        assert store.latest() == original
        assert store.count() == 1
    finally:
        store.close()


def test_history_uses_latest_snapshot_as_cutoff_and_returns_ascending_dates(tmp_path) -> None:
    store = SnapshotStore(f"sqlite:///{tmp_path / 'snapshots.db'}")
    try:
        for asof in (date(2026, 8, 1), date(2026, 8, 3), date(2026, 8, 6)):
            store.save(snapshot(asof, 10_000, "SAMPLE-A"))

        assert [item.asof for item in store.history(6)] == [
            date(2026, 8, 1),
            date(2026, 8, 3),
            date(2026, 8, 6),
        ]
        assert [item.asof for item in store.history(3)] == [date(2026, 8, 6)]
        with pytest.raises(ValueError, match="positive"):
            store.history(0)
    finally:
        store.close()


def test_in_memory_store_is_shared_across_sessions() -> None:
    store = SnapshotStore("sqlite:///:memory:")
    try:
        store.save(snapshot(date(2026, 8, 7), 10_000, "SAMPLE-A"))
        assert store.count() == 1
        assert store.latest() is not None
    finally:
        store.close()
