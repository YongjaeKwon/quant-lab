from dataclasses import dataclass
from datetime import date
from typing import Protocol

import pandas as pd


@dataclass(frozen=True)
class StrategySignal:
    asof: date
    symbol: str
    weight: float


class Strategy(Protocol):
    """Public interface boundary; concrete private strategy logic is not included."""

    def generate(self, candles: dict[str, pd.DataFrame], asof: date) -> list[StrategySignal]: ...
