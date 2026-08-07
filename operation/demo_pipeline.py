from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from datastore.candle_store import CandleStore
from datastore.snapshot_store import SnapshotStore
from operation.models import AccountSnapshot, Holding, PipelineReport, PipelineStage
from universe import DEMO_UNIVERSE
from validation import validate_candles


@dataclass(frozen=True)
class SeedResult:
    snapshots: int
    candle_symbols: int
    candle_rows: int
    universe_date: str
    fx_rows: int


def business_dates(asof: date, count: int) -> list[date]:
    dates: list[date] = []
    cursor = asof
    while len(dates) < count:
        if cursor.weekday() < 5:
            dates.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(dates))


def demo_holdings(step: int) -> tuple[Holding, ...]:
    return (
        Holding(
            symbol="SAMPLE-A",
            name="샘플 성장형",
            market="KR",
            quantity=12,
            last_price=125_000 + step * 210,
            average_price=119_000,
        ),
        Holding(
            symbol="SAMPLE-B",
            name="샘플 안정형",
            market="KR",
            quantity=18,
            last_price=81_000 + step * 80,
            average_price=79_500,
        ),
        Holding(
            symbol="SAMPLE-C",
            name="샘플 배당형",
            market="KR",
            quantity=9,
            last_price=63_000 - step * 25,
            average_price=64_500,
        ),
    )


def demo_snapshot(asof: date, step: int, total_steps: int) -> AccountSnapshot:
    wave = math.sin(step / 4) * 120_000
    trend = step * 38_000
    total = 25_000_000 + trend + wave
    previous_wave = math.sin(max(step - 1, 0) / 4) * 120_000
    previous = 25_000_000 + max(step - 1, 0) * 38_000 + previous_wave
    cash = 4_300_000 + (total_steps - step) * 7_500
    return AccountSnapshot(
        asof=asof,
        total_krw=round(total, 2),
        cash_krw=round(cash, 2),
        invested_krw=round(total - cash, 2),
        pnl_rate=round(total / 25_000_000 - 1.0, 6),
        daily_pnl_rate=round(total / previous - 1.0, 6) if step else 0.0,
        holdings=demo_holdings(step),
    )


def demo_candles(symbol_index: int, dates: list[date]) -> pd.DataFrame:
    rows = []
    base = 10_000 + symbol_index * 1_700
    for step, candle_date in enumerate(dates):
        close = base + step * (22 + symbol_index * 3) + math.sin(step / 3) * 90
        open_price = close - math.cos(step / 4) * 35
        rows.append(
            {
                "date": candle_date.isoformat(),
                "open": round(open_price, 2),
                "high": round(max(open_price, close) + 55, 2),
                "low": round(min(open_price, close) - 55, 2),
                "close": round(close, 2),
                "volume": float(100_000 + symbol_index * 8_000 + step * 750),
            }
        )
    return pd.DataFrame(rows)


def seed_demo(data_root: Path, asof: date | None = None) -> SeedResult:
    """Builds deterministic, fictional data without any outbound request."""

    asof = asof or date.today()
    data_root.mkdir(parents=True, exist_ok=True)
    snapshot_store = SnapshotStore(f"sqlite:///{data_root / 'demo.db'}")
    try:
        snapshot_dates = business_dates(asof, 45)
        for step, snapshot_date in enumerate(snapshot_dates):
            snapshot_store.save(demo_snapshot(snapshot_date, step, len(snapshot_dates)))

        candle_store = CandleStore(data_root / "market")
        candle_dates = business_dates(asof, 30)
        for index, item in enumerate(DEMO_UNIVERSE):
            frame = demo_candles(index, candle_dates)
            validate_candles(frame, asof)
            candle_store.upsert(str(item["symbol"]), frame)
        candle_store.save_universe(asof, DEMO_UNIVERSE)
        candle_store.append_fx(asof, 1_350.0)

        snapshot_count = snapshot_store.count()
        market_status = candle_store.status()
        report = PipelineReport(
            generated_at=datetime.now(timezone.utc),
            sample_data=True,
            stages=(
                PipelineStage("fixture", "합성 데이터 생성", "DONE", "외부 네트워크 요청 없음"),
                PipelineStage(
                    "snapshot",
                    "계좌 스냅샷 저장",
                    "DONE",
                    f"날짜별 {snapshot_count}건",
                ),
                PipelineStage(
                    "market",
                    "시장 데이터 upsert",
                    "DONE",
                    f"가상 종목 {market_status['symbols']}개 · {market_status['rows']}행",
                ),
                PipelineStage("validation", "시계열 검증", "DONE", "정렬·중복·미래 데이터 확인"),
            ),
        )
        _write_report(data_root / "pipeline-report.json", report)
        return SeedResult(
            snapshots=snapshot_count,
            candle_symbols=int(market_status["symbols"]),
            candle_rows=int(market_status["rows"]),
            universe_date=str(market_status["latest_universe"]),
            fx_rows=int(market_status["fx_rows"]),
        )
    finally:
        snapshot_store.close()


def _write_report(path: Path, report: PipelineReport) -> None:
    body = asdict(report)
    body["generated_at"] = report.generated_at.isoformat()
    temporary = path.with_suffix(".tmp.json")
    temporary.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def read_report(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
