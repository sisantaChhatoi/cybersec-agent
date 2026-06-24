from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

Role = Literal["user", "agent"]

DEFAULT_TITLE = "New chat"


class Message(BaseModel):
    role: Role
    message: str
    time: datetime


class ChatCreate(BaseModel):
    title: str | None = None


class SendMessage(BaseModel):
    message: str = Field(min_length=1)


class ChatSummary(BaseModel):
    chat_id: str
    title: str


class ChatMeta(BaseModel):
    chat_id: str
    user_id: str
    title: str


class Chat(BaseModel):
    chat_id: str
    user_id: str
    title: str
    messages: list[Message] = []


def new_chat_id() -> str:
    return uuid4().hex
