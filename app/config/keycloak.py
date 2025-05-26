import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class KeycloakConfig:
    """Конфігурація підключення до Keycloak"""

    def __init__(self):
        self.server_url = os.getenv('KEYCLOAK_SERVER_URL', 'http://localhost:8080')
        self.realm = os.getenv('KEYCLOAK_REALM', 'airline-system')
        self.client_id = os.getenv('KEYCLOAK_CLIENT_ID', 'airline-app')
        self.client_secret = os.getenv('KEYCLOAK_CLIENT_SECRET', '')
        self.admin_username = os.getenv('KEYCLOAK_ADMIN_USERNAME', 'admin')
        self.admin_password = os.getenv('KEYCLOAK_ADMIN_PASSWORD', 'admin')

        # URLs для різних ендпоінтів
        self.auth_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/auth"
        self.token_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"
        self.userinfo_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/userinfo"
        self.logout_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/logout"
        self.certs_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/certs"
        self.admin_url = f"{self.server_url}/admin/realms/{self.realm}"

        # Налаштування HTTP клієнта
        self.session = self._create_http_session()

    def _create_http_session(self) -> requests.Session:
        """Створює HTTP сесію з retry логікою"""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def get_well_known_config(self) -> Dict[str, Any]:
        """Отримує конфігурацію OpenID Connect"""
        well_known_url = f"{self.server_url}/realms/{self.realm}/.well-known/openid_configuration"
        try:
            response = self.session.get(well_known_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Помилка отримання конфігурації Keycloak: {e}")
            raise KeycloakConnectionError(f"Не вдалося підключитися до Keycloak: {e}")


class KeycloakClient:
    """Клієнт для роботи з Keycloak API"""

    def __init__(self, config: KeycloakConfig):
        self.config = config
        self._admin_token = None
        self._admin_token_expires = 0

    def get_admin_token(self) -> str:
        """Отримує токен адміністратора для роботи з Admin API"""
        import time

        # Перевіряємо чи токен ще валідний
        if self._admin_token and time.time() < self._admin_token_expires:
            return self._admin_token

        data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': self.config.admin_username,
            'password': self.config.admin_password,
        }

        try:
            response = self.config.session.post(
                f"{self.config.server_url}/realms/master/protocol/openid-connect/token",
                data=data,
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()
            self._admin_token = token_data['access_token']
            self._admin_token_expires = time.time() + token_data.get('expires_in', 300) - 30

            return self._admin_token

        except requests.RequestException as e:
            logger.error(f"Помилка отримання токена адміністратора: {e}")
            raise KeycloakAuthError(f"Не вдалося отримати токен адміністратора: {e}")

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Обмінює authorization code на токени"""
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
        }

        try:
            response = self.config.session.post(self.config.token_url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Помилка обміну коду на токен: {e}")
            raise KeycloakAuthError(f"Не вдалося обміняти код на токен: {e}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Оновлює токен доступу"""
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'refresh_token': refresh_token,
        }

        try:
            response = self.config.session.post(self.config.token_url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Помилка оновлення токена: {e}")
            raise KeycloakAuthError(f"Не вдалося оновити токен: {e}")

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Отримує інформацію про користувача за токеном"""
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            response = self.config.session.get(
                self.config.userinfo_url,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Помилка отримання інформації про користувача: {e}")
            raise KeycloakAuthError(f"Не вдалося отримати інформацію про користувача: {e}")

    def logout_user(self, refresh_token: str) -> bool:
        """Виходить користувача з системи"""
        data = {
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'refresh_token': refresh_token,
        }

        try:
            response = self.config.session.post(self.config.logout_url, data=data, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Помилка виходу з системи: {e}")
            return False

    def get_user_by_keycloak_id(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Отримує користувача з Keycloak за ID"""
        admin_token = self.get_admin_token()
        headers = {'Authorization': f'Bearer {admin_token}'}

        try:
            response = self.config.session.get(
                f"{self.config.admin_url}/users/{keycloak_id}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if e.response and e.response.status_code == 404:
                return None
            logger.error(f"Помилка отримання користувача: {e}")
            raise KeycloakAPIError(f"Не вдалося отримати користувача: {e}")

    def create_user(self, user_data: Dict[str, Any]) -> str:
        """Створює нового користувача в Keycloak"""
        admin_token = self.get_admin_token()
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }

        try:
            response = self.config.session.post(
                f"{self.config.admin_url}/users",
                json=user_data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            # Keycloak повертає Location header з ID нового користувача
            location = response.headers.get('Location', '')
            user_id = location.split('/')[-1] if location else None

            if not user_id:
                raise KeycloakAPIError("Не вдалося отримати ID створеного користувача")

            return user_id

        except requests.RequestException as e:
            logger.error(f"Помилка створення користувача: {e}")
            raise KeycloakAPIError(f"Не вдалося створити користувача: {e}")

    def update_user(self, keycloak_id: str, user_data: Dict[str, Any]) -> bool:
        """Оновлює користувача в Keycloak"""
        admin_token = self.get_admin_token()
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }

        try:
            response = self.config.session.put(
                f"{self.config.admin_url}/users/{keycloak_id}",
                json=user_data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Помилка оновлення користувача: {e}")
            raise KeycloakAPIError(f"Не вдалося оновити користувача: {e}")

    def get_public_keys(self) -> Dict[str, Any]:
        """Отримує публічні ключі для валідації JWT"""
        try:
            response = self.config.session.get(self.config.certs_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Помилка отримання публічних ключів: {e}")
            raise KeycloakConnectionError(f"Не вдалося отримати публічні ключі: {e}")


class KeycloakOAuthConfig:
    """Конфігурація OAuth2 параметрів"""

    def __init__(self, config: KeycloakConfig):
        self.config = config

    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Генерує URL для авторизації"""
        params = {
            'client_id': self.config.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid profile email',
        }

        if state:
            params['state'] = state

        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.auth_url}?{param_string}"

    def get_logout_url(self, redirect_uri: str = None) -> str:
        """Генерує URL для виходу"""
        params = {'client_id': self.config.client_id}

        if redirect_uri:
            params['post_logout_redirect_uri'] = redirect_uri

        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.logout_url}?{param_string}"


# Винятки для роботи з Keycloak
class KeycloakError(Exception):
    """Базовий виняток для Keycloak"""
    pass


class KeycloakConnectionError(KeycloakError):
    """Помилка підключення до Keycloak"""
    pass


class KeycloakAuthError(KeycloakError):
    """Помилка аутентифікації в Keycloak"""
    pass


class KeycloakAPIError(KeycloakError):
    """Помилка API Keycloak"""
    pass


# Ініціалізація глобальних об'єктів
keycloak_config = KeycloakConfig()
keycloak_client = KeycloakClient(keycloak_config)
oauth_config = KeycloakOAuthConfig(keycloak_config)


def get_keycloak_client() -> KeycloakClient:
    """Повертає екземпляр Keycloak клієнта"""
    return keycloak_client


def get_oauth_config() -> KeycloakOAuthConfig:
    """Повертає конфігурацію OAuth"""
    return oauth_config


def health_check() -> bool:
    """Перевіряє доступність Keycloak сервера"""
    try:
        keycloak_config.get_well_known_config()
        return True
    except KeycloakConnectionError:
        return False


# Приклад використання ролей та груп
ROLE_MAPPINGS = {
    'ADMIN': ['admin', 'user'],
    'DISPATCHER': ['dispatcher', 'user'],
}

GROUP_MAPPINGS = {
    'ADMIN': '/airline-admins',
    'DISPATCHER': '/airline-dispatchers',
}


def map_keycloak_roles_to_app_roles(keycloak_user: Dict[str, Any]) -> list:
    """Мапить ролі Keycloak на ролі додатку"""
    app_roles = []

    # Отримуємо ролі з realm_access
    realm_roles = keycloak_user.get('realm_access', {}).get('roles', [])

    for role in realm_roles:
        if role in ['admin', 'administrator']:
            app_roles.append('ADMIN')
        elif role in ['dispatcher']:
            app_roles.append('DISPATCHER')

    return list(set(app_roles))  # Унікальні ролі