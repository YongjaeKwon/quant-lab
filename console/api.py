from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from console.schemas import (
    AccountSummaryResponse,
    HealthResponse,
    HistoryPointResponse,
    HoldingResponse,
    HoldingsResponse,
    PipelineResponse,
)
from datastore.snapshot_store import SnapshotStore
from operation.demo_pipeline import read_report, seed_demo
from operation.models import AccountSnapshot


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = REPO_ROOT / "data" / "demo"
WEB_DIST = REPO_ROOT / "console" / "web" / "dist"
logger = logging.getLogger(__name__)


def create_app(
    data_root: Path | None = None,
    *,
    bootstrap: bool = True,
) -> FastAPI:
    root = data_root or DEFAULT_DATA_ROOT
    if bootstrap:
        seed_demo(root)
    store = SnapshotStore(f"sqlite:///{root / 'demo.db'}")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            store.close()

    app = FastAPI(
        title="ReachRich Public Lab API",
        description="합성 데이터만 읽는 공개용 로컬 미러 API",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.data_root = root
    app.state.snapshot_store = store

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        latest = _latest_or_unavailable(store)
        return HealthResponse(
            status="ok",
            sample_data=True,
            latest_snapshot=latest.asof.isoformat() if latest else None,
        )

    @app.get("/api/account/summary", response_model=AccountSummaryResponse)
    def account_summary() -> AccountSummaryResponse:
        latest = _latest_or_unavailable(store)
        if latest is None:
            raise HTTPException(status_code=404, detail="demo snapshot not found")
        return AccountSummaryResponse(
            asof=latest.asof.isoformat(),
            total_krw=latest.total_krw,
            cash_krw=latest.cash_krw,
            invested_krw=latest.invested_krw,
            pnl_rate=latest.pnl_rate,
            daily_pnl_rate=latest.daily_pnl_rate,
        )

    @app.get("/api/account/history", response_model=list[HistoryPointResponse])
    def account_history(
        days: int = Query(default=90, ge=1, le=365),
    ) -> list[HistoryPointResponse]:
        try:
            snapshots = store.history(days)
        except SQLAlchemyError as exc:
            logger.exception("Unable to read synthetic account history")
            raise HTTPException(status_code=503, detail="demo data store unavailable") from exc
        return [
            HistoryPointResponse(
                asof=snapshot.asof.isoformat(),
                total_krw=snapshot.total_krw,
                daily_pnl_rate=snapshot.daily_pnl_rate,
            )
            for snapshot in snapshots
        ]

    @app.get("/api/account/holdings", response_model=HoldingsResponse)
    def account_holdings() -> HoldingsResponse:
        latest = _latest_or_unavailable(store)
        if latest is None:
            return HoldingsResponse(asof=None, items=[])
        return HoldingsResponse(
            asof=latest.asof.isoformat(),
            items=[
                HoldingResponse(
                    symbol=holding.symbol,
                    name=holding.name,
                    market=holding.market,
                    quantity=holding.quantity,
                    last_price=holding.last_price,
                    average_price=holding.average_price,
                    pnl_rate=holding.pnl_rate,
                )
                for holding in latest.holdings
            ],
        )

    @app.get("/api/pipeline/status", response_model=PipelineResponse)
    def pipeline_status() -> PipelineResponse:
        try:
            report = read_report(root / "pipeline-report.json")
        except (OSError, json.JSONDecodeError) as exc:
            logger.exception("Unable to read synthetic pipeline report")
            raise HTTPException(status_code=503, detail="demo pipeline report unavailable") from exc
        if report is None:
            return PipelineResponse(generated_at=None, stages=[])
        try:
            return PipelineResponse.model_validate(report)
        except ValidationError as exc:
            logger.exception("Synthetic pipeline report has an invalid shape")
            raise HTTPException(status_code=503, detail="demo pipeline report unavailable") from exc

    if WEB_DIST.is_dir():
        app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
    else:
        @app.get("/")
        def development_hint() -> dict[str, str]:
            return {
                "message": "ReachRich Public Lab API",
                "dashboard": "build console/web or run its Vite development server",
            }

    return app


def _latest_or_unavailable(store: SnapshotStore) -> AccountSnapshot | None:
    try:
        return store.latest()
    except SQLAlchemyError as exc:
        logger.exception("Unable to read synthetic account snapshot")
        raise HTTPException(status_code=503, detail="demo data store unavailable") from exc
