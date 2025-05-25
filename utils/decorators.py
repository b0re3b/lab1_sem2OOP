import functools
import time
from typing import Any, Callable, List, Optional, Union
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime

from config.logging_config import log_info, log_error, log_warning, log_auth_event
from utils.jwt_utils import JWTManager
from models.user import User


class AuthDecorators:
    """Декоратори для авторизації та перевірки ролей"""
    def __init__(self):
        self.jwt_manager = JWTManager()
    security = HTTPBearer()

    @staticmethod
    def jwt_required(f: Callable) -> Callable:
        """Декоратор для перевірки JWT токена"""

        @functools.wraps(f)
        async def wrapper(self, *args, **kwargs):
            try:
                # Отримуємо токен з headers
                credentials: HTTPAuthorizationCredentials = Depends(AuthDecorators.security)
                token = credentials.credentials if credentials else None

                if not token:
                    log_auth_event("AUTH_FAILED", "No token provided", None)
                    raise HTTPException(status_code=401, detail="Token required")

                # Декодуємо та валідуємо токен
                payload = self.jwt_manager.decode_token(token)
                if not payload:
                    log_auth_event("AUTH_FAILED", "Invalid token", None)
                    raise HTTPException(status_code=401, detail="Invalid token")

                # Додаємо користувача до kwargs
                user = self.jwt_manager.get_user_from_token(token)
                kwargs['current_user'] = user

                log_auth_event("AUTH_SUCCESS", f"User {user.username} authenticated", user.id)
                return await f(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                log_auth_event("AUTH_FAILED", "Token expired", None)
                raise HTTPException(status_code=401, detail="Token expired")
            except Exception as e:
                log_error(f"Authentication error: {str(e)}")
                raise HTTPException(status_code=401, detail="Authentication failed")

        return wrapper

    @staticmethod
    def role_required(allowed_roles: Union[str, List[str]]) -> Callable:
        """Декоратор для перевірки ролі користувача"""
        if isinstance(allowed_roles, str):
            allowed_roles = [allowed_roles]

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                current_user: User = kwargs.get('current_user')

                if not current_user:
                    log_auth_event("ROLE_CHECK_FAILED", "No user in context", None)
                    raise HTTPException(status_code=401, detail="Authentication required")

                if current_user.role not in allowed_roles:
                    log_auth_event("ROLE_CHECK_FAILED",
                                   f"User {current_user.username} with role {current_user.role} tried to access resource requiring {allowed_roles}",
                                   current_user.id)
                    raise HTTPException(status_code=403, detail="Insufficient permissions")

                log_auth_event("ROLE_CHECK_SUCCESS",
                               f"User {current_user.username} authorized with role {current_user.role}",
                               current_user.id)
                return await f(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def admin_required(f: Callable) -> Callable:
        """Декоратор для перевірки адміністраторських прав"""
        return AuthDecorators.role_required("ADMIN")(f)

    @staticmethod
    def dispatcher_required(f: Callable) -> Callable:
        """Декоратор для перевірки прав диспетчера"""
        return AuthDecorators.role_required(["ADMIN", "DISPATCHER"])(f)


class LoggingDecorators:
    """Декоратори для логування"""

    @staticmethod
    def log_execution(operation_name: str = None) -> Callable:
        """Декоратор для логування виконання функцій"""

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                func_name = operation_name or f.__name__
                start_time = time.time()

                # Логуємо початок виконання
                log_info(f"Starting {func_name}")

                try:
                    result = await f(*args, **kwargs)
                    execution_time = time.time() - start_time
                    log_info(f"Completed {func_name} in {execution_time:.2f}s")
                    return result

                except Exception as e:
                    execution_time = time.time() - start_time
                    log_error(f"Error in {func_name} after {execution_time:.2f}s: {str(e)}")
                    raise

            return wrapper

        return decorator

    @staticmethod
    def log_database_operation(table_name: str, operation_type: str) -> Callable:
        """Декоратор для логування операцій з базою даних"""

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                try:
                    result = f(*args, **kwargs)
                    log_info(f"Database {operation_type} on {table_name} completed successfully")
                    return result
                except Exception as e:
                    log_error(f"Database {operation_type} on {table_name} failed: {str(e)}")
                    raise

            return wrapper

        return decorator


class ValidationDecorators:
    """Декоратори для валідації"""

    @staticmethod
    def validate_input(validator_func: Callable) -> Callable:
        """Декоратор для валідації вхідних даних"""

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                try:
                    # Валідуємо дані за допомогою переданої функції
                    validator_func(*args, **kwargs)
                    return await f(*args, **kwargs)
                except ValueError as e:
                    log_warning(f"Validation failed in {f.__name__}: {str(e)}")
                    raise HTTPException(status_code=400, detail=str(e))
                except Exception as e:
                    log_error(f"Validation error in {f.__name__}: {str(e)}")
                    raise HTTPException(status_code=400, detail="Validation failed")

            return wrapper

        return decorator


class ErrorHandlingDecorators:
    """Декоратори для обробки помилок"""

    @staticmethod
    def handle_exceptions(default_status_code: int = 500) -> Callable:
        """Декоратор для обробки винятків"""

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                try:
                    return await f(*args, **kwargs)
                except HTTPException:
                    # Пропускаємо HTTP винятки без змін
                    raise
                except ValueError as e:
                    log_warning(f"Value error in {f.__name__}: {str(e)}")
                    raise HTTPException(status_code=400, detail=str(e))
                except Exception as e:
                    log_error(f"Unexpected error in {f.__name__}: {str(e)}")
                    raise HTTPException(
                        status_code=default_status_code,
                        detail="Internal server error"
                    )

            return wrapper

        return decorator

    @staticmethod
    def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable:
        """Декоратор для повторного виконання при помилці"""

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(max_retries + 1):
                    try:
                        return await f(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            log_warning(
                                f"Attempt {attempt + 1} failed for {f.__name__}: {str(e)}. Retrying in {delay}s...")
                            time.sleep(delay)
                        else:
                            log_error(f"All {max_retries + 1} attempts failed for {f.__name__}: {str(e)}")

                raise last_exception

            return wrapper

        return decorator


class PerformanceDecorators:
    """Декоратори для моніторингу продуктивності"""

    @staticmethod
    def measure_time(threshold_seconds: float = None) -> Callable:
        """Декоратор для вимірювання часу виконання"""

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                result = await f(*args, **kwargs)
                execution_time = time.time() - start_time

                if threshold_seconds and execution_time > threshold_seconds:
                    log_warning(
                        f"Slow execution: {f.__name__} took {execution_time:.2f}s (threshold: {threshold_seconds}s)")
                else:
                    log_info(f"Execution time for {f.__name__}: {execution_time:.2f}s")

                return result

            return wrapper

        return decorator

    @staticmethod
    def cache_result(expiry_seconds: int = 300) -> Callable:
        """Простий декоратор для кешування результатів (в пам'яті)"""
        cache = {}

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                # Створюємо ключ кешу
                cache_key = f"{f.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                current_time = time.time()

                # Перевіряємо кеш
                if cache_key in cache:
                    cached_result, cached_time = cache[cache_key]
                    if current_time - cached_time < expiry_seconds:
                        log_info(f"Cache hit for {f.__name__}")
                        return cached_result

                # Виконуємо функцію та кешуємо результат
                result = await f(*args, **kwargs)
                cache[cache_key] = (result, current_time)
                log_info(f"Cache miss for {f.__name__}, result cached")

                return result

            return wrapper

        return decorator


# Комбіновані декоратори для зручності
def authenticated_admin(f: Callable) -> Callable:
    """Комбінований декоратор: JWT + права адміністратора + логування"""
    return LoggingDecorators.log_execution()(
        ErrorHandlingDecorators.handle_exceptions()(
            AuthDecorators.admin_required(
                AuthDecorators.jwt_required(f)
            )
        )
    )


def authenticated_dispatcher(f: Callable) -> Callable:
    """Комбінований декоратор: JWT + права диспетчера + логування"""
    return LoggingDecorators.log_execution()(
        ErrorHandlingDecorators.handle_exceptions()(
            AuthDecorators.dispatcher_required(
                AuthDecorators.jwt_required(f)
            )
        )
    )

