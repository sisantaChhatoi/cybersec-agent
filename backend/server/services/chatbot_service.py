from collections.abc import AsyncIterator
from datetime import datetime, timezone

from server.chatbot.engine import ChatbotEngine, to_lc_messages
from server.chatbot.tools import build_chat_tools
from server.models.chat import (
    DEFAULT_TITLE,
    Chat,
    ChatSummary,
    Message,
    new_chat_id,
)
from server.repositories.chat_repo import ChatRepository
from server.repositories.incident_repo import IncidentRepository


class ChatNotFoundError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _title_from(text: str) -> str:
    return text[:40]


class ChatbotService:
    def __init__(
        self,
        chats: ChatRepository,
        incidents: IncidentRepository,
        engine: ChatbotEngine,
        history_limit: int,
    ) -> None:
        self._chats = chats
        self._incidents = incidents
        self._engine = engine
        self._history_limit = history_limit

    async def create_chat(self, user_id: str, title: str | None) -> Chat:
        chat = Chat(
            chat_id=new_chat_id(), user_id=user_id, title=title or DEFAULT_TITLE
        )
        await self._chats.create(chat)
        return chat

    async def list_chats(self, user_id: str) -> list[ChatSummary]:
        return await self._chats.list_for_user(user_id)

    async def get_chat(self, user_id: str, chat_id: str) -> Chat:
        chat = await self._chats.get(chat_id)
        if chat is None or chat.user_id != user_id:
            raise ChatNotFoundError
        return chat

    async def verify_access(self, user_id: str, chat_id: str) -> None:
        meta = await self._chats.get_meta(chat_id)
        if meta is None or meta.user_id != user_id:
            raise ChatNotFoundError

    async def reply_stream(
        self, chat_id: str, user_id: str, text: str
    ) -> AsyncIterator[str]:
        history_msgs = await self._chats.recent_messages(chat_id, self._history_limit)
        if not history_msgs:
            meta = await self._chats.get_meta(chat_id)
            if meta is not None and meta.title == DEFAULT_TITLE:
                await self._chats.set_title(chat_id, _title_from(text))

        await self._chats.append_message(
            chat_id, Message(role="user", message=text, time=_now())
        )

        history = to_lc_messages(history_msgs)
        tools = build_chat_tools(self._incidents, session_id=chat_id, user_id=user_id)
        parts: list[str] = []
        async for token in self._engine.stream_reply(history, text, tools):
            parts.append(token)
            yield token

        await self._chats.append_message(
            chat_id, Message(role="agent", message="".join(parts), time=_now())
        )
