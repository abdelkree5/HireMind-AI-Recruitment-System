from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.websocket_manager import manager
from backend.app.services.auth_service import get_current_user

router = APIRouter()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token") or websocket.headers.get("authorization", "")
    if token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1].strip()
    try:
        get_current_user(token)
    except Exception:
        await websocket.close(code=1008)
        return
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
