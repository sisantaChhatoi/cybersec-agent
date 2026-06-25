import asyncio
import base64
import contextlib
import logging
from collections.abc import AsyncIterator

from sarvamai import AsyncSarvamAI

from shared.stt.base import SpeechToText, TranscriptEvent

logger = logging.getLogger("scamcall.stt.sarvam")


class SarvamSTT(SpeechToText):
    def __init__(
        self,
        api_key: str,
        *,
        language_code: str = "unknown",
        model: str = "saaras:v3",
        sample_rate: int = 16000,
        input_audio_codec: str = "pcm_s16le",
    ) -> None:
        self._api_key = api_key
        self._language_code = language_code
        self._model = model
        self._sample_rate = sample_rate
        self._codec = input_audio_codec

    async def stream(
        self, audio: AsyncIterator[bytes]
    ) -> AsyncIterator[TranscriptEvent]:
        client = AsyncSarvamAI(api_subscription_key=self._api_key)
        async with client.speech_to_text_streaming.connect(
            language_code=self._language_code,
            model=self._model,
            input_audio_codec=self._codec,
            sample_rate=str(self._sample_rate),
        ) as ws:
            logger.debug(
                "sarvam connected model=%s codec=%s sr=%s",
                self._model,
                self._codec,
                self._sample_rate,
            )
            sender = asyncio.create_task(self._feed(ws, audio))
            try:
                async for response in ws:
                    rtype = getattr(response, "type", None)
                    if rtype != "data":
                        logger.info(
                            "sarvam response type=%s data=%r",
                            rtype,
                            getattr(response, "data", None),
                        )
                    event = self._to_event(response)
                    if event is not None:
                        yield event
            finally:
                if not sender.done():
                    sender.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await sender

    async def _feed(self, ws, audio: AsyncIterator[bytes]) -> None:
        sent = 0
        try:
            async for chunk in audio:
                # encoding literal only accepts "audio/wav"; real codec set at connect
                await ws.transcribe(
                    audio=base64.b64encode(chunk).decode(),
                    sample_rate=self._sample_rate,
                )
                sent += 1
                if sent == 1 or sent % 100 == 0:
                    logger.debug("sarvam sent %d audio chunks", sent)
            await ws.flush()
            logger.debug("sarvam audio stream ended after %d chunks, flushed", sent)
        except Exception:
            logger.exception("sarvam feed failed after %d chunks", sent)
            raise

    @staticmethod
    def _to_event(response) -> TranscriptEvent | None:
        if getattr(response, "type", None) != "data":
            return None
        data = getattr(response, "data", None)
        transcript = getattr(data, "transcript", None) if data is not None else None
        if not transcript:
            return None
        return TranscriptEvent(
            text=transcript, language=getattr(data, "language_code", None)
        )
