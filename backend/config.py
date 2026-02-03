from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    mongo_url: str = Field(
        ...,
        validation_alias=AliasChoices("MONGO_URL", "mongo_url"),
    )
    db_name: str = Field(
        ...,
        validation_alias=AliasChoices("MONGO_DB", "DB_NAME", "db_name"),
    )
    allowed_origins: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "CORS_ORIGINS", "allowed_origins"),
    )
    allow_credentials: bool = Field(
        False,
        validation_alias=AliasChoices("ALLOW_CREDENTIALS", "allow_credentials"),
    )
    log_level: str = Field(
        "INFO",
        validation_alias=AliasChoices("LOG_LEVEL", "log_level"),
    )
    max_page_size: int = Field(
        500,
        validation_alias=AliasChoices("MAX_PAGE_SIZE", "max_page_size"),
    )
    default_page_size: int = Field(
        100,
        validation_alias=AliasChoices("DEFAULT_PAGE_SIZE", "default_page_size"),
    )
    mongo_server_selection_timeout_ms: int = Field(
        5000,
        validation_alias=AliasChoices(
            "MONGO_SERVER_SELECTION_TIMEOUT_MS",
            "mongo_server_selection_timeout_ms",
        ),
    )
    auth_enabled: bool = Field(
        True,
        validation_alias=AliasChoices("AUTH_ENABLED", "auth_enabled"),
    )
    jwt_secret: str = Field(
        "change-me",
        validation_alias=AliasChoices("JWT_SECRET", "jwt_secret"),
    )
    jwt_secret_file: str = Field(
        "",
        validation_alias=AliasChoices("JWT_SECRET_FILE", "jwt_secret_file"),
    )
    jwt_algorithm: str = Field(
        "HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "jwt_algorithm"),
    )
    jwt_audience: str = Field(
        "",
        validation_alias=AliasChoices("JWT_AUDIENCE", "jwt_audience"),
    )
    jwt_issuer: str = Field(
        "",
        validation_alias=AliasChoices("JWT_ISSUER", "jwt_issuer"),
    )
    jwt_required_roles: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("JWT_REQUIRED_ROLES", "jwt_required_roles"),
    )
    rate_limit_default: str = Field(
        "100/minute",
        validation_alias=AliasChoices("RATE_LIMIT_DEFAULT", "rate_limit_default"),
    )
    rate_limit_auth: str = Field(
        "20/minute",
        validation_alias=AliasChoices("RATE_LIMIT_AUTH", "rate_limit_auth"),
    )
    metrics_enabled: bool = Field(
        True,
        validation_alias=AliasChoices("METRICS_ENABLED", "metrics_enabled"),
    )
    otel_enabled: bool = Field(
        False,
        validation_alias=AliasChoices("OTEL_ENABLED", "otel_enabled"),
    )
    otel_service_name: str = Field(
        "satellite-orbit-api",
        validation_alias=AliasChoices("OTEL_SERVICE_NAME", "otel_service_name"),
    )
    otel_exporter_otlp_endpoint: str = Field(
        "",
        validation_alias=AliasChoices(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "otel_exporter_otlp_endpoint",
        ),
    )

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        case_sensitive=True,
        extra="ignore",
    )

    @classmethod
    def parse_env_var(cls, field_name: str, raw_value: str):
        if field_name in {"allowed_origins", "jwt_required_roles"}:
            return [origin.strip() for origin in raw_value.split(",") if origin.strip()]
        return super().parse_env_var(field_name, raw_value)

    @model_validator(mode="after")
    def validate_auth_secrets(self):
        if self.jwt_secret_file:
            secret_path = Path(self.jwt_secret_file)
            if secret_path.is_file():
                self.jwt_secret = secret_path.read_text(encoding="utf-8").strip()
            else:
                raise ValueError("JWT_SECRET_FILE must point to a readable file.")
        if self.auth_enabled and self.jwt_secret == "change-me":
            raise ValueError("JWT_SECRET must be set to a secure value in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
