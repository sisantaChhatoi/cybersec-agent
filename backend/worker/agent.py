import asyncio
import logging

from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli

import shared.config  # noqa: F401
from shared.config import settings
from shared.detector import Detection, ScamDetector
from shared.stt.factory import create_stt
from worker.audio_out import publish_silence
from worker.call_monitor import CallMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scamcall.worker")


async def _raise_alert(
    participant: rtc.RemoteParticipant, detection: Detection, window: str
) -> None:
    logger.warning(
        "SCAM ALERT caller=%s confidence=%.2f reason=%s red_flags=%s",
        participant.identity,
        detection.confidence,
        detection.reason,
        detection.red_flags,
    )
    # TODO: POST to FastAPI alert intake -> Expo push -> user's phone.


def _log_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    if (exc := task.exception()) is not None:
        logger.error("monitor task failed", exc_info=exc)


def _spawn(coro) -> None:
    task = asyncio.create_task(coro)
    task.add_done_callback(_log_task_error)


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    logger.info("connected to room %r", ctx.room.name)

    _spawn(publish_silence(ctx.room))

    detector = ScamDetector(
        settings.groq_api_key or None,
        model=settings.detector_model,
        threshold=settings.detector_threshold,
    )

    def new_monitor() -> CallMonitor:
        return CallMonitor(
            create_stt(),
            detector,
            sample_rate=settings.stt_sample_rate,
            interval_seconds=settings.detect_interval_seconds,
            window_seconds=settings.transcript_window_seconds,
            min_chars=settings.min_transcript_chars,
            consecutive_positives=settings.consecutive_positives,
            on_alert=_raise_alert,
        )

    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            _spawn(new_monitor().handle_track(track, participant))

    ctx.room.on("track_subscribed", on_track_subscribed)

    for participant in ctx.room.remote_participants.values():
        for publication in participant.track_publications.values():
            track = publication.track
            if track is not None and track.kind == rtc.TrackKind.KIND_AUDIO:
                _spawn(new_monitor().handle_track(track, participant))

    disconnected = asyncio.Event()
    ctx.room.on("disconnected", lambda *_: disconnected.set())
    await disconnected.wait()
    logger.info("call ended, room %r", ctx.room.name)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
