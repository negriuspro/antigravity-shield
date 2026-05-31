from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://aguser:password@postgres:5432/antigravity"

    # Redis
    redis_url: str = "redis://:password@redis:6379/0"

    # JWT
    secret_key: str = "super-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # CORS
    cors_origins: str = "http://localhost:3000"

    # AdGuard
    adguard_host: str = "adguardhome"
    adguard_port: int = 3000
    adguard_user: str = "admin"
    adguard_password: str = "password"

    # Alerts
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    alert_email_to: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""

    @property
    def adguard_base_url(self) -> str:
        return f"http://{self.adguard_host}:{self.adguard_port}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
