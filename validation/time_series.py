from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import pandas as pd

from datastore.candle_store import REQUIRED_COLUMNS


@dataclass(frozen=True)
class WalkForwardWindow:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def validate_candles(frame: pd.DataFrame, asof: date) -> None:
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"missing candle columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("candle data must not be empty")
    try:
        dates = pd.to_datetime(frame["date"], errors="raise")
        numeric = frame[REQUIRED_COLUMNS[1:]].apply(pd.to_numeric, errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError("candle values must contain valid dates and numbers") from exc
    if dates.isna().any():
        raise ValueError("candle dates must not be empty")
    if not all(math.isfinite(float(value)) for value in numeric.to_numpy().ravel()):
        raise ValueError("candle values must be finite")
    if dates.duplicated().any():
        raise ValueError("duplicate candle dates")
    if not dates.is_monotonic_increasing:
        raise ValueError("candle dates must be sorted")
    if (dates.dt.date > asof).any():
        raise ValueError("future candles are not allowed")
    if (numeric[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("prices must be positive")
    if (numeric["volume"] < 0).any():
        raise ValueError("volume must be non-negative")
    if (numeric["high"] < numeric[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("high price is inconsistent")
    if (numeric["low"] > numeric[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("low price is inconsistent")


def walk_forward_windows(
    sample_count: int,
    train_size: int,
    test_size: int,
    purge_gap: int = 1,
) -> list[WalkForwardWindow]:
    if min(sample_count, train_size, test_size) <= 0 or purge_gap < 0:
        raise ValueError("window sizes must be positive and purge_gap must be non-negative")
    windows: list[WalkForwardWindow] = []
    test_start = train_size + purge_gap
    while test_start + test_size <= sample_count:
        windows.append(
            WalkForwardWindow(
                train_start=test_start - purge_gap - train_size,
                train_end=test_start - purge_gap,
                test_start=test_start,
                test_end=test_start + test_size,
            )
        )
        test_start += test_size
    return windows
