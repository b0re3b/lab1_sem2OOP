import logging
from functools import wraps
from typing import Optional, List, Callable

from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config.keycloak import KeycloakClient, keycloak_config
from app.config import get_settings
from app.models.user import User
from app.services.auth_service import AuthService
from app.controller import get_auth_service
from app.utils.jwt_utils import JWTManager, KeycloakJWTManager

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthMiddleware:
    """
    Middleware для обробки аутентифікації та авторизації
    Перевіряє JWT токени та інтеграцію з Keycloak
    """

    def __init__(self, keycloak_client: KeycloakClient, jwt_manager: JWTManager):
        self.keycloak_client = keycloak_client
        self.jwtkey_manager = KeycloakJWTManager(keycloak_config)
        self.jwt_manager = JWTManager()
        self.settings = get_settings()

    def __call__(self, request: Request, call_next):
        """
        Основний метод middleware для обробки запитів
        """
        # Перевіряємо чи потрібна аутентифікація для цього endpoint
        if self._is_public_endpoint(request.url.path):
            return  call_next(request)

        try:
            # Отримуємо токен з заголовків
            token = self._extract_token_from_request(request)
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token required"
                )

            # Валідуємо токен
            user_info =  self._validate_token(token)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )

            # Додаємо інформацію про користувача до request
            request.state.current_user = user_info
            request.state.token = token

            logger.info(f"Authenticated user: {user_info.get('username', 'Unknown')}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

        return  call_next(request)

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Перевіряє чи є endpoint публічним (не потребує аутентифікації)
        """
        public_paths = [
            "/docs", "/redoc", "/openapi.json",
            "/health", "/auth/login", "/auth/keycloak",
            "/auth/callback"
        ]
        return any(path.startswith(public_path) for public_path in public_paths)

    def _extract_token_from_request(self, request: Request) -> Optional[str]:
        """
        Витягує JWT токен з заголовків запиту
        """
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization.split(" ")[1]
        return None

    async def _validate_token(self, token: str) -> Optional[dict]:
        """
        Валідує JWT токен (локальний або Keycloak)
        """
        try:
            # Спочатку пробуємо валідувати як локальний JWT
            if self.jwt_manager.is_token_valid(token):
                return self.jwt_manager.get_user_from_token(token)
        except:
            pass

        try:
            # Якщо не вдалося - пробуємо Keycloak токен
            keycloak_user_info = self.jwtkey_manager.decode_keycloak_token(token)
            if keycloak_user_info:
                return keycloak_user_info
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")

        return None


def jwt_required(func: Callable = None, *, optional: bool = False):
    """
    Декоратор для перевірки JWT токену
    """

    def decorator(f: Callable):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            # Отримуємо request з args або kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            if not optional and not hasattr(request.state, 'current_user'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            return await f(*args, **kwargs)

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def role_required(required_roles: List[str]):
    """
    Декоратор для перевірки ролі користувача
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Отримуємо request
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break

            if not request or not hasattr(request.state, 'current_user'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_info = request.state.current_user
            user_role = user_info.get('role', '').upper()

            if user_role not in [role.upper() for role in required_roles]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(required_roles)}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def get_current_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Dependency для отримання поточного користувача
    """
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )