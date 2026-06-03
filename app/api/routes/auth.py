from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest) -> TokenResponse:
    if request.username != settings.demo_username or request.password != settings.demo_password:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    token = create_access_token(
        username=request.username,
        secret=settings.auth_secret,
        expires_in=settings.token_expire_seconds,
    )
    return TokenResponse(access_token=token, expires_in=settings.token_expire_seconds)
