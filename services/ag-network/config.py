from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://aguser:password@postgres:5432/antigravity"
    redis_url: str = "redis://:password@redis:6379/0"
    adguard_host: str = "adguardhome"
    adguard_port: int = 3000
    adguard_user: str = "admin"
    adguard_password: str = "password"
    poll_interval: int = 10  # seconds

    @property
    def adguard_base_url(self) -> str:
        return f"http://{self.adguard_host}:{self.adguard_port}"
