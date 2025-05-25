import logging
import logging.config
import os
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional
import structlog

from .settings import get_settings


class LoggingConfig:
    """Logging configuration class."""

    def __init__(self, settings: Optional[object] = None):
        self.settings = settings or get_settings()
        self._setup_directories()

    def _setup_directories(self):
        """Create logging directories if they don't exist."""
        log_dir = Path(self.settings.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create additional log directories
        for log_type in ["error", "access", "audit"]:
            (log_dir / log_type).mkdir(exist_ok=True)

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        log_dir = Path(self.settings.log_file).parent

        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "simple": {
                    "format": "%(levelname)s - %(message)s"
                },
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s"
                },
                "access": {
                    "format": "%(asctime)s - %(remote_addr)s - %(method)s %(url)s - %(status_code)s - %(duration)s ms"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "stream": sys.stdout
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": self.settings.log_level,
                    "formatter": "detailed",
                    "filename": str(log_dir / "app.log"),
                    "maxBytes": self.settings.log_max_size,
                    "backupCount": self.settings.log_backup_count,
                    "encoding": "utf-8"
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": str(log_dir / "error" / "error.log"),
                    "maxBytes": self.settings.log_max_size,
                    "backupCount": self.settings.log_backup_count,
                    "encoding": "utf-8"
                },
                "access_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "access",
                    "filename": str(log_dir / "access" / "access.log"),
                    "maxBytes": self.settings.log_max_size,
                    "backupCount": self.settings.log_backup_count,
                    "encoding": "utf-8"
                },
                "audit_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": str(log_dir / "audit" / "audit.log"),
                    "maxBytes": self.settings.log_max_size,
                    "backupCount": self.settings.log_backup_count,
                    "encoding": "utf-8"
                }
            },
            "loggers": {
                "": {  # Root logger
                    "level": self.settings.log_level,
                    "handlers": ["console", "file", "error_file"],
                    "propagate": False
                },
                "airline": {  # Application logger
                    "level": self.settings.log_level,
                    "handlers": ["console", "file", "error_file"],
                    "propagate": False
                },
                "airline.access": {  # Access logger
                    "level": "INFO",
                    "handlers": ["access_file"],
                    "propagate": False
                },
                "airline.audit": {  # Audit logger
                    "level": "INFO",
                    "handlers": ["audit_file"],
                    "propagate": False
                },
                "airline.security": {  # Security logger
                    "level": "INFO",
                    "handlers": ["file", "error_file", "audit_file"],
                    "propagate": False
                },
                "sqlalchemy.engine": {  # Database logger
                    "level": "WARNING" if not self.settings.database_echo else "INFO",
                    "handlers": ["file"],
                    "propagate": False
                },
                "uvicorn": {  # Uvicorn logger
                    "level": "INFO",
                    "handlers": ["console", "access_file"],
                    "propagate": False
                },
                "uvicorn.access": {  # Uvicorn access logger
                    "level": "INFO",
                    "handlers": ["access_file"],
                    "propagate": False
                }
            }
        }

        return config

    def setup_structlog(self):
        """Setup structured logging with structlog."""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    def get_audit_logger(self):
        """Get audit logger for security events."""
        return logging.getLogger("airline.audit")

    def get_access_logger(self):
        """Get access logger for HTTP requests."""
        return logging.getLogger("airline.access")

    def get_security_logger(self):
        """Get security logger for security events."""
        return logging.getLogger("airline.security")


def setup_logging():
    """Setup application logging."""
    logging_config = LoggingConfig()
    config = logging_config.get_logging_config()

    # Apply logging configuration
    logging.config.dictConfig(config)

    # Setup structured logging
    logging_config.setup_structlog()

    # Log startup message
    logger = logging.getLogger("airline")
    logger.info(f"Logging configured - Level: {logging_config.settings.log_level}")

    return logging_config


@lru_cache()
def get_logging_config() -> LoggingConfig:
    """Get cached logging configuration."""
    return LoggingConfig()