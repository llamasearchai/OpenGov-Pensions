"""Configuration management for OpenPension.

This module centralizes application configuration using Pydantic BaseSettings.
All fields are environment-overridable and validated. A companion `.env.example`
will enumerate defaults for developer onboarding.
"""

from typing import Optional

from pydantic import Field, AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings for OpenPension.

    Grouped logically for clarity. Environment variables are UPPER_SNAKE.
    """

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name: str = Field(default="OpenPension", env="APP_NAME")
    version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="local", env="ENVIRONMENT")  # local|dev|staging|prod
    debug: bool = Field(default=False, env="DEBUG")

    # ------------------------------------------------------------------
    # Database & Persistence
    # ------------------------------------------------------------------
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/opengovpension.db",
        env="DATABASE_URL",
    )
    db_echo: bool = Field(default=False, env="DB_ECHO")
    db_pool_size: int = Field(default=5, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")

    # ------------------------------------------------------------------
    # Caching / Redis
    # ------------------------------------------------------------------
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    cache_default_ttl: int = Field(default=60, env="CACHE_DEFAULT_TTL")

    # ------------------------------------------------------------------
    # Celery / Task Queue
    # ------------------------------------------------------------------
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    celery_task_soft_time_limit: int = Field(default=30, env="CELERY_TASK_SOFT_TIME_LIMIT")
    celery_task_hard_time_limit: int = Field(default=60, env="CELERY_TASK_HARD_TIME_LIMIT")

    # ------------------------------------------------------------------
    # AI / LLM Providers
    # ------------------------------------------------------------------
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama2:7b", env="OLLAMA_MODEL")

    # ------------------------------------------------------------------
    # Authentication / Security
    # ------------------------------------------------------------------
    jwt_secret: str = Field(default="change_me", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 30, env="REFRESH_TOKEN_EXPIRE_MINUTES")
    password_hash_rounds: int = Field(default=12, env="PASSWORD_HASH_ROUNDS")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    rate_limit_per_minute: int = Field(default=120, env="RATE_LIMIT_PER_MINUTE")
    cors_allow_origins: str = Field(default="*", env="CORS_ALLOW_ORIGINS")  # comma list

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    structured_logging: bool = Field(default=True, env="STRUCTURED_LOGGING")
    tracing_enabled: bool = Field(default=False, env="TRACING_ENABLED")
    otlp_endpoint: Optional[AnyHttpUrl] = Field(default=None, env="OTLP_ENDPOINT")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")

    # ------------------------------------------------------------------
    # Performance / Limits
    # ------------------------------------------------------------------
    max_concurrent_analyses: int = Field(default=5, env="MAX_CONCURRENT_ANALYSES")
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")

    # ------------------------------------------------------------------
    # Server Configuration
    # ------------------------------------------------------------------
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    reload: bool = Field(default=False, env="RELOAD")

    # ------------------------------------------------------------------
    # Datasette Integration (Legacy)
    # ------------------------------------------------------------------
    datasette_host: str = Field(default="localhost", env="DATASETTE_HOST")
    datasette_port: int = Field(default=8001, env="DATASETTE_PORT")

    # ------------------------------------------------------------------
    # Feature Flags
    # ------------------------------------------------------------------
    enable_websockets: bool = Field(default=True, env="ENABLE_WEBSOCKETS")
    enable_audit_log: bool = Field(default=True, env="ENABLE_AUDIT_LOG")

    # ------------------------------------------------------------------
    # State-Specific Configuration
    # ------------------------------------------------------------------
    default_state: str = Field(default="CA", env="DEFAULT_STATE")  # CA|IN|OH
    supported_states: str = Field(default="CA,IN,OH", env="SUPPORTED_STATES")  # comma-separated

    # ------------------------------------------------------------------
    # Security & Compliance
    # ------------------------------------------------------------------
    max_login_attempts: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    lockout_duration_minutes: int = Field(default=15, env="LOCKOUT_DURATION_MINUTES")
    session_cookie_secure: bool = Field(default=True, env="SESSION_COOKIE_SECURE")
    session_cookie_httponly: bool = Field(default=True, env="SESSION_COOKIE_HTTPONLY")
    enable_cors: bool = Field(default=True, env="ENABLE_CORS")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    enable_request_validation: bool = Field(default=True, env="ENABLE_REQUEST_VALIDATION")

    class Config:
        env_file = ".env"
        case_sensitive = False

    # Derived helpers
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def supported_states_list(self) -> list[str]:
        """Get list of supported state codes."""
        return [s.strip().upper() for s in self.supported_states.split(",") if s.strip()]

    @property
    def default_state_code(self) -> str:
        """Get default state code in uppercase."""
        return self.default_state.upper()


def get_settings() -> Settings:  # pragma: no cover - simple accessor
    return Settings()