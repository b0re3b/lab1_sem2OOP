import jwt
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from functools import wraps
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import time
from urllib.parse import urljoin

# Налаштування логування
logger = logging.getLogger(__name__)

# Security схема для FastAPI
security = HTTPBearer()


class JWTConfig:
    """Конфігурація JWT"""

    def __init__(self):
        # Keycloak налаштування (зазвичай завантажуються з config/keycloak.yaml)
        self.KEYCLOAK_SERVER_URL = "http://localhost:8080"
        self.KEYCLOAK_REALM = "airline-system"
        self.KEYCLOAK_CLIENT_ID = "airline-backend"
        self.KEYCLOAK_CLIENT_SECRET = "client-secret"

        # JWT налаштування
        self.JWT_ALGORITHM = "RS256"
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

        # Внутрішні JWT налаштування (для власних токенів)
        self.INTERNAL_JWT_SECRET_KEY = "internal-secret-key"
        self.INTERNAL_JWT_ALGORITHM = "HS256"


class JWTManager:
    """Менеджер для роботи з JWT токенами та Keycloak"""

    def __init__(self, config: JWTConfig = None):
        self.config = config or JWTConfig()
        self._public_key = None
        self._public_key_cache_time = 0
        self._public_key_cache_duration = 3600  # 1 година

    def _get_keycloak_public_key(self) -> str:
        """Отримання публічного ключа Keycloak з кешуванням"""
        current_time = time.time()

        # Перевірка кешу
        if (self._public_key and
                current_time - self._public_key_cache_time < self._public_key_cache_duration):
            return self._public_key

        try:
            # URL для отримання публічного ключа Keycloak
            certs_url = urljoin(
                self.config.KEYCLOAK_SERVER_URL,
                f"/auth/realms/{self.config.KEYCLOAK_REALM}/protocol/openid_connect/certs"
            )

            response = requests.get(certs_url, timeout=10)
            response.raise_for_status()

            keys_data = response.json()

            # Знаходимо ключ для підпису (використовується для RS256)
            for key in keys_data.get('keys', []):
                if key.get('use') == 'sig' and key.get('alg') == 'RS256':
                    # Конвертуємо JWK в PEM формат
                    public_key_pem = self._jwk_to_pem(key)

                    # Кешуємо ключ
                    self._public_key = public_key_pem
                    self._public_key_cache_time = current_time

                    return public_key_pem

            raise ValueError("Не знайдено відповідний ключ для підпису")

        except Exception as e:
            logger.error(f"Помилка отримання публічного ключа Keycloak: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Сервіс автентифікації недоступний"
            )

    def _jwk_to_pem(self, jwk: Dict) -> str:
        """Конвертація JWK в PEM формат"""
        try:
            from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
            from cryptography.hazmat.primitives import serialization
            import base64

            # Декодуємо компоненти RSA ключа
            n = int.from_bytes(
                base64.urlsafe_b64decode(jwk['n'] + '=='),
                byteorder='big'
            )
            e = int.from_bytes(
                base64.urlsafe_b64decode(jwk['e'] + '=='),
                byteorder='big'
            )

            # Створюємо публічний ключ
            public_numbers = RSAPublicNumbers(e, n)
            public_key = public_numbers.public_key()

            # Конвертуємо в PEM
            pem = public_key.serialize(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            return pem.decode('utf-8')

        except Exception as e:
            logger.error(f"Помилка конвертації JWK в PEM: {e}")
            raise ValueError("Неможливо конвертувати ключ")

    def verify_keycloak_token(self, token: str) -> Dict[str, Any]:
        """Верифікація Keycloak JWT токена"""
        try:
            # Отримуємо публічний ключ
            public_key = self._get_keycloak_public_key()

            # Декодуємо та верифікуємо токен
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=[self.config.JWT_ALGORITHM],
                audience=self.config.KEYCLOAK_CLIENT_ID,
                options={"verify_exp": True}
            )

            return decoded_token

        except jwt.ExpiredSignatureError:
            logger.warning("JWT токен прострочений")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен прострочений"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Недійсний JWT токен: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недійсний токен"
            )
        except Exception as e:
            logger.error(f"Помилка верифікації токена: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Помилка верифікації токена"
            )

    def create_internal_token(self, user_data: Dict[str, Any],
                              expires_delta: Optional[timedelta] = None) -> str:
        """Створення внутрішнього JWT токена"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode = user_data.copy()
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

        encoded_jwt = jwt.encode(
            to_encode,
            self.config.INTERNAL_JWT_SECRET_KEY,
            algorithm=self.config.INTERNAL_JWT_ALGORITHM
        )

        return encoded_jwt

    def verify_internal_token(self, token: str) -> Dict[str, Any]:
        """Верифікація внутрішнього JWT токена"""
        try:
            payload = jwt.decode(
                token,
                self.config.INTERNAL_JWT_SECRET_KEY,
                algorithms=[self.config.INTERNAL_JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен прострочений"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недійсний токен"
            )


# Глобальний екземпляр менеджера
jwt_manager = JWTManager()


def create_access_token(data: Dict[str, Any],
                        expires_delta: Optional[timedelta] = None) -> str:
    """Створення access токена"""
    return jwt_manager.create_internal_token(data, expires_delta)


def verify_token(token: str, keycloak: bool = True) -> Dict[str, Any]:
    """
    Верифікація токена

    Args:
        token: JWT токен
        keycloak: True для Keycloak токенів, False для внутрішніх
    """
    if keycloak:
        return jwt_manager.verify_keycloak_token(token)
    else:
        return jwt_manager.verify_internal_token(token)


def extract_user_roles(token_payload: Dict[str, Any]) -> List[str]:
    """Витягування ролей користувача з токена"""
    roles = []

    # Keycloak зберігає ролі в різних частинах токена
    # Ролі реалму
    realm_access = token_payload.get('realm_access', {})
    realm_roles = realm_access.get('roles', [])
    roles.extend(realm_roles)

    # Ролі клієнта
    resource_access = token_payload.get('resource_access', {})
    client_access = resource_access.get(jwt_manager.config.KEYCLOAK_CLIENT_ID, {})
    client_roles = client_access.get('roles', [])
    roles.extend(client_roles)

    # Фільтруємо системні ролі Keycloak
    filtered_roles = [
        role for role in roles
        if not role.startswith('uma_') and role not in ['offline_access']
    ]

    return filtered_roles


def is_token_expired(token_payload: Dict[str, Any]) -> bool:
    """Перевірка чи токен прострочений"""
    exp_timestamp = token_payload.get('exp')
    if not exp_timestamp:
        return True

    current_timestamp = datetime.now(timezone.utc).timestamp()
    return current_timestamp >= exp_timestamp


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency для отримання поточного користувача з JWT токена
    Використовується в FastAPI endpoints
    """
    try:
        # Витягуємо токен з Authorization header
        token = credentials.credentials

        # Спочатку пробуємо як Keycloak токен
        try:
            payload = verify_token(token, keycloak=True)
        except HTTPException:
            # Якщо не вийшло, пробуємо як внутрішній токен
            payload = verify_token(token, keycloak=False)

        # Витягуємо інформацію про користувача
        user_info = {
            'user_id': payload.get('sub'),
            'username': payload.get('preferred_username') or payload.get('username'),
            'email': payload.get('email'),
            'roles': extract_user_roles(payload),
            'token_payload': payload
        }

        return user_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка отримання поточного користувача: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не вдалося автентифікувати користувача"
        )


