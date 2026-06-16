from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration using Pydantic Settings."""

    base_dir: str = "./downloads/"
    base_url: str = "http://localhost"
    bearer_token: str = "test_token"
    hanko_url: str = "http://localhost:8000"
    hanko_admin: str = ""
    database_url: str = "database/database.db"
    transmission_url: str = "gluetun"
    origin_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_prefix = ""
        extra = "ignore"


settings = Settings()
