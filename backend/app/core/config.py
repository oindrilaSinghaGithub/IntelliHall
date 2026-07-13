"""
IntelliHall — Application Settings

Reads all configuration from environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/intellihall"

    # Security
    SECRET_KEY: str = "change-me-to-a-secure-random-string"

    # CORS / URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024       # 5 MB per image
    MAX_IMAGES_PER_COMPLAINT: int = 5

    # AI / ML
    MODEL_DIR: str = "app/ai/models"

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
