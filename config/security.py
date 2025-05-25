import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from keycloak import KeycloakOpenID, KeycloakAdmin, KeycloakUMA
from pydantic import BaseModel

from .settings import get_settings

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration class."""

    def __init__(self, settings: Optional[object] = None):
        self.settings = settings or get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._keycloak_openid = None
        self._keycloak_admin = None
        self._keycloak_uma = None

    @property
    def keycloak_openid(self) -> KeycloakOpenID:
        """Get Keycloak OpenID client."""
        if self._keycloak_openid is None:
            self._keycloak_openid = KeycloakOpenID(
                server_url=self.settings.keycloak_server_url,
                client_id=self.settings.keycloak_client_id,
                realm_name=self.settings.keycloak_realm,
                client_secret_key=self.settings.keycloak_client_secret,
                verify=True
            )
        return self._keycloak_openid

    @property
    def keycloak_admin(self) -> Optional[KeycloakAdmin]:
        """Get Keycloak Admin client."""
        if (self._keycloak_admin is None and
                self.settings.keycloak_admin_username and
                self.settings.keycloak_admin_password):
            self._keycloak_admin = KeycloakAdmin(
                server_url=self.settings.keycloak_server_url,
                username=self.settings.keycloak_admin_username,
                password=self.settings.keycloak_admin_password,
                realm_name=self.settings.keycloak_realm,
                verify=True
            )
        return self._keycloak_admin

    @property
    def keycloak_uma(self) -> KeycloakUMA:
        """Get Keycloak UMA client."""
        if self._keycloak_uma is None:
            self._keycloak_uma = KeycloakUMA(
                connection=self.keycloak_openid.connection
            )
        return self._keycloak_uma

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Get password hash."""
        return self.pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.access_token_expire_minutes)

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
        )
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.settings.refresh_token_expire_days)

        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
        )
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm]
            )

            # Check token type
            if payload.get("type") != token_type:
                return None

            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp", 0)):
                return None

            return payload

        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None

    def verify_keycloak_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Keycloak token."""
        try:
            # Get token info from Keycloak
            token_info = self.keycloak_openid.introspect(token)

            if not token_info.get("active", False):
                return None

            return token_info

        except Exception as e:
            logger.warning(f"Keycloak token verification failed: {e}")
            return None

    def get_user_info_from_keycloak(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user info from Keycloak token."""
        try:
            user_info = self.keycloak_openid.userinfo(token)
            return user_info
        except Exception as e:
            logger.warning(f"Failed to get user info from Keycloak: {e}")
            return None

    def exchange_keycloak_token(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Exchange username/password for Keycloak tokens."""
        try:
            token_response = self.keycloak_openid.token(username, password)
            return token_response
        except Exception as e:
            logger.warning(f"Keycloak token exchange failed: {e}")
            return None

    def refresh_keycloak_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh Keycloak token."""
        try:
            token_response = self.keycloak_openid.refresh_token(refresh_token)
            return token_response
        except Exception as e:
            logger.warning(f"Keycloak token refresh failed: {e}")
            return None

    def logout_keycloak(self, refresh_token: str) -> bool:
        """Logout from Keycloak."""
        try:
            self.keycloak_openid.logout(refresh_token)
            return True
        except Exception as e:
            logger.warning(f"Keycloak logout failed: {e}")
            return False

    def check_user_permissions(self, token: str, resource: str, scope: str) -> bool:
        """Check user permissions using Keycloak UMA."""
        try:
            # This would implement UMA-based authorization
            # For now, we'll implement basic role-based checks
            token_info = self.verify_keycloak_token(token)
            if not token_info:
                return False

            roles = token_info.get("realm_access", {}).get("roles", [])

            # Define permission mappings
            permission_map = {
                "flights": {
                    "create": ["ADMIN"],
                    "read": ["ADMIN", "DISPATCHER"],
                    "update": ["ADMIN"],
                    "delete": ["ADMIN"]
                },
                "crew": {
                    "create": ["ADMIN", "DISPATCHER"],
                    "read": ["ADMIN", "DISPATCHER"],
                    "update": ["ADMIN", "DISPATCHER"],
                    "delete": ["ADMIN"]
                },
                "assignments": {
                    "create": ["DISPATCHER"],
                    "read": ["ADMIN", "DISPATCHER"],
                    "update": ["DISPATCHER"],
                    "delete": ["ADMIN", "DISPATCHER"]
                }
            }

            allowed_roles = permission_map.get(resource, {}).get(scope, [])
            return any(role in roles for role in allowed_roles)

        except Exception as e:
            logger.warning(f"Permission check failed: {e}")
            return False


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    roles: List[str] = []
    keycloak_id: Optional[str] = None


@lru_cache()
def get_security_config() -> SecurityConfig:
    """Get cached security configuration."""
    return SecurityConfig()