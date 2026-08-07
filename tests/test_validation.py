from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from operation.demo_pipeline import demo_candles
from validation import WalkForwardWindow, validate_candles, walk_forward_windows


def valid_frame() -> pd.DataFrame:
    return demo_candles(0, [date(2026, 8, 4), date(2026, 8, 5), date(2026, 8, 6)])


def test_valid_candles_and_walk_forward_boundaries() -> None:
    validate_candles(valid_frame(), date(2026, 8, 7))
    windows = walk_forward_windows(sample_count=12, train_size=4, test_size=3, purge_gap=1)
    assert windows == [
        WalkForwardWindow(0, 4, 5, 8),
        WalkForwardWindow(3, 7, 8, 11),
    ]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda frame: frame.iloc[[1, 0, 2]].reset_index(drop=True), "sorted"),
        (lambda frame: pd.concat([frame, frame.iloc[[0]]], ignore_index=True), "duplicate"),
        (lambda frame: frame.assign(date=["2026-08-04", "2026-08-05", "2026-08-08"]), "future"),
        (lambda frame: frame.assign(volume=[1, -1, 1]), "volume"),
        (lambda frame: frame.assign(close=[1, float("nan"), 1]), "finite"),
        (lambda frame: frame.assign(high=[1, 1, 1]), "high"),
    ],
)
def test_invalid_time_series_is_rejected(mutate, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_candles(mutate(valid_frame()), date(2026, 8, 7))


def test_empty_candles_and_invalid_window_sizes_are_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        validate_candles(valid_frame().iloc[0:0], date(2026, 8, 7))
    with pytest.raises(ValueError, match="window sizes"):
        walk_forward_windows(sample_count=12, train_size=0, test_size=3)
