import jwt
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from functools import wraps
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import base64
import hashlib
import secrets


class JWTError(Exception):
    """Кастомний клас для помилок JWT"""
    pass


class TokenExpiredError(JWTError):
    """Помилка коли токен прострочений"""
    pass


class InvalidTokenError(JWTError):
    """Помилка коли токен недійсний"""
    pass


class JWTConfig:
    """Конфігурація для JWT"""

    def __init__(self):
        # Ці значення зазвичай беруться з config/settings.py
        self.SECRET_KEY = "your-secret-key-should-be-from-config"
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7
        self.ISSUER = "airline-system"
        self.AUDIENCE = "airline-app"


class JWTManager:
    """Менеджер для роботи з JWT токенами"""

    def __init__(self, config: JWTConfig = None):
        self.config = config or JWTConfig()
        self._public_keys_cache = {}
        self._cache_expiry = None

    def create_access_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Створення access токена"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user_data.get("id")),  # Subject (user ID)
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "role": user_data.get("role"),
            "keycloak_id": user_data.get("keycloak_id"),
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "iss": self.config.ISSUER,  # Issuer
            "aud": self.config.AUDIENCE,  # Audience
            "type": "access"
        }

        try:
            return jwt.encode(payload, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
        except Exception as e:
            raise JWTError(f"Помилка створення токена: {str(e)}")

    def create_refresh_token(self, user_id: Union[str, int]) -> str:
        """Створення refresh токена"""
        expire = datetime.utcnow() + timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": self.config.ISSUER,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # JWT ID для унікальності
        }

        try:
            return jwt.encode(payload, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
        except Exception as e:
            raise JWTError(f"Помилка створення refresh токена: {str(e)}")

    def decode_token(self, token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """Декодування та валідація токена"""
        try:
            # Спочатку декодуємо без верифікації щоб отримати header
            unverified_header = jwt.get_unverified_header(token)

            options = {
                "verify_signature": True,
                "verify_exp": verify_exp,
                "verify_iat": True,
                "verify_iss": True,
                "verify_aud": True
            }

            payload = jwt.decode(
                token,
                self.config.SECRET_KEY,
                algorithms=[self.config.ALGORITHM],
                issuer=self.config.ISSUER,
                audience=self.config.AUDIENCE,
                options=options
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Токен прострочений")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Недійсний токен: {str(e)}")
        except Exception as e:
            raise JWTError(f"Помилка декодування токена: {str(e)}")

    def refresh_access_token(self, refresh_token: str, user_data: Dict[str, Any]) -> str:
        """Оновлення access токена за допомогою refresh токена"""
        try:
            # Перевіряємо refresh токен
            payload = self.decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise InvalidTokenError("Це не refresh токен")

            # Створюємо новий access токен
            return self.create_access_token(user_data)

        except (TokenExpiredError, InvalidTokenError):
            raise
        except Exception as e:
            raise JWTError(f"Помилка оновлення токена: {str(e)}")

    def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """Отримання даних користувача з токена"""
        payload = self.decode_token(token)

        return {
            "id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "keycloak_id": payload.get("keycloak_id")
        }

    def is_token_valid(self, token: str) -> bool:
        """Перевірка чи токен дійсний"""
        try:
            self.decode_token(token)
            return True
        except (TokenExpiredError, InvalidTokenError, JWTError):
            return False

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Отримання часу закінчення дії токена"""
        try:
            payload = self.decode_token(token, verify_exp=False)
            exp = payload.get("exp")
            if exp:
                return datetime.utcfromtimestamp(exp)
            return None
        except Exception:
            return None


class KeycloakJWTManager:
    """Менеджер для роботи з JWT токенами від Keycloak"""

    def __init__(self, keycloak_config: Dict[str, Any]):
        self.keycloak_config = keycloak_config
        self.server_url = keycloak_config.get("server_url")
        self.realm = keycloak_config.get("realm")
        self.client_id = keycloak_config.get("client_id")
        self._public_keys = {}
        self._keys_last_updated = None

    def get_public_keys(self) -> Dict[str, Any]:
        """Отримання публічних ключів від Keycloak"""
        # Кешуємо ключі на 1 годину
        if (self._keys_last_updated and
                datetime.now() - self._keys_last_updated < timedelta(hours=1)):
            return self._public_keys

        try:
            certs_url = f"{self.server_url}/realms/{self.realm}/protocol/openid_connect/certs"
            response = requests.get(certs_url, timeout=10)
            response.raise_for_status()

            keys_data = response.json()
            self._public_keys = {}

            for key in keys_data.get("keys", []):
                kid = key.get("kid")
                if kid:
                    self._public_keys[kid] = key

            self._keys_last_updated = datetime.now()
            return self._public_keys

        except Exception as e:
            raise JWTError(f"Помилка отримання публічних ключів Keycloak: {str(e)}")

    def _jwk_to_public_key(self, jwk_data: Dict[str, Any]):
        """Конвертація JWK в публічний ключ"""
        try:
            n = base64.urlsafe_b64decode(jwk_data['n'] + '==')
            e = base64.urlsafe_b64decode(jwk_data['e'] + '==')

            # Створюємо RSA публічний ключ
            from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers, RSAPublicKey

            public_numbers = RSAPublicNumbers(
                int.from_bytes(e, 'big'),
                int.from_bytes(n, 'big')
            )

            return public_numbers.public_key()

        except Exception as e:
            raise JWTError(f"Помилка конвертації JWK: {str(e)}")

    def decode_keycloak_token(self, token: str) -> Dict[str, Any]:
        """Декодування токена від Keycloak"""
        try:
            # Отримуємо header токена
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise InvalidTokenError("Відсутній kid в header токена")

            # Отримуємо публічні ключі
            public_keys = self.get_public_keys()

            if kid not in public_keys:
                raise InvalidTokenError(f"Невідомий kid: {kid}")

            # Конвертуємо JWK в публічний ключ
            key_data = public_keys[kid]
            public_key = self._jwk_to_public_key(key_data)

            # Декодуємо токен
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.client_id,
                options={"verify_exp": True}
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Keycloak токен прострочений")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Недійсний Keycloak токен: {str(e)}")
        except Exception as e:
            raise JWTError(f"Помилка декодування Keycloak токена: {str(e)}")

    def get_user_info_from_keycloak_token(self, token: str) -> Dict[str, Any]:
        """Отримання інформації про користувача з Keycloak токена"""
        payload = self.decode_keycloak_token(token)

        return {
            "keycloak_id": payload.get("sub"),
            "username": payload.get("preferred_username"),
            "email": payload.get("email"),
            "first_name": payload.get("given_name"),
            "last_name": payload.get("family_name"),
            "roles": payload.get("realm_access", {}).get("roles", []),
            "client_roles": payload.get("resource_access", {}).get(self.client_id, {}).get("roles", [])
        }


def jwt_required(optional: bool = False):
    """Декоратор для перевірки JWT токена"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, g

            token = None
            auth_header = request.headers.get('Authorization')

            if auth_header:
                try:
                    token = auth_header.split(' ')[1]  # Bearer <token>
                except IndexError:
                    if not optional:
                        return {'error': 'Неправильний формат токена'}, 401

            if not token and not optional:
                return {'error': 'Токен відсутній'}, 401

            if token:
                jwt_manager = JWTManager()
                try:
                    user_data = jwt_manager.get_user_from_token(token)
                    g.current_user = user_data
                except (TokenExpiredError, InvalidTokenError, JWTError) as e:
                    if not optional:
                        return {'error': str(e)}, 401
                    g.current_user = None
            else:
                g.current_user = None

            return func(*args, **kwargs)

        return wrapper

    return decorator


def role_required(required_role: str):
    """Декоратор для перевірки ролі користувача"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import g

            if not hasattr(g, 'current_user') or not g.current_user:
                return {'error': 'Потрібна авторизація'}, 401

            user_role = g.current_user.get('role')
            if user_role != required_role:
                return {'error': f'Потрібна роль: {required_role}'}, 403

            return func(*args, **kwargs)

        return wrapper

    return decorator

