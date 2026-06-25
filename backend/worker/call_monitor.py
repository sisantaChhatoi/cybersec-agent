import asyncio
import contextlib
import logging
import time
from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable

from livekit import rtc

from shared.detector import AlertPolicy, Detection, ScamDetector
from shared.stt.base import SpeechToText

logger = logging.getLogger("scamcall.monitor")

AlertCallback = Callable[[rtc.RemoteParticipant, Detection, str], Awaitable[None]]


class _TranscriptBuffer:
    def __init__(self, window_seconds: float) -> None:
        self._window = window_seconds
        self._entries: deque[tuple[float, str]] = deque()

    def add(self, text: str) -> None:
        now = time.monotonic()
        self._entries.append((now, text))
        cutoff = now - self._window
        while self._entries and self._entries[0][0] < cutoff:
            self._entries.popleft()

    def text(self) -> str:
        return " ".join(text for _, text in self._entries)


class CallMonitor:
    def __init__(
        self,
        stt: SpeechToText,
        detector: ScamDetector,
        *,
        sample_rate: int,
        interval_seconds: float,
        window_seconds: float,
        min_chars: int,
        consecutive_positives: int,
        on_alert: AlertCallback,
    ) -> None:
        self._stt = stt
        self._detector = detector
        self._sample_rate = sample_rate
        self._interval = interval_seconds
        self._min_chars = min_chars
        self._buffer = _TranscriptBuffer(window_seconds)
        self._policy = AlertPolicy(consecutive_positives)
        self._on_alert = on_alert
        self._closed = asyncio.Event()

    async def handle_track(
        self, track: rtc.Track, participant: rtc.RemoteParticipant
    ) -> None:
        logger.info("monitoring audio from %s", participant.identity)
        detect_task = asyncio.create_task(self._detect_loop(participant))
        try:
            await self._transcribe(track)
        finally:
            self._closed.set()
            detect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await detect_task

    async def _transcribe(self, track: rtc.Track) -> None:
        stream = rtc.AudioStream(track, sample_rate=self._sample_rate, num_channels=1)
        logger.debug("opening STT stream")

        async def pcm() -> AsyncIterator[bytes]:
            frames = 0
            async for event in stream:
                frames += 1
                if frames == 1 or frames % 200 == 0:
                    logger.debug("received %d audio frames from caller", frames)
                yield bytes(event.frame.data)

        try:
            async for event in self._stt.stream(pcm()):
                text = event.text.strip()
                if text:
                    self._buffer.add(text)
                    logger.info("transcript: %s", text)
        finally:
            await stream.aclose()

    async def _detect_loop(self, participant: rtc.RemoteParticipant) -> None:
        while not self._closed.is_set():
            await asyncio.sleep(self._interval)
            window = self._buffer.text()
            logger.debug("detect tick window_chars=%d", len(window))
            if len(window) < self._min_chars:
                continue
            detection = await self._detector.detect(window)
            flagged = self._detector.flags(detection)
            logger.info(
                "detect scam=%s confidence=%.2f flags=%s",
                detection.scam,
                detection.confidence,
                detection.red_flags,
            )
            if self._policy.update(flagged):
                await self._on_alert(participant, detection, window)
