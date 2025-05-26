import logging
import logging.handlers
import os
from typing import Optional


class LoggingConfig:
    """Клас для налаштування та управління системою логування авіакомпанії"""

    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper())

        # Створюємо директорію для логів
        self._create_log_directory()

        # Ініціалізуємо логери
        self.app_logger = None
        self.access_logger = None

        # Налаштовуємо логування
        self.setup_logging()

    def _create_log_directory(self) -> None:
        """Створює директорію для логів якщо її немає"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _get_formatter(self, format_type: str = "standard") -> logging.Formatter:
        """Повертає форматер для логів"""
        if format_type == "access":
            return logging.Formatter('%(asctime)s - %(message)s')

        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )

    def _create_rotating_handler(self, filename: str, level: int,
                                 formatter: logging.Formatter) -> logging.handlers.RotatingFileHandler:
        """Створює RotatingFileHandler з заданими параметрами"""
        handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, filename),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler

    def setup_logging(self) -> None:
        """Налаштовує систему логування"""
        # Основний логер додатку
        self.app_logger = logging.getLogger("airline_system")
        self.app_logger.setLevel(self.log_level)

        # Очищаємо попередні хендлери якщо є
        self.app_logger.handlers.clear()

        formatter = self._get_formatter("standard")

        # Хендлер для загальних логів
        app_handler = self._create_rotating_handler("app.log", logging.INFO, formatter)

        # Хендлер для помилок
        error_handler = self._create_rotating_handler("error.log", logging.ERROR, formatter)

        # Хендлер для консолі
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)

        # Додаємо хендлери
        self.app_logger.addHandler(app_handler)
        self.app_logger.addHandler(error_handler)
        self.app_logger.addHandler(console_handler)

        # Налаштовуємо access логер
        self._setup_access_logger()

    def _setup_access_logger(self) -> None:
        """Налаштовує логер для HTTP запитів"""
        self.access_logger = logging.getLogger("airline_system.access")
        self.access_logger.setLevel(logging.INFO)

        # Очищаємо попередні хендлери
        self.access_logger.handlers.clear()

        access_formatter = self._get_formatter("access")
        access_handler = self._create_rotating_handler("access.log", logging.INFO, access_formatter)

        self.access_logger.addHandler(access_handler)

        # Запобігаємо передачі повідомлень до батьківського логера
        self.access_logger.propagate = False

    def log_info(self, message: str) -> None:
        """Логування інформаційних повідомлень"""
        self.app_logger.info(message)

    def log_error(self, message: str, exc_info: Optional[Exception] = None) -> None:
        """Логування помилок"""
        self.app_logger.error(message, exc_info=exc_info)

    def log_warning(self, message: str) -> None:
        """Логування попереджень"""
        self.app_logger.warning(message)

    def log_debug(self, message: str) -> None:
        """Логування налагоджувальних повідомлень"""
        self.app_logger.debug(message)

    def log_access(self, method: str, path: str, status_code: int,
                   user_id: Optional[int] = None, ip_address: Optional[str] = None,
                   response_time: Optional[float] = None) -> None:
        """Логування HTTP запитів"""
        user_info = f"user_id={user_id}" if user_id else "anonymous"
        ip_info = f"ip={ip_address}" if ip_address else "ip=unknown"
        time_info = f"time={response_time:.3f}s" if response_time else ""

        message = f"{method} {path} - {status_code} - {user_info} - {ip_info} {time_info}".strip()
        self.access_logger.info(message)

    def log_database_operation(self, operation: str, table: str, record_id: Optional[int] = None,
                               user_id: Optional[int] = None) -> None:
        """Логування операцій з базою даних"""
        record_info = f"record_id={record_id}" if record_id else ""
        user_info = f"user_id={user_id}" if user_id else ""

        message = f"DB {operation} on {table} - {record_info} {user_info}".strip()
        self.app_logger.info(message)

    def log_auth_event(self, event_type: str, username: str, ip_address: Optional[str] = None,
                       success: bool = True) -> None:
        """Логування подій авторизації"""
        status = "SUCCESS" if success else "FAILED"
        ip_info = f"from {ip_address}" if ip_address else ""

        message = f"AUTH {event_type} - {username} - {status} {ip_info}".strip()

        if success:
            self.app_logger.info(message)
        else:
            self.app_logger.warning(message)

    def get_logger(self, name: str = None) -> logging.Logger:
        """Повертає логер з заданим ім'ям"""
        if name:
            return logging.getLogger(f"airline_system.{name}")
        return self.app_logger

    def shutdown(self) -> None:
        """Закриває всі хендлери логування"""
        if self.app_logger:
            for handler in self.app_logger.handlers:
                handler.close()

        if self.access_logger:
            for handler in self.access_logger.handlers:
                handler.close()


def setup_logging(self) -> None:
    logger_config.setup_logging()
def get_logger(name: str = None) -> None:
    logger_config.get_logger(name)
# Функції для зворотної сумісності та зручності використання
def log_info(message: str) -> None:
    """Логування інформаційних повідомлень"""
    logger_config.log_info(message)


def log_error(message: str, exc_info: Optional[Exception] = None) -> None:
    """Логування помилок"""
    logger_config.log_error(message, exc_info)


def log_warning(message: str) -> None:
    """Логування попереджень"""
    logger_config.log_warning(message)


def log_debug(message: str) -> None:
    """Логування налагоджувальних повідомлень"""
    logger_config.log_debug(message)


def log_access(method: str, path: str, status_code: int,
               user_id: Optional[int] = None, ip_address: Optional[str] = None,
               response_time: Optional[float] = None) -> None:
    """Логування HTTP запитів"""
    logger_config.log_access(method, path, status_code, user_id, ip_address, response_time)


def log_database_operation(operation: str, table: str, record_id: Optional[int] = None,
                           user_id: Optional[int] = None) -> None:
    """Логування операцій з базою даних"""
    logger_config.log_database_operation(operation, table, record_id, user_id)


def log_auth_event(event_type: str, username: str, ip_address: Optional[str] = None,
                   success: bool = True) -> None:
    """Логування подій авторизації"""
    logger_config.log_auth_event(event_type, username, ip_address, success)
# Глобальний екземпляр для використання в додатку
logger_config = LoggingConfig()