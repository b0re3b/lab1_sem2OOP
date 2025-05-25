import os
from functools import lru_cache
from typing import Optional, List
from pydantic import BaseSettings, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main application settings."""

    # Application settings
    app_name: str = "Airline Management System"
    app_version: str = "1.0.0"
    app_description: str = "Laboratory work: Airline crew management system"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # Database settings
    database_url: str
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Security settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Keycloak settings
    keycloak_server_url: str
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: str
    keycloak_admin_username: Optional[str] = None
    keycloak_admin_password: Optional[str] = None

    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # Redis settings (для кешування та сесій)
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # File upload settings
    upload_max_size: int = 10 * 1024 * 1024  # 10MB
    upload_allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"]
    upload_path: str = "uploads"

    # Email settings (для сповіщень)
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True

    # Pagination settings
    default_page_size: int = 20
    max_page_size: int = 100

    # Feature flags
    enable_email_notifications: bool = False
    enable_audit_logging: bool = True
    enable_rate_limiting: bool = True
    enable_metrics: bool = False

    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("Database URL must be PostgreSQL")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()