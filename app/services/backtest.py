from statistics import mean
from uuid import uuid4

from app.schemas import BacktestRequest, BacktestResult, EquityPoint, TradePoint
from app.services.market_data import generate_demo_prices


def _moving_average(values: list[float], window: int, index: int) -> float:
    if index + 1 < window:
        return mean(values[: index + 1])
    return mean(values[index + 1 - window : index + 1])


def _max_drawdown(equity_curve: list[EquityPoint]) -> float:
    peak = equity_curve[0].equity
    max_dd = 0.0
    for point in equity_curve:
        peak = max(peak, point.equity)
        drawdown = (point.equity - peak) / peak
        max_dd = min(max_dd, drawdown)
    return round(max_dd * 100, 2)


def run_moving_average_demo(request: BacktestRequest) -> BacktestResult:
    prices = generate_demo_prices()
    cash = request.start_cash
    units = 0.0
    trades: list[TradePoint] = []
    equity_curve: list[EquityPoint] = []

    for day, price in enumerate(prices):
        short_ma = _moving_average(prices, request.short_window, day)
        long_ma = _moving_average(prices, request.long_window, day)

        if short_ma > long_ma and units == 0:
            units = cash / price
            cash = 0.0
            trades.append(TradePoint(day=day, action="BUY", price=price, cash=round(cash, 2), units=round(units, 6)))
        elif short_ma < long_ma and units > 0:
            cash = units * price
            units = 0.0
            trades.append(TradePoint(day=day, action="SELL", price=price, cash=round(cash, 2), units=round(units, 6)))

        equity = cash + units * price
        equity_curve.append(EquityPoint(day=day, price=price, equity=round(equity, 2)))

    final_equity = equity_curve[-1].equity
    total_return_pct = round((final_equity / request.start_cash - 1) * 100, 2)

    return BacktestResult(
        run_id=str(uuid4()),
        symbol=request.symbol,
        start_cash=request.start_cash,
        final_equity=final_equity,
        total_return_pct=total_return_pct,
        max_drawdown_pct=_max_drawdown(equity_curve),
        trades=trades,
        equity_curve=equity_curve,
    )
