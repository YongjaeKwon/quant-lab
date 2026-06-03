from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import verify_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")

    try:
        payload = verify_access_token(credentials.credentials, settings.auth_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return str(payload["sub"])
