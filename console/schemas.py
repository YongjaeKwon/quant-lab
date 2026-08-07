from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    sample_data: bool
    latest_snapshot: str | None


class AccountSummaryResponse(BaseModel):
    asof: str
    total_krw: float
    cash_krw: float
    invested_krw: float
    pnl_rate: float
    daily_pnl_rate: float
    sample_data: bool = True


class HistoryPointResponse(BaseModel):
    asof: str
    total_krw: float
    daily_pnl_rate: float


class HoldingResponse(BaseModel):
    symbol: str
    name: str
    market: str
    quantity: float
    last_price: float
    average_price: float
    pnl_rate: float


class HoldingsResponse(BaseModel):
    asof: str | None
    items: list[HoldingResponse]
    sample_data: bool = True


class PipelineStageResponse(BaseModel):
    id: str
    label: str
    status: str
    detail: str


class PipelineResponse(BaseModel):
    generated_at: str | None
    sample_data: bool = True
    stages: list[PipelineStageResponse] = Field(default_factory=list)
