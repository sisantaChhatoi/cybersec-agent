from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pydantic import BaseModel


class TranscriptEvent(BaseModel):
    text: str
    is_final: bool = True
    language: str | None = None
    speaker: str | None = None


class SpeechToText(ABC):
    """Strategy interface: consume 16 kHz mono s16le PCM, yield transcript events."""

    @abstractmethod
    def stream(self, audio: AsyncIterator[bytes]) -> AsyncIterator[TranscriptEvent]: ...
