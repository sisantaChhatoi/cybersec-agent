import logging

from livekit import rtc

logger = logging.getLogger("scamcall.audio_out")

_SAMPLE_RATE = 48000
_FRAME_SAMPLES = _SAMPLE_RATE // 100


async def publish_silence(room: rtc.Room) -> None:
    """Keep the SIP leg alive: carriers drop one-way audio, so publish silence."""
    source = rtc.AudioSource(_SAMPLE_RATE, 1)
    track = rtc.LocalAudioTrack.create_audio_track("agent-keepalive", source)
    await room.local_participant.publish_track(
        track, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
    )
    logger.debug("published keepalive audio track")

    silence = b"\x00\x00" * _FRAME_SAMPLES
    while True:
        await source.capture_frame(
            rtc.AudioFrame(
                data=silence,
                sample_rate=_SAMPLE_RATE,
                num_channels=1,
                samples_per_channel=_FRAME_SAMPLES,
            )
        )
