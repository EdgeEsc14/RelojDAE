from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    APP_NAME: str = "RelojDAE API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    API_PREFIX: str = "/api/v1"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "dae_reloj"
    POSTGRES_USER: str = "reloj_app"
    POSTGRES_PASSWORD: str

    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    BACKEND_CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    # Seguridad de autenticación.
    # No tiene valor predeterminado intencionalmente.
    AUTH_SECRET_KEY: str
    AUTH_ACCESS_TOKEN_MINUTES: int = 480

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("AUTH_SECRET_KEY")
    @classmethod
    def validate_auth_secret_key(cls, value: str) -> str:
        secret = value.strip()

        if len(secret) < 32:
            raise ValueError(
                "AUTH_SECRET_KEY debe contener al menos 32 caracteres."
            )

        return secret

    @field_validator("AUTH_ACCESS_TOKEN_MINUTES")
    @classmethod
    def validate_auth_access_token_minutes(cls, value: int) -> int:
        if value < 5:
            raise ValueError(
                "AUTH_ACCESS_TOKEN_MINUTES debe ser de al menos 5 minutos."
            )

        if value > 1440:
            raise ValueError(
                "AUTH_ACCESS_TOKEN_MINUTES no puede superar 1440 minutos."
            )

        return value

    @property
    def database_url(self) -> URL:
        """
        Construye la URL de conexión a PostgreSQL.

        No convertimos el URL a str porque SQLAlchemy puede ocultar
        la contraseña como ***. create_engine acepta un objeto URL.
        """
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()