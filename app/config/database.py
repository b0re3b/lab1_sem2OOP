import os
import logging
from functools import lru_cache
from typing import Optional, Dict, Any
from contextlib import contextmanager
from pydantic import BaseSettings, validator
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseSettings):
    """Конфігурація підключення до PostgreSQL"""

    # Основні параметри підключення
    DB_HOST: str = "localhost"
    DB_PORT: int = 5433
    DB_NAME: str = "lab11"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "28488476"
    DB_SCHEMA: str = "airline"

    # SSL параметри
    DB_SSL_MODE: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full
    DB_SSL_CERT: Optional[str] = None
    DB_SSL_KEY: Optional[str] = None
    DB_SSL_ROOT_CERT: Optional[str] = None

    # Connection Pool параметри
    DB_POOL_MIN_CONN: int = 2
    DB_POOL_MAX_CONN: int = 20
    DB_POOL_CONNECTION_TIMEOUT: int = 30
    DB_POOL_IDLE_TIMEOUT: int = 300  # 5 хвилин

    # Параметри запитів
    DB_QUERY_TIMEOUT: int = 30
    DB_STATEMENT_TIMEOUT: int = 60000  # 60 секунд в мілісекундах

    # Retry параметри
    DB_MAX_RETRIES: int = 3
    DB_RETRY_DELAY: float = 1.0

    # Моніторинг
    DB_LOG_QUERIES: bool = False
    DB_LOG_SLOW_QUERIES: bool = True
    DB_SLOW_QUERY_THRESHOLD: float = 1.0  # секунди

    @validator('DB_PORT')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

    @validator('DB_SSL_MODE')
    def validate_ssl_mode(cls, v):
        valid_modes = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']
        if v not in valid_modes:
            raise ValueError(f'SSL mode must be one of: {valid_modes}')
        return v

    @property
    def database_url(self) -> str:
        """Генерує URL для підключення до бази даних"""
        url = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

        params = []
        if self.DB_SSL_MODE != "prefer":
            params.append(f"sslmode={self.DB_SSL_MODE}")

        if self.DB_SSL_CERT:
            params.append(f"sslcert={self.DB_SSL_CERT}")

        if self.DB_SSL_KEY:
            params.append(f"sslkey={self.DB_SSL_KEY}")

        if self.DB_SSL_ROOT_CERT:
            params.append(f"sslrootcert={self.DB_SSL_ROOT_CERT}")

        if params:
            url += "?" + "&".join(params)

        return url

    @property
    def connection_params(self) -> Dict[str, Any]:
        """Параметри для psycopg2 підключення"""
        params = {
            'host': self.DB_HOST,
            'port': self.DB_PORT,
            'database': self.DB_NAME,
            'user': self.DB_USER,
            'password': self.DB_PASSWORD,
            'sslmode': self.DB_SSL_MODE,
            'connect_timeout': self.DB_POOL_CONNECTION_TIMEOUT,
            'application_name': 'airline_system',
            'options': f'-c search_path={self.DB_SCHEMA}'
        }

        if self.DB_SSL_CERT:
            params['sslcert'] = self.DB_SSL_CERT

        if self.DB_SSL_KEY:
            params['sslkey'] = self.DB_SSL_KEY

        if self.DB_SSL_ROOT_CERT:
            params['sslrootcert'] = self.DB_SSL_ROOT_CERT

        return params

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class DatabaseConnectionPool:
    """Менеджер connection pool для PostgreSQL"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self._create_pool()

    def _create_pool(self):
        """Створює connection pool"""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.DB_POOL_MIN_CONN,
                maxconn=self.config.DB_POOL_MAX_CONN,
                cursor_factory=RealDictCursor,
                **self.config.connection_params
            )
            logger.info(f"Database connection pool created successfully. "
                        f"Min connections: {self.config.DB_POOL_MIN_CONN}, "
                        f"Max connections: {self.config.DB_POOL_MAX_CONN}")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Контекстний менеджер для отримання підключення з пулу"""
        connection = None
        try:
            if not self._pool:
                raise Exception("Connection pool is not initialized")

            connection = self._pool.getconn()
            if connection:
                # Встановлюємо autocommit за замовчуванням
                connection.autocommit = True
                yield connection
            else:
                raise Exception("Unable to get connection from pool")

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                self._pool.putconn(connection)

    @contextmanager
    def get_cursor(self, commit: bool = True):
        """Контекстний менеджер для отримання курсора з автоматичним керуванням транзакціями"""
        with self.get_connection() as connection:
            connection.autocommit = False
            cursor = connection.cursor()
            try:
                yield cursor
                if commit:
                    connection.commit()
            except Exception as e:
                connection.rollback()
                logger.error(f"Database query error: {e}")
                raise
            finally:
                cursor.close()

    def close_all_connections(self):
        """Закриває всі підключення в пулі"""
        if self._pool:
            self._pool.closeall()
            logger.info("All database connections closed")

    def test_connection(self) -> bool:
        """Тестує підключення до бази даних"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_pool_status(self) -> Dict[str, Any]:
        """Повертає статус connection pool"""
        if not self._pool:
            return {"status": "not_initialized"}

        return {
            "status": "active",
            "min_connections": self.config.DB_POOL_MIN_CONN,
            "max_connections": self.config.DB_POOL_MAX_CONN,
            "closed": self._pool.closed
        }


# Глобальні екземпляри
_db_config: Optional[DatabaseConfig] = None
_connection_pool: Optional[DatabaseConnectionPool] = None


@lru_cache()
def get_database_config() -> DatabaseConfig:
    """Повертає конфігурацію бази даних з кешуванням"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_connection_pool() -> DatabaseConnectionPool:
    """Повертає глобальний connection pool"""
    global _connection_pool
    if _connection_pool is None:
        config = get_database_config()
        _connection_pool = DatabaseConnectionPool(config)
    return _connection_pool


def init_database():
    """Ініціалізує підключення до бази даних"""
    pool = get_connection_pool()
    if not pool.test_connection():
        raise Exception("Failed to connect to database")
    logger.info("Database initialized successfully")


def close_database():
    """Закриває всі підключення до бази даних"""
    global _connection_pool
    if _connection_pool:
        _connection_pool.close_all_connections()
        _connection_pool = None


def execute_query(query: str, params: tuple = None, fetch: bool = True):
    """
    Виконує SQL запит з автоматичним керуванням підключенням

    Args:
        query: SQL запит
        params: Параметри для запиту
        fetch: Чи потрібно повертати результат

    Returns:
        Результат запиту або None
    """
    pool = get_connection_pool()
    with pool.get_cursor() as cursor:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        return None


def execute_many(query: str, params_list: list):
    """
    Виконує багато запитів з одним SQL та різними параметрами

    Args:
        query: SQL запит
        params_list: Список параметрів для кожного запиту
    """
    pool = get_connection_pool()
    with pool.get_cursor() as cursor:
        cursor.executemany(query, params_list)