import logging
from functools import lru_cache
from typing import AsyncGenerator, Optional, Any, Generator
from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration class."""

    def __init__(self, settings: Optional[object] = None):
        self.settings = settings or get_settings()
        self._engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL."""
        return self.settings.database_url.replace("+asyncpg", "")

    @property
    def async_database_url(self) -> str:
        """Get asynchronous database URL."""
        if "+asyncpg" not in self.settings.database_url:
            return self.settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.settings.database_url

    def get_engine(self):
        """Get or create synchronous database engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.sync_database_url,
                echo=self.settings.database_echo,
                poolclass=QueuePool,
                pool_size=self.settings.database_pool_size,
                max_overflow=self.settings.database_max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,  # 1 hour
                connect_args={
                    "application_name": self.settings.app_name,
                    "options": "-c timezone=UTC"
                }
            )

            # Add connection event listeners
            self._setup_connection_events(self._engine)

        return self._engine

    def get_async_engine(self):
        """Get or create asynchronous database engine."""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self.async_database_url,
                echo=self.settings.database_echo,
                pool_size=self.settings.database_pool_size,
                max_overflow=self.settings.database_max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,  # 1 hour
                connect_args={
                    "server_settings": {
                        "application_name": self.settings.app_name,
                        "timezone": "UTC"
                    }
                }
            )
        return self._async_engine

    def get_session_factory(self):
        """Get synchronous session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.get_engine(),
                class_=Session,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._session_factory

    def get_async_session_factory(self):
        """Get asynchronous session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.get_async_engine(),
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._async_session_factory

    def _setup_connection_events(self, engine):
        """Setup database connection events for monitoring."""

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set database pragmas on connection."""
            logger.debug("Database connection established")

        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout."""
            logger.debug("Connection checked out from pool")

        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin."""
            logger.debug("Connection checked in to pool")

    def create_session(self) -> Session:
        """Create new synchronous database session."""
        return self.get_session_factory()()

    async def create_async_session(self) -> AsyncSession:
        """Create new asynchronous database session."""
        return self.get_async_session_factory()()

    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency for getting async database session."""
        async with self.get_async_session_factory()() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def get_session(self) -> Generator[Session, Any, None]:
        """Dependency for getting sync database session."""
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def close_connections(self):
        """Close all database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("Async database connections closed")

        if self._engine:
            self._engine.dispose()
            logger.info("Sync database connections closed")


# Create declarative base for SQLAlchemy models
Base = declarative_base()


@lru_cache()
def get_database_config() -> DatabaseConfig:
    """Get cached database configuration."""
    return DatabaseConfig()


# Dependency functions for FastAPI
def get_db() -> Generator[Session, Any, None]:
    """FastAPI dependency for getting database session."""
    db_config = get_database_config()
    session = db_config.create_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession | Any, Any]:
    """FastAPI dependency for getting async database session."""
    db_config = get_database_config()
    async with db_config.get_async_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
