from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class BacktestRequest(BaseModel):
    symbol: str = Field(default="DEMO-BTC", min_length=3, max_length=20)
    start_cash: float = Field(default=10_000, gt=0, le=1_000_000)
    short_window: int = Field(default=5, ge=2, le=30)
    long_window: int = Field(default=20, ge=5, le=90)


class TradePoint(BaseModel):
    day: int
    action: str
    price: float
    cash: float
    units: float


class EquityPoint(BaseModel):
    day: int
    price: float
    equity: float


class BacktestResult(BaseModel):
    run_id: str
    symbol: str
    start_cash: float
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    trades: list[TradePoint]
    equity_curve: list[EquityPoint]


class EventMessage(BaseModel):
    type: str
    payload: dict
