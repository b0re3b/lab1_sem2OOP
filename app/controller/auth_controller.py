import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.config.keycloak import KeycloakOAuthConfig, KeycloakConfig
from app.models.user import User
from app.services.auth_service import AuthService, AuthenticationError, AuthorizationError
from app.utils.decorators import LoggingDecorators, ErrorHandlingDecorators

log_execution = LoggingDecorators.log_execution
handle_exceptions = ErrorHandlingDecorators.handle_exceptions
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Аутентифікація"])
security = HTTPBearer()

key = KeycloakOAuthConfig(KeycloakConfig)

# Моделі запитів/відповідей
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserInfoResponse(BaseModel):
    user: User
    permissions: list[str]


class KeycloakCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


# Залежності
def get_auth_service() -> AuthService:
    return AuthService()


def get_current_user_dep(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Залежність для отримання поточного аутентифікованого користувача"""
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невірні облікові дані аутентифікації"
            )
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Помилка аутентифікації: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка сервісу аутентифікації"
        )


@router.post("/login", response_model=LoginResponse)
@log_execution
@handle_exceptions
def login(
        request: LoginRequest,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Аутентифікація користувача за ім'ям та паролем
    """
    try:
        result = auth_service.login(request.username, request.password)
        return LoginResponse(**result)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Помилка входу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка сервісу входу"
        )


@router.post("/logout")
@log_execution
@handle_exceptions
def logout(
        current_user: User = Depends(get_current_user_dep),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Вийти з системи та анулювати токени
    """
    try:
        auth_service.logout(current_user.keycloak_id)
        return {"message": "Успішний вихід з системи"}
    except Exception as e:
        logger.error(f"Помилка виходу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка сервісу виходу"
        )


@router.post("/refresh", response_model=LoginResponse)
@log_execution
@handle_exceptions
def refresh_token(
        request: RefreshTokenRequest,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Оновити токен доступу за допомогою токена оновлення
    """
    try:
        result = auth_service.refresh_token(request.refresh_token)
        return LoginResponse(**result)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Помилка оновлення токена: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка сервісу оновлення токена"
        )


@router.get("/me", response_model=UserInfoResponse)
@log_execution
@handle_exceptions
def get_current_user_info(
        current_user: User = Depends(get_current_user_dep),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Отримати інформацію про поточного користувача та його дозволи
    """
    try:
        permissions = auth_service.get_user_permissions(current_user)
        return UserInfoResponse(
            user=current_user,
            permissions=permissions
        )
    except Exception as e:
        logger.error(f"Помилка отримання інформації про користувача: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося отримати інформацію про користувача"
        )


@router.get("/keycloak/login")
@log_execution
@handle_exceptions
def keycloak_login():
    """
    Перенаправлення на сторінку входу Keycloak
    """
    try:
        authorization_url = key.get_authorization_url()
        return RedirectResponse(url=authorization_url)
    except Exception as e:
        logger.error(f"Помилка перенаправлення на вхід Keycloak: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося перенаправити на Keycloak"
        )


@router.post("/keycloak/callback", response_model=LoginResponse)
@log_execution
@handle_exceptions
async def keycloak_callback(
        request: KeycloakCallbackRequest,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Обробка зворотного виклику OAuth Keycloak
    """
    try:
        result = await auth_service.handle_keycloak_callback(request.code, request.state)
        return LoginResponse(**result)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Помилка зворотного виклику Keycloak: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка аутентифікації Keycloak"
        )


@router.get("/keycloak/logout")
@log_execution
@handle_exceptions
def keycloak_logout(
        current_user: User = Depends(get_current_user_dep)
):
    """
    Перенаправлення на сторінку виходу Keycloak
    """
    try:
        logout_url = key.get_logout_url()
        return RedirectResponse(url=logout_url)
    except Exception as e:
        logger.error(f"Помилка перенаправлення на вихід Keycloak: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося перенаправити на вихід Keycloak"
        )


@router.post("/validate-token")
@log_execution
@handle_exceptions
def validate_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Валідація JWT токена
    """
    try:
        token = credentials.credentials
        is_valid = auth_service.validate_token(token)
        if is_valid:
            user = auth_service.get_current_user(token)
            return {
                "valid": True,
                "user": user.dict() if user else None
            }
        else:
            return {"valid": False}
    except Exception as e:
        logger.error(f"Помилка валідації токена: {str(e)}")
        return {"valid": False}


@router.post("/change-user-status")
@log_execution
@handle_exceptions
def change_user_status(
        user_id: int,
        is_active: bool,
        current_user: User = Depends(get_current_user_dep),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Змінити статус активності користувача (тільки для адміністратора)
    """
    try:
        # Перевірка, чи поточний користувач є адміністратором
        if current_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Тільки адміністратори можуть змінювати статус користувачів"
            )

        result = auth_service.change_user_status(user_id, is_active)
        if result:
            return {"message": "Статус користувача успішно змінено"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Користувача не знайдено"
            )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Помилка зміни статусу користувача: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося змінити статус користувача"
        )


@router.get("/check-permission")
@log_execution
@handle_exceptions
def check_permission(
        permission: str,
        current_user: User = Depends(get_current_user_dep),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Перевірити, чи має поточний користувач певний дозвіл
    """
    try:
        has_permission = auth_service.check_permission(current_user, permission)
        return {
            "user_id": current_user.id,
            "permission": permission,
            "has_permission": has_permission
        }
    except Exception as e:
        logger.error(f"Помилка перевірки дозволу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося перевірити дозвіл"
        )


# Ендпоінт для перевірки стану
@router.get("/health")
def health_check():
    """
    Перевірка стану сервісу аутентифікації
    """
    return {"status": "працює", "service": "auth"}