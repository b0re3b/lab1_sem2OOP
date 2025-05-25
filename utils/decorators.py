import time
import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import json
import hashlib

logger = logging.getLogger(__name__)

_cache_storage: Dict[str, Dict[str, Any]] = {}


def log_execution_time(func: Callable) -> Callable:

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"Function {func.__name__} executed in {execution_time:.4f} seconds"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed after {execution_time:.4f} seconds: {str(e)}"
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"Function {func.__name__} executed in {execution_time:.4f} seconds"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed after {execution_time:.4f} seconds: {str(e)}"
            )
            raise

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def validate_input(validation_func: Callable) -> Callable:


    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract data from kwargs or args
            data = kwargs.get('data') or (args[1] if len(args) > 1 else None)
            if data:
                validation_result = validation_func(data)
                if not validation_result.is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Validation failed: {validation_result.errors}"
                    )
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            data = kwargs.get('data') or (args[1] if len(args) > 1 else None)
            if data:
                validation_result = validation_func(data)
                if not validation_result.is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Validation failed: {validation_result.errors}"
                    )
            return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def require_role(allowed_roles: Union[str, List[str]]) -> Callable:

    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                for arg in args:
                    if hasattr(arg, 'role'):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_role = getattr(current_user, 'role', None)
            if user_role not in allowed_roles:
                logger.warning(
                    f"Access denied for user {current_user.username} "
                    f"with role {user_role}. Required roles: {allowed_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {allowed_roles}"
                )

            logger.info(
                f"Access granted for user {current_user.username} "
                f"with role {user_role} to function {func.__name__}"
            )
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                for arg in args:
                    if hasattr(arg, 'role'):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_role = getattr(current_user, 'role', None)
            if user_role not in allowed_roles:
                logger.warning(
                    f"Access denied for user {current_user.username} "
                    f"with role {user_role}. Required roles: {allowed_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {allowed_roles}"
                )

            logger.info(
                f"Access granted for user {current_user.username} "
                f"with role {user_role} to function {func.__name__}"
            )
            return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def audit_operation(operation_type: str, table_name: str) -> Callable:


    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            user_id = getattr(current_user, 'id', None) if current_user else None

            start_time = datetime.utcnow()

            try:
                result = await func(*args, **kwargs)

                logger.info(
                    f"AUDIT: User {user_id} performed {operation_type} "
                    f"on {table_name} at {start_time}"
                )



                return result

            except Exception as e:
                # Log failed operation
                logger.error(
                    f"AUDIT: User {user_id} failed {operation_type} "
                    f"on {table_name} at {start_time}. Error: {str(e)}"
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            user_id = getattr(current_user, 'id', None) if current_user else None

            start_time = datetime.utcnow()

            try:
                result = func(*args, **kwargs)

                logger.info(
                    f"AUDIT: User {user_id} performed {operation_type} "
                    f"on {table_name} at {start_time}"
                )

                return result

            except Exception as e:
                logger.error(
                    f"AUDIT: User {user_id} failed {operation_type} "
                    f"on {table_name} at {start_time}. Error: {str(e)}"
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def handle_db_errors(func: Callable) -> Callable:


    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error in {func.__name__}: {str(e)}")
            if "unique" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Resource already exists with this identifier"
                )
            elif "foreign key" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Referenced resource does not exist"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data integrity constraint violation"
                )
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed"
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error in {func.__name__}: {str(e)}")
            if "unique" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Resource already exists with this identifier"
                )
            elif "foreign key" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Referenced resource does not exist"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data integrity constraint violation"
                )
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed"
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def cache_result(expire_minutes: int = 10) -> Callable:


    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = _create_cache_key(func.__name__, args, kwargs)

            if cache_key in _cache_storage:
                cached_data = _cache_storage[cache_key]
                if datetime.utcnow() < cached_data['expires_at']:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_data['result']
                else:
                    del _cache_storage[cache_key]

            result = await func(*args, **kwargs)
            _cache_storage[cache_key] = {
                'result': result,
                'expires_at': datetime.utcnow() + timedelta(minutes=expire_minutes)
            }

            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = _create_cache_key(func.__name__, args, kwargs)

            if cache_key in _cache_storage:
                cached_data = _cache_storage[cache_key]
                if datetime.utcnow() < cached_data['expires_at']:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_data['result']
                else:
                    del _cache_storage[cache_key]

            result = func(*args, **kwargs)
            _cache_storage[cache_key] = {
                'result': result,
                'expires_at': datetime.utcnow() + timedelta(minutes=expire_minutes)
            }

            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _create_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:

    key_data = {
        'func': func_name,
        'args': args,
        'kwargs': kwargs
    }

    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def clear_cache():
    global _cache_storage
    _cache_storage.clear()
    logger.info("Cache cleared")


def get_cache_stats() -> Dict[str, Any]:
    total_entries = len(_cache_storage)
    expired_entries = 0

    current_time = datetime.utcnow()
    for cached_data in _cache_storage.values():
        if current_time >= cached_data['expires_at']:
            expired_entries += 1

    return {
        'total_entries': total_entries,
        'active_entries': total_entries - expired_entries,
        'expired_entries': expired_entries
    }