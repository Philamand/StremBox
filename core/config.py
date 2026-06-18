from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration using Pydantic Settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    base_dir: str = "./downloads/"
    base_url: str = "http://localhost"
    bearer_token: str = "test_token"
    hanko_url: str = "http://localhost:8000"
    hanko_admin: str = ""
    fastapi_database_url: str = "database/database.db"
    transmission_url: str = "gluetun"
    origin_url: str = "http://localhost:8000"


settings = Settings()
