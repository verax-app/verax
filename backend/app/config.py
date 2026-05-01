import os
from pydantic_settings import BaseSettings

_env = os.getenv("APP_ENV", "local")


class Settings(BaseSettings):
    database_url: str = "sqlite:///./verax.db"
    ollama_model: str = "llama3.2"
    ollama_host: str = "http://localhost:11434"
    ai_provider: str = "ollama"
    groq_api_key: str = ""
    gemini_api_key: str = ""
    fetch_interval_minutes: int = 30
    summarize_interval_minutes: int = 2
    articles_per_feed: int = 10
    batch_summarize: int = 10

    model_config = {"env_file": f".env.{_env}", "extra": "ignore"}


settings = Settings()
