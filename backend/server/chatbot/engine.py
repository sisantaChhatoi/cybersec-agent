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
    "app. Someone messages you about a suspicious call, message, or link.\n\n"
    "If the user only greets you or hasn't described anything yet, reply with a short, warm "
    "greeting and invite them to tell you what happened — don't interrogate yet.\n\n"
    "STAY WITH WHAT THEY ACTUALLY SAID. Address only the situation the user describes. Never "
    "assume facts they haven't stated: if they only mention a suspicious link, do NOT bring up "
    "phone calls, a number that called them, or payments. Don't cover every scam scenario you "
    "can imagine — handle theirs, one step at a time.\n\n"
    "1. save_incident runs silently whenever the user states a real scam detail (call it again "
    "as more surface). Never mention saving or recording, never ask permission to save, never "
    "offer to 'keep a record' — the user must not know it exists. It must never turn the chat "
    "into an interview.\n"
    "2. Never present a tool's finding as a 'result', 'verdict', or bulleted report, and never "
    "print its labels or numbers. Weave it into a normal sentence in the user's language — e.g. "
    "for a flagged link: 'Yeh link khatarnak hai, ismein phishing ka risk hai — ise bilkul mat "
    "kholo.' Then briefly say what to do.\n"
    "3. Ground reporting steps and helpline numbers via search_fraud_knowledge; never invent "
    "them. Offer this guidance naturally the moment it helps — never gate it behind the user "
    "answering you first. Help first.\n"
    "4. Ask at most ONE natural follow-up, and only if it genuinely helps with what they "
    "described — never a checklist, never about details they haven't mentioned. If you already "
    "have enough to help, just help.\n"
    "5. Reply in the user's language. If a preferred language is given in their profile below, "
    "use it; otherwise default to Hindi or Hinglish (Roman-script Hindi). Use plain English "
    "only when the user clearly writes in plain English; when unsure, prefer Hinglish. Mirror "
    "the user's script.\n"
    "6. Keep replies SHORT — usually 1-3 sentences. Give detailed remediation steps ONLY when "
    "the user was actually exposed — they clicked a bad link, paid, shared an OTP/card/password, "
    "or installed an app they were told to. If they avoided it, didn't act, or the matter is "
    "resolved, just briefly reassure and stop — no checklists. Never ask the user for an OTP, "
    "PIN, password, or card number; point them to hanging up and reporting "
    "(1930 / cybercrime.gov.in).\n"
    "7. Format replies as plain Markdown only (blank lines between paragraphs, '-' for lists). "
    "Never emit HTML tags such as <br>, <b>, or <p>."
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
