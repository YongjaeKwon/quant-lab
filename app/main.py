from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, backtests, health, ws
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="공개 가능한 구조만 남긴 퀀트 백엔드 학습 API",
        version="0.1.0",
    )

    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(backtests.router, prefix="/api/backtests", tags=["backtests"])
    app.include_router(ws.router, prefix="/api", tags=["websocket"])
    app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")
    return app


app = create_app()
