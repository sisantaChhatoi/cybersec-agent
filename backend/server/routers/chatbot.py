import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from server.deps import get_chatbot_service, get_current_user
from server.models.chat import Chat, ChatCreate, ChatSummary, SendMessage
from server.models.user import UserInDB
from server.services.chatbot_service import ChatbotService, ChatNotFoundError

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

_ServiceDep = Annotated[ChatbotService, Depends(get_chatbot_service)]
_UserDep = Annotated[UserInDB, Depends(get_current_user)]


@router.post("/chats", response_model=Chat, status_code=status.HTTP_201_CREATED)
async def create_chat(body: ChatCreate, user: _UserDep, service: _ServiceDep) -> Chat:
    return await service.create_chat(user.user_id, body.title)


@router.get("/chats", response_model=list[ChatSummary])
async def list_chats(user: _UserDep, service: _ServiceDep) -> list[ChatSummary]:
    return await service.list_chats(user.user_id)


@router.get("/chats/{chat_id}", response_model=Chat)
async def get_chat(chat_id: str, user: _UserDep, service: _ServiceDep) -> Chat:
    try:
        return await service.get_chat(user.user_id, chat_id)
    except ChatNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chat not found") from exc


@router.post("/chats/{chat_id}/messages")
async def send_message(
    chat_id: str, body: SendMessage, user: _UserDep, service: _ServiceDep
) -> EventSourceResponse:
    try:
        await service.verify_access(user.user_id, chat_id)
    except ChatNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chat not found") from exc

    async def events():
        async for token in service.reply_stream(chat_id, user.user_id, body.message):
            yield {"data": json.dumps(token)}
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(events())
