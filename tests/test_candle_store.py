from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from datastore.candle_store import REQUIRED_COLUMNS, CandleStore


def candles(rows: list[tuple[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": day,
                "open": close - 1,
                "high": close + 2,
                "low": close - 2,
                "close": close,
                "volume": 1_000,
            }
            for day, close in rows
        ],
        columns=REQUIRED_COLUMNS,
    )


def test_parquet_upsert_sorts_deduplicates_and_counts_only_new_dates(tmp_path) -> None:
    store = CandleStore(tmp_path)
    first = candles(
        [
            ("2026-08-02", 102),
            ("2026-08-01", 100),
            ("2026-08-01", 101),
        ]
    )
    assert store.upsert("SAMPLE-A", first) == 2

    second = candles([("2026-08-02", 202), ("2026-08-03", 103)])
    assert store.upsert("SAMPLE-A", second) == 1

    saved = store.read("SAMPLE-A")
    assert saved is not None
    assert saved["date"].tolist() == ["2026-08-01", "2026-08-02", "2026-08-03"]
    assert saved["date"].is_unique
    assert saved.loc[saved["date"] == "2026-08-01", "close"].item() == 101
    assert saved.loc[saved["date"] == "2026-08-02", "close"].item() == 202


def test_failed_parquet_write_preserves_the_previous_file_and_cleans_temp(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = CandleStore(tmp_path)
    store.upsert("SAMPLE-A", candles([("2026-08-01", 100)]))
    destination = store.candle_dir / "SAMPLE-A.parquet"
    original = destination.read_bytes()

    def fail_after_partial_write(_frame, path, **_kwargs):
        Path(path).write_bytes(b"partial")
        raise OSError("simulated disk failure")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fail_after_partial_write)
    with pytest.raises(OSError, match="simulated"):
        store.upsert("SAMPLE-A", candles([("2026-08-02", 101)]))

    assert destination.read_bytes() == original
    assert list(store.candle_dir.glob("*.tmp.parquet")) == []


def test_universe_and_fx_writes_are_date_idempotent_and_sorted(tmp_path) -> None:
    store = CandleStore(tmp_path)
    asof = date(2026, 8, 7)
    store.save_universe(asof, [{"symbol": "SAMPLE-A"}])
    store.save_universe(asof, [{"symbol": "SAMPLE-B"}])

    universe = json.loads((store.universe_dir / "2026-08-07.json").read_text(encoding="utf-8"))
    assert universe["items"] == [{"symbol": "SAMPLE-B"}]
    assert store.append_fx(date(2026, 8, 7), 1_350.0) is True
    assert store.append_fx(date(2026, 8, 5), 1_340.0) is True
    assert store.append_fx(date(2026, 8, 7), 9_999.0) is False

    fx = pd.read_parquet(store.fx_path)
    assert fx["date"].tolist() == ["2026-08-05", "2026-08-07"]
    assert fx["date"].is_unique
    assert store.status() == {
        "symbols": 0,
        "rows": 0,
        "latest_universe": "2026-08-07",
        "fx_rows": 2,
    }


@pytest.mark.parametrize("symbol", ["sample-a", "../SECRET", "SAMPLE_A", "A" * 25])
def test_symbol_is_restricted_to_safe_file_names(tmp_path, symbol: str) -> None:
    store = CandleStore(tmp_path)
    with pytest.raises(ValueError, match="symbol"):
        store.upsert(symbol, candles([("2026-08-01", 100)]))


def test_invalid_candle_schema_and_values_are_rejected(tmp_path) -> None:
    store = CandleStore(tmp_path)
    with pytest.raises(ValueError, match="missing"):
        store.upsert("SAMPLE-A", pd.DataFrame([{"date": "2026-08-01"}]))

    invalid = candles([("2026-08-01", 100)])
    invalid.loc[0, "volume"] = -1
    with pytest.raises(ValueError, match="volume"):
        store.upsert("SAMPLE-A", invalid)

    with pytest.raises(ValueError, match="positive finite"):
        store.append_fx(date(2026, 8, 7), float("nan"))
