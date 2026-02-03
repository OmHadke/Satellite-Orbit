from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    mongo_url: str = Field(..., env="MONGO_URL")
    db_name: str = Field(..., env="DB_NAME")
    allowed_origins: List[str] = Field(default_factory=list, env="ALLOWED_ORIGINS")
    allow_credentials: bool = Field(False, env="ALLOW_CREDENTIALS")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_page_size: int = Field(500, env="MAX_PAGE_SIZE")
    default_page_size: int = Field(100, env="DEFAULT_PAGE_SIZE")
    mongo_server_selection_timeout_ms: int = Field(
        5000, env="MONGO_SERVER_SELECTION_TIMEOUT_MS"
    )
    auth_enabled: bool = Field(True, env="AUTH_ENABLED")
    jwt_secret: str = Field("change-me", env="JWT_SECRET")
    jwt_secret_file: str = Field("", env="JWT_SECRET_FILE")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_audience: str = Field("", env="JWT_AUDIENCE")
    jwt_issuer: str = Field("", env="JWT_ISSUER")
    jwt_required_roles: List[str] = Field(default_factory=list, env="JWT_REQUIRED_ROLES")
    rate_limit_default: str = Field("100/minute", env="RATE_LIMIT_DEFAULT")
    rate_limit_auth: str = Field("20/minute", env="RATE_LIMIT_AUTH")
    metrics_enabled: bool = Field(True, env="METRICS_ENABLED")
    otel_enabled: bool = Field(False, env="OTEL_ENABLED")
    otel_service_name: str = Field("satellite-orbit-api", env="OTEL_SERVICE_NAME")
    otel_exporter_otlp_endpoint: str = Field("", env="OTEL_EXPORTER_OTLP_ENDPOINT")

    class Config:
        env_file = ROOT_DIR / ".env"
        case_sensitive = True

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
