from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {
        "ok": True,
        "app": settings.app_name,
        "env": settings.app_env,
        "message": "quant-lab API가 실행 중입니다.",
    }
