from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.security import verify_access_token
from app.services.event_bus import event_bus

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token", "")
    try:
        payload = verify_access_token(token, settings.auth_secret)
    except ValueError:
        await websocket.close(code=1008)
        return

    await event_bus.connect(websocket)
    await websocket.send_json({"type": "auth.ok", "payload": {"user": payload["sub"]}})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_bus.disconnect(websocket)
