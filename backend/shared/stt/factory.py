from shared.config import settings
from shared.stt.base import SpeechToText
from shared.stt.sarvam import SarvamSTT


def create_stt() -> SpeechToText:
    provider = settings.stt_provider.lower()
    if provider == "sarvam":
        return SarvamSTT(
            settings.sarvam_api_key,
            language_code=settings.stt_language_code,
            model=settings.stt_model,
            sample_rate=settings.stt_sample_rate,
        )
    raise ValueError(f"unknown stt provider: {settings.stt_provider!r}")
