import os
from functools import lru_cache
from typing import List, Optional
from pydantic import BaseSettings, field_validator


class Settings(BaseSettings):
    """Основні налаштування додатка"""

    # Загальні налаштування
    APP_NAME: str = "Airline Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "eyJhbGciOiJIUzUxMiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI0MzNhNjQwOS1iM2Y3LTQwY2ItOGUyNi0xMTQ0ODg3ZDViMWYifQ.eyJleHAiOjE3NTA4MTQ5OTgsImlhdCI6MTc0ODIyMjk5OCwianRpIjoiYmY5YWMyZTEtZWJlNS00YzI3LTgzYTUtNjFiMGRkNjZjZTdkIiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL3JlYWxtcy9tYXN0ZXIiLCJhdWQiOiJodHRwOi8vbG9jYWxob3N0OjgwODAvcmVhbG1zL21hc3RlciIsInR5cCI6IkluaXRpYWxBY2Nlc3NUb2tlbiJ9.Kgm7hXZ2uJdcdOPI1yvFj2kUYhaW-yCpuXZp2IcUgy_AtkREF5A44rXTVRBDglQug8SV2ubp6jSjl5XOt1Yy-Qe"

    # Сервер
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # JWT налаштування
    JWT_SECRET_KEY: str = "jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 днів

    # Безпека
    BCRYPT_ROUNDS: int = 12

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Timezone
    TIMEZONE: str = "Europe/Kiev"

    # Логування
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # Пагінація
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Файлова система
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"]

    # Redis (для кешування, якщо потрібно)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None

    # Email (для сповіщень)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True

    # Моніторинг
    ENABLE_METRICS: bool = False
    METRICS_PORT: int = 9090

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Парсинг CORS origins з рядка або списку"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator('CORS_ALLOW_METHODS', mode='before')
    @classmethod
    def parse_cors_methods(cls, v):
        """Парсинг CORS methods з рядка або списку"""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @field_validator('ALLOWED_EXTENSIONS', mode='before')
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Парсинг дозволених розширень файлів"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v):
        """Валідація рівня логування"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Повертає екземпляр налаштувань з кешуванням.
    Використовується для dependency injection в FastAPI.
    """
    return Settings()


# Глобальний екземпляр налаштувань
settings = get_settings()


def get_environment() -> str:
    """Визначає поточне середовище (development, staging, production)"""
    return os.getenv("ENVIRONMENT", "development").lower()


def is_development() -> bool:
    """Перевіряє чи це середовище розробки"""
    return get_environment() == "development"


def is_production() -> bool:
    """Перевіряє чи це продакшн середовище"""
    return get_environment() == "production"


def is_testing() -> bool:
    """Перевіряє чи це тестове середовище"""
    return get_environment() == "testing"
