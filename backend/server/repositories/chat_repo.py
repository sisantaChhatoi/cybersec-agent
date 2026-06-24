from pymongo.asynchronous.database import AsyncDatabase

from server.models.chat import Chat, ChatMeta, ChatSummary, Message


class ChatRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self._col = db["chats"]

    async def ensure_indexes(self) -> None:
        await self._col.create_index("chat_id", unique=True)
        await self._col.create_index("user_id")

    async def create(self, chat: Chat) -> None:
        await self._col.insert_one(chat.model_dump())

    async def get(self, chat_id: str) -> Chat | None:
        doc = await self._col.find_one({"chat_id": chat_id})
        return Chat(**doc) if doc else None

    async def get_meta(self, chat_id: str) -> ChatMeta | None:
        doc = await self._col.find_one({"chat_id": chat_id}, {"messages": 0})
        return ChatMeta(**doc) if doc else None

    async def recent_messages(self, chat_id: str, limit: int) -> list[Message]:
        doc = await self._col.find_one(
            {"chat_id": chat_id}, {"messages": {"$slice": -limit}}
        )
        return [Message(**m) for m in doc["messages"]] if doc else []

    async def append_message(self, chat_id: str, message: Message) -> None:
        await self._col.update_one(
            {"chat_id": chat_id}, {"$push": {"messages": message.model_dump()}}
        )

    async def set_title(self, chat_id: str, title: str) -> None:
        await self._col.update_one({"chat_id": chat_id}, {"$set": {"title": title}})

    async def list_for_user(self, user_id: str) -> list[ChatSummary]:
        cursor = self._col.find({"user_id": user_id}, {"chat_id": 1, "title": 1})
        return [ChatSummary(**doc) async for doc in cursor]
