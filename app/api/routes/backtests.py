from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas import BacktestRequest, BacktestResult
from app.services.backtest import run_moving_average_demo
from app.services.event_bus import event_bus

router = APIRouter()


@router.post("/run", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest, username: str = Depends(get_current_user)) -> BacktestResult:
    result = run_moving_average_demo(request)
    await event_bus.broadcast(
        {
            "type": "backtest.completed",
            "payload": {
                "user": username,
                "run_id": result.run_id,
                "symbol": result.symbol,
                "total_return_pct": result.total_return_pct,
                "max_drawdown_pct": result.max_drawdown_pct,
            },
        }
    )
    return result
