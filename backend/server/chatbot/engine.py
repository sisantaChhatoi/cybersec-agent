import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool

from server.chatbot.llm import make_chat_llm
from server.models.chat import Message

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a calm, non-alarmist fraud-safety assistant for an Indian scam-protection "
    "app. Someone messages you about a suspicious call or message.\n\n"
    "This is a focused fraud-safety chat. If the user only greets you or hasn't described "
    "anything yet, reply with a short, warm greeting and invite them to tell you about the "
    "suspicious call or message — do NOT interrogate for specifics yet. Once they actually "
    "describe a scam, then help and gather details.\n\n"
    "1. CAPTURE FIRST: the moment the user reveals any scam detail, call save_incident before "
    "replying, and again as new details surface. Do it silently — never tell the user you are "
    "saving or recording anything.\n"
    "2. Never state a helpline number or reporting step you haven't grounded via "
    "search_fraud_knowledge.\n"
    "3. Reply in the user's language. If a preferred language is given in their profile below, "
    "use it; otherwise default to Hindi or Hinglish (Roman-script Hindi). Use plain English only "
    "when the user clearly writes in plain English; when unsure, prefer Hinglish. Mirror the "
    "user's script.\n"
    "4. BE CONCISE: a few short sentences at most. No preamble, no filler, no meta-talk about "
    "what you are doing. Once a scam is described, ask naturally for the key missing details "
    "(the number that called, the account/UPI they were told to pay, and their city only if it "
    "isn't already known) in ONE plain question. Settle with what you get within 2-3 "
    "clarifications — never re-ask the same field.\n"
    "5. Never ask the user for an OTP, PIN, password, or card number yourself. Reassure them "
    "that hanging up and reporting (1930 / cybercrime.gov.in) is the right move.\n"
    "6. Format replies as plain Markdown only (use blank lines between paragraphs, '-' for "
    "lists). Never emit HTML tags such as <br>, <b>, or <p>."
)

_MAX_TOOL_ROUNDS = 5


@dataclass(frozen=True)
class UserContext:
    languages: str
    location: str


def _profile_block(ctx: UserContext) -> str:
    return (
        "\n\nUSER PROFILE (from their saved account — already known, never ask for these):\n"
        f"- Preferred language(s), primary first: {ctx.languages}. Reply in the primary "
        "language unless the user writes in another.\n"
        f"- Location: {ctx.location}. Treat this as their city/region (use it for victim_region "
        "when saving an incident); never ask them where they are from."
    )


def to_lc_messages(messages: list[Message]) -> list[BaseMessage]:
    return [
        HumanMessage(m.message) if m.role == "user" else AIMessage(m.message)
        for m in messages
    ]


class ChatbotEngine:
    def __init__(self) -> None:
        self._llm: BaseChatModel | None = None

    @property
    def llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = make_chat_llm()
        return self._llm

    async def stream_reply(
        self,
        history: list[BaseMessage],
        user_message: str,
        tools: list[BaseTool],
        user_context: UserContext | None = None,
    ) -> AsyncIterator[str]:
        llm = self.llm.bind_tools(tools)
        by_name = {t.name: t for t in tools}
        system = _SYSTEM_PROMPT + (_profile_block(user_context) if user_context else "")
        messages: list[BaseMessage] = [
            SystemMessage(system),
            *history,
            HumanMessage(user_message),
        ]

        for round_num in range(_MAX_TOOL_ROUNDS):
            gathered: AIMessageChunk | None = None
            text_buffer: list[str] = []
            async for raw in llm.astream(messages):
                chunk = cast(AIMessageChunk, raw)
                if isinstance(chunk.content, str) and chunk.content:
                    text_buffer.append(chunk.content)
                gathered = chunk if gathered is None else gathered + chunk

            if gathered is None:
                return
            messages.append(gathered)

            if not gathered.tool_calls:
                for text in text_buffer:
                    yield text
                return

            logger.info(
                "round %d: calling tools %s",
                round_num,
                [c["name"] for c in gathered.tool_calls],
            )
            for call in gathered.tool_calls:
                tool = by_name.get(call["name"])
                result = (
                    await tool.ainvoke(call["args"])
                    if tool is not None
                    else f"unknown tool: {call['name']}"
                )
                logger.info("tool %s → %s", call["name"], str(result)[:200])
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=call["id"])
                )
