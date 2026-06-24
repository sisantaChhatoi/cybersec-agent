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
    groq_chat_model: str = "llama-3.3-70b-versatile"
    chat_history_limit: int = 6


settings = Settings()
