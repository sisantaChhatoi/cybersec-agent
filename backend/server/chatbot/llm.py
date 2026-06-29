from langchain_core.language_models import BaseChatModel

from shared.config import settings


def make_chat_llm() -> BaseChatModel:
    """Chat model for the agent, selected by `chat_provider`. Both providers
    are OpenAI-tool-calling capable, so `bind_tools` works on either."""
    provider = settings.chat_provider
    if provider == "sarvam":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.sarvam_chat_model,
            base_url=settings.sarvam_base_url,
            api_key=settings.sarvam_api_key,
            temperature=settings.chat_temperature,
        )
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.groq_chat_model,
            temperature=settings.chat_temperature,
        )
    raise ValueError(f"unknown chat provider: {provider!r}")
