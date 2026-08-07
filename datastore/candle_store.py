from __future__ import annotations

import json
import math
import os
import re
import tempfile
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
SAFE_SYMBOL = re.compile(r"^[A-Z0-9-]{1,24}$")


def _atomic_write(path: Path, writer: Callable[[Path], None], suffix: str) -> None:
    """Write beside the destination and atomically swap the completed file in.

    Keeping the temporary file in the same directory guarantees that ``os.replace``
    stays on one filesystem. A unique name also prevents concurrent demo runs from
    clobbering each other's temporary output.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.",
        suffix=suffix,
        dir=path.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        writer(temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _normalise_candles(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"missing candle columns: {sorted(missing)}")

    normalised = frame[REQUIRED_COLUMNS].copy()
    try:
        dates = pd.to_datetime(normalised["date"], errors="raise")
        if dates.isna().any():
            raise ValueError("candle dates must not be empty")
        normalised["date"] = dates.dt.strftime("%Y-%m-%d")
        for column in REQUIRED_COLUMNS[1:]:
            normalised[column] = pd.to_numeric(normalised[column], errors="raise").astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("candle values must contain valid dates and numbers") from exc

    numeric_values = normalised[REQUIRED_COLUMNS[1:]].to_numpy().ravel()
    if not all(math.isfinite(float(value)) for value in numeric_values):
        raise ValueError("candle values must be finite")
    if (normalised[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("candle prices must be positive")
    if (normalised["volume"] < 0).any():
        raise ValueError("candle volume must be non-negative")
    if (normalised["high"] < normalised[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("high price is inconsistent")
    if (normalised["low"] > normalised[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("low price is inconsistent")
    return normalised


class CandleStore:
    """Local Parquet mirror for synthetic market data used by the public demo."""

    def __init__(self, root: Path):
        self.root = root
        self.candle_dir = root / "candles"
        self.universe_dir = root / "universe"
        self.fx_path = root / "fx_usdkrw.parquet"
        self.candle_dir.mkdir(parents=True, exist_ok=True)
        self.universe_dir.mkdir(parents=True, exist_ok=True)

    def upsert(self, symbol: str, frame: pd.DataFrame) -> int:
        if not SAFE_SYMBOL.fullmatch(symbol):
            raise ValueError("symbol may contain only A-Z, 0-9 and hyphens")
        if frame.empty:
            return 0
        incoming = _normalise_candles(frame)
        incoming = incoming.drop_duplicates(subset="date", keep="last")

        path = self.candle_dir / f"{symbol}.parquet"
        existing = (
            _normalise_candles(pd.read_parquet(path))
            if path.exists()
            else pd.DataFrame(columns=REQUIRED_COLUMNS)
        )
        existing_dates = set(existing["date"])
        new_rows = int((~incoming["date"].isin(existing_dates)).sum())

        merged = (
            incoming.copy()
            if existing.empty
            else pd.concat([existing, incoming], ignore_index=True)
        )
        merged = merged.drop_duplicates(subset="date", keep="last")
        merged = merged.sort_values("date").reset_index(drop=True)
        _atomic_write(
            path,
            lambda temporary: merged.to_parquet(temporary, index=False),
            ".tmp.parquet",
        )
        return new_rows

    def read(self, symbol: str) -> pd.DataFrame | None:
        if not SAFE_SYMBOL.fullmatch(symbol):
            raise ValueError("symbol may contain only A-Z, 0-9 and hyphens")
        path = self.candle_dir / f"{symbol}.parquet"
        return pd.read_parquet(path) if path.exists() else None

    def save_universe(self, asof: date, items: list[dict[str, object]]) -> None:
        path = self.universe_dir / f"{asof.isoformat()}.json"
        payload = json.dumps(
            {"asof": asof.isoformat(), "items": items},
            ensure_ascii=False,
            indent=2,
        )
        _atomic_write(
            path,
            lambda temporary: temporary.write_text(payload, encoding="utf-8"),
            ".tmp.json",
        )

    def append_fx(self, asof: date, rate: float) -> bool:
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("FX rate must be a positive finite number")
        iso = asof.isoformat()
        columns = ["date", "rate"]
        existing = (
            pd.read_parquet(self.fx_path)
            if self.fx_path.exists()
            else pd.DataFrame(columns=columns)
        )
        if not existing.empty:
            existing = existing[columns].copy()
            existing["date"] = pd.to_datetime(existing["date"], errors="raise").dt.strftime(
                "%Y-%m-%d"
            )
            existing["rate"] = pd.to_numeric(existing["rate"], errors="raise").astype(float)
            existing = existing.drop_duplicates(subset="date", keep="last")
        if iso in set(existing["date"]):
            return False
        incoming = pd.DataFrame([{"date": iso, "rate": float(rate)}])
        merged = (
            incoming
            if existing.empty
            else pd.concat([existing, incoming], ignore_index=True)
        )
        merged = merged.sort_values("date").reset_index(drop=True)
        _atomic_write(
            self.fx_path,
            lambda temporary: merged.to_parquet(temporary, index=False),
            ".tmp.parquet",
        )
        return True

    def status(self) -> dict[str, object]:
        symbols = sorted(path.stem for path in self.candle_dir.glob("*.parquet"))
        rows = sum(len(pd.read_parquet(self.candle_dir / f"{symbol}.parquet")) for symbol in symbols)
        universe_files = sorted(self.universe_dir.glob("*.json"))
        return {
            "symbols": len(symbols),
            "rows": rows,
            "latest_universe": universe_files[-1].stem if universe_files else None,
            "fx_rows": len(pd.read_parquet(self.fx_path)) if self.fx_path.exists() else 0,
        }
