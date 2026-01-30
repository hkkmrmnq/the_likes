from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket

from src import db
from src import dependencies as dp
from src.config import CFG
from src.services.chat import chat_manager

router = APIRouter()


@router.websocket(CFG.PATHS.PRIVATE.CHAT)
async def websocket_endpoint(
    *,
    websocket: WebSocket,
    user: Annotated[
        db.User, Depends(dp.get_current_active_and_virified_websocket_user)
    ],
):
    await chat_manager.manage_chat(
        websocket=websocket,
        current_user=user,
    )
