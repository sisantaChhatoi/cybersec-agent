from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from server.models.chat import Message

_SYSTEM_PROMPT = (
    "You are a helpful assistant for a scam-call awareness app. "
    "Answer the user's questions clearly and concisely."
)


def to_lc_messages(messages: list[Message]) -> list[BaseMessage]:
    out: list[BaseMessage] = []
    for m in messages:
        out.append(
            HumanMessage(m.message) if m.role == "user" else AIMessage(m.message)
        )
    return out


class ChatbotEngine:
    def __init__(self, model: str, temperature: float = 0.3) -> None:
        self._model = model
        self._temperature = temperature
        self._llm: ChatGroq | None = None

    @property
    def llm(self) -> ChatGroq:
        llm = self._llm
        if llm is None:
            llm = ChatGroq(model=self._model, temperature=self._temperature)
            self._llm = llm
        return llm

    async def stream_reply(
        self, history: list[BaseMessage], user_message: str
    ) -> AsyncIterator[str]:
        # TODO: bind tools here once tool-calling is designed (self.llm.bind_tools([...])).
        messages = [SystemMessage(_SYSTEM_PROMPT), *history, HumanMessage(user_message)]
        async for chunk in self.llm.astream(messages):
            if isinstance(chunk.content, str) and chunk.content:
                yield chunk.content
