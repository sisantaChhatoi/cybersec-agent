from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(_ENV_FILE)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "scamcall"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60 * 24 * 7
    groq_chat_model: str = "llama-3.3-70b-versatile"
    chat_history_limit: int = 6

    groq_api_key: str = ""
    sarvam_api_key: str = ""

    stt_provider: str = "sarvam"
    stt_language_code: str = "unknown"
    stt_model: str = "saaras:v3"
    stt_sample_rate: int = 16000

    detector_model: str = "llama-3.3-70b-versatile"
    detector_threshold: float = 0.6
    detect_interval_seconds: float = 4.0
    transcript_window_seconds: float = 45.0
    min_transcript_chars: int = 40
    consecutive_positives: int = 2


settings = Settings()
