from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://aguser:password@postgres:5432/antigravity"
    redis_url: str = "redis://:password@redis:6379/0"
    network_interface: str = "eth0"
    network_subnet: str = "192.168.1.0/24"
    scan_interval_seconds: int = 30
