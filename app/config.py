from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Milli Yapay Zeka"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # AI Keys
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    zhipuai_api_key: Optional[str] = None

    # GitHub
    github_token: Optional[str] = None
    github_username: Optional[str] = None

    # Supabase
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # Streamlit
    streamlit_port: int = 8501
    fastapi_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
