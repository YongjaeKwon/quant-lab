from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Holding:
    symbol: str
    name: str
    market: str
    quantity: float
    last_price: float
    average_price: float

    @property
    def pnl_rate(self) -> float:
        if self.average_price <= 0:
            return 0.0
        return self.last_price / self.average_price - 1.0


@dataclass(frozen=True)
class AccountSnapshot:
    asof: date
    total_krw: float
    cash_krw: float
    invested_krw: float
    pnl_rate: float
    daily_pnl_rate: float
    holdings: tuple[Holding, ...]


@dataclass(frozen=True)
class PipelineStage:
    id: str
    label: str
    status: str
    detail: str


@dataclass(frozen=True)
class PipelineReport:
    generated_at: datetime
    sample_data: bool
    stages: tuple[PipelineStage, ...]