def require_roles(required_roles: List[str]):
    """
    Декоратор для перевірки ролей користувача

    Usage:
        @require_roles(['admin', 'dispatcher'])
        def some_endpoint(current_user: dict = Depends(get_current_user)):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Отримуємо current_user з kwargs (має бути передано через Depends)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Немає доступу до ресурсу"
                )

            user_roles = current_user.get('roles', [])

            # Перевіряємо чи є хоча б одна з необхідних ролей
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Необхідні ролі: {', '.join(required_roles)}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_admin(func):
    """Декоратор для перевірки ролі адміністратора"""
    return require_roles(['admin'])(func)


def require_dispatcher(func):
    """Декоратор для перевірки ролі диспетчера"""
    return require_roles(['dispatcher'])(func)


# Utility функції для роботи з токенами
def decode_token_without_verification(token: str) -> Dict[str, Any]:
    """Декодування токена без верифікації (для дебагу)"""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        logger.error(f"Помилка декодування токена: {e}")
        return {}


def get_token_claims(token: str) -> Dict[str, Any]:
    """Отримання claims з токена без повної верифікації"""
    return decode_token_without_verification(token)


def refresh_token_if_needed(token: str, threshold_minutes: int = 5) -> Optional[str]:
    """
    Оновлення токена, якщо він скоро прострочиться

    Args:
        token: Поточний токен
        threshold_minutes: За скільки хвилин до закінчення оновлювати

    Returns:
        Новий токен або None, якщо оновлення не потрібне
    """
    try:
        payload = decode_token_without_verification(token)
        exp_timestamp = payload.get('exp')

        if not exp_timestamp:
            return None

        current_time = datetime.now(timezone.utc).timestamp()
        time_until_expiry = exp_timestamp - current_time

        # Якщо токен закінчиться менш ніж через threshold_minutes хвилин
        if time_until_expiry < (threshold_minutes * 60):
            # Тут можна реалізувати логіку оновлення токена через Keycloak
            # Поки що повертаємо None
            logger.info("Токен потребує оновлення")
            return None

        return None

    except Exception as e:
        logger.error(f"Помилка перевірки необхідності оновлення токена: {e}")
        return None