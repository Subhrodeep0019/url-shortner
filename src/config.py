from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # src/ -> parent.parent = root/

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )

settings = Settings()