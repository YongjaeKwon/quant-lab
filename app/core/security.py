import base64
import hashlib
import hmac
import json
import time
from typing import Any


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return _b64encode(digest)


def create_access_token(username: str, secret: str, expires_in: int) -> str:
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in,
    }
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(encoded_payload, secret)
    return f"{encoded_payload}.{signature}"


def verify_access_token(token: str, secret: str) -> dict[str, Any]:
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("토큰 형식이 올바르지 않습니다.") from exc

    expected = _sign(encoded_payload, secret)
    if not hmac.compare_digest(signature, expected):
        raise ValueError("토큰 서명이 올바르지 않습니다.")

    payload = json.loads(_b64decode(encoded_payload))
    if int(payload["exp"]) < int(time.time()):
        raise ValueError("토큰이 만료되었습니다.")
    return payload
