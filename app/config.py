from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    ENV: str = "development"
    VERSION: str = "1.0.0"
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Escalation webhook (optional)
    ESCALATION_WEBHOOK_URL: str = ""


settings = Settings()
