from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="NEWSRADAR API")
    app_version: str = Field(default="0.1.0")
    api_v1_prefix: str = Field(default="/api/v1")
    debug: bool = Field(default=True)
    environment: str = Field(default="development")

    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)

    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)

    frontend_url: str = Field(default="http://localhost:5173")

    # SMTP / Email
    smtp_host: Optional[str] = Field(default=None)
    smtp_port: int = Field(default=587)
    smtp_username: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    smtp_sender: Optional[str] = Field(default=None)
    smtp_use_tls: bool = Field(default=True)

    # Email verification
    verification_token_expire_hours: int = Field(default=24)

    # Admin seed
    admin_email: str = Field(default="admin@newsradar.com")
    # Mismo valor que el seed del ``main.py`` oficial del aula global,
    # para que la batería de smoke tests del profesor pueda hacer
    # ``/auth/login`` con las credenciales esperadas. Sobrescribir vía
    # variable de entorno ``ADMIN_PASSWORD`` en producción.
    admin_password: str = Field(default="admin123")
    admin_first_name: str = Field(default="Admin")
    admin_last_name: str = Field(default="NewsRadar")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
