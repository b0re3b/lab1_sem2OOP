import time
from functools import wraps
from typing import Callable, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.logging_config import get_logger, log_access, log_info, log_error

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для логування запитів та відповідей
    """

    def __init__(self, app, exclude_paths: List[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обробляє кожен HTTP запит та логує інформацію
        """
        # Пропускаємо логування для виключених шляхів
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        start_time = time.time()

        # Логування вхідного запиту
        await self._log_request(request)

        try:
            # Виконуємо запит
            response = await call_next(request)

            # Розраховуємо час виконання
            process_time = time.time() - start_time

            # Логування відповіді
            await self._log_response(request, response, process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            await self._log_error(request, e, process_time)
            raise

    async def _log_request(self, request: Request):
        """
        Логує вхідний запит
        """
        try:
            client_ip = request.client.host if request.client else "Unknown"
            user_agent = request.headers.get("User-Agent", "Unknown")

            # Отримуємо інформацію про користувача якщо доступна
            user_info = "Anonymous"
            if hasattr(request.state, 'current_user'):
                user_data = request.state.current_user
                user_info = user_data.get('username', 'Unknown')

            log_data = {
                "event": "request_received",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user": user_info,
                "headers": {
                    key: value for key, value in request.headers.items()
                    if key.lower() not in ['authorization', 'cookie']
                }
            }

            log_access(f"Incoming request", extra=log_data)

        except Exception as e:
            log_error(f"Error logging request: {str(e)}")

    async def _log_response(self, request: Request, response: Response, process_time: float):
        """
        Логує відповідь
        """
        try:
            client_ip = request.client.host if request.client else "Unknown"

            user_info = "Anonymous"
            if hasattr(request.state, 'current_user'):
                user_data = request.state.current_user
                user_info = user_data.get('username', 'Unknown')

            log_data = {
                "event": "response_sent",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "client_ip": client_ip,
                "user": user_info,
                "response_headers": dict(response.headers)
            }

            # Визначаємо рівень логування на основі статус коду
            if response.status_code >= 500:
                log_error(f"Request completed with server error", extra=log_data)
            elif response.status_code >= 400:
                log_info(f"Request completed with client error", extra=log_data)
            else:
                log_access(f"Request completed successfully", extra=log_data)

        except Exception as e:
            log_error(f"Error logging response: {str(e)}")

    async def _log_error(self, request: Request, error: Exception, process_time: float):
        """
        Логує помилки під час обробки запиту
        """
        try:
            client_ip = request.client.host if request.client else "Unknown"

            user_info = "Anonymous"
            if hasattr(request.state, 'current_user'):
                user_data = request.state.current_user
                user_info = user_data.get('username', 'Unknown')

            log_data = {
                "event": "request_error",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "process_time": round(process_time, 4),
                "client_ip": client_ip,
                "user": user_info
            }

            log_error(f"Request failed with error: {str(error)}", extra=log_data)

        except Exception as e:
            log_error(f"Error logging error: {str(e)}")


def request_logging(operation_name: str = None):
    """
    Декоратор для логування викликів методів
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            try:
                log_info(f"Starting operation: {func_name}")
                result = await func(*args, **kwargs)

                process_time = time.time() - start_time
                log_info(f"Operation completed: {func_name} in {process_time:.4f}s")

                return result

            except Exception as e:
                process_time = time.time() - start_time
                log_error(f"Operation failed: {func_name} in {process_time:.4f}s - {str(e)}")
                raise

        return wrapper

    return decorator