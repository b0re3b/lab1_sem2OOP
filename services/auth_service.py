from typing import Optional, Dict, Any
from datetime import datetime
import logging

from models.user import User, UserRole
from config.keycloak import KeycloakClient
from repositories.user_repository import UserRepository
from utils.jwt_utils import JWTManager, KeycloakJWTManager
from utils.validators import UserValidator, ValidationError
from config.logging_config import log_auth_event, log_error, log_info


class AuthenticationError(Exception):
    """Виняток для помилок автентифікації"""
    pass


class AuthorizationError(Exception):
    """Виняток для помилок авторизації"""
    pass


class AuthService:
    def __init__(self,
                 keycloak_client: KeycloakClient,
                 user_repository: UserRepository,
                 jwt_manager: JWTManager,
                 keycloak_jwt_manager: KeycloakJWTManager):
        self.keycloak_client = keycloak_client
        self.user_repository = user_repository
        self.jwt_manager = jwt_manager
        self.keycloak_jwt_manager = keycloak_jwt_manager
        self.logger = logging.getLogger(__name__)

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Авторизація користувача через Keycloak

        Args:
            username: Ім'я користувача
            password: Пароль

        Returns:
            Dict з токенами та інформацією про користувача

        Raises:
            AuthenticationError: Якщо автентифікація не вдалася
        """
        try:
            log_auth_event(f"Спроба входу користувача: {username}")

            # Отримуємо токени від Keycloak
            token_response = self.keycloak_client.get_admin_token()
            if not token_response:
                raise AuthenticationError("Не вдалося отримати токен від Keycloak")

            # Отримуємо інформацію про користувача від Keycloak
            keycloak_user_info = self.keycloak_client.get_user_info(token_response['access_token'])
            if not keycloak_user_info:
                raise AuthenticationError("Не вдалося отримати інформацію про користувача")

            # Синхронізуємо або створюємо користувача в локальній БД
            user = self._sync_user_with_keycloak(keycloak_user_info)

            if not user.is_active:
                log_auth_event(f"Спроба входу деактивованого користувача: {username}")
                raise AuthenticationError("Обліковий запис деактивовано")

            # Створюємо локальні JWT токени
            access_token = self.jwt_manager.create_access_token(user.id, user.role.value)
            refresh_token = self.jwt_manager.create_refresh_token(user.id)

            log_auth_event(f"Успішний вхід користувача: {username}")

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'keycloak_token': token_response['access_token'],
                'user': user.to_dict(),
                'expires_in': self.jwt_manager.get_token_expiry(access_token)
            }

        except Exception as e:
            log_error(f"Помилка при авторизації користувача {username}: {str(e)}")
            raise AuthenticationError(f"Помилка авторизації: {str(e)}")

    def logout(self, refresh_token: str, keycloak_token: Optional[str] = None) -> bool:
        """
        Вихід користувача із системи

        Args:
            refresh_token: Refresh токен для відкликання
            keycloak_token: Токен Keycloak для відкликання

        Returns:
            True якщо вихід успішний
        """
        try:
            user_info = self.jwt_manager.get_user_from_token(refresh_token)
            username = user_info.get('username', 'Unknown') if user_info else 'Unknown'

            log_auth_event(f"Вихід користувача: {username}")

            # Відкликаємо токен в Keycloak якщо є
            if keycloak_token:
                self.keycloak_client.logout_user(keycloak_token)

            log_info(f"Успішний вихід користувача: {username}")
            return True

        except Exception as e:
            log_error(f"Помилка при виході користувача: {str(e)}")
            return False

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Оновлення access токена за допомогою refresh токена

        Args:
            refresh_token: Refresh токен

        Returns:
            Dict з новими токенами

        Raises:
            AuthenticationError: Якщо токен недійсний
        """
        try:
            if not self.jwt_manager.is_token_valid(refresh_token):
                raise AuthenticationError("Недійсний refresh токен")

            user_info = self.jwt_manager.get_user_from_token(refresh_token)
            if not user_info:
                raise AuthenticationError("Не вдалося отримати інформацію з токена")

            user = self.user_repository.find_by_id(user_info['user_id'])
            if not user or not user.is_active:
                raise AuthenticationError("Користувач не знайдений або деактивований")

            new_access_token = self.jwt_manager.create_access_token(user.id, user.role.value)

            log_auth_event(f"Оновлення токена для користувача: {user.username}")

            return {
                'access_token': new_access_token,
                'expires_in': self.jwt_manager.get_token_expiry(new_access_token)
            }

        except Exception as e:
            log_error(f"Помилка при оновленні токена: {str(e)}")
            raise AuthenticationError(f"Помилка оновлення токена: {str(e)}")

    def validate_token(self, token: str) -> Optional[User]:
        """
        Валідація JWT токена та отримання інформації про користувача

        Args:
            token: JWT токен

        Returns:
            User об'єкт або None якщо токен недійсний
        """
        try:
            if not self.jwt_manager.is_token_valid(token):
                return None

            user_info = self.jwt_manager.get_user_from_token(token)
            if not user_info:
                return None

            user = self.user_repository.find_by_id(user_info['user_id'])
            if not user or not user.is_active:
                return None

            return user

        except Exception as e:
            log_error(f"Помилка валідації токена: {str(e)}")
            return None

    def validate_keycloak_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Валідація Keycloak токена

        Args:
            token: Keycloak JWT токен

        Returns:
            Декодована інформація з токена або None
        """
        try:
            return self.keycloak_jwt_manager.decode_keycloak_token(token)
        except Exception as e:
            log_error(f"Помилка валідації Keycloak токена: {str(e)}")
            return None

    def check_permission(self, user: User, required_role: UserRole) -> bool:
        """
        Перевірка прав доступу користувача

        Args:
            user: Користувач
            required_role: Необхідна роль

        Returns:
            True якщо користувач має необхідні права
        """
        if not user or not user.is_active:
            return False

        # Адміністратор має доступ до всього
        if user.is_admin():
            return True

        # Перевіряємо відповідність ролі
        return user.role == required_role

    def create_user_from_keycloak(self, keycloak_user_data: Dict[str, Any]) -> User:
        """
        Створення користувача на основі даних з Keycloak

        Args:
            keycloak_user_data: Дані користувача з Keycloak

        Returns:
            Створений користувач

        Raises:
            ValidationError: Якщо дані некоректні
        """
        try:
            # Валідуємо дані
            UserValidator.validate_keycloak_id(keycloak_user_data.get('sub', ''))
            UserValidator.validate_username(keycloak_user_data.get('preferred_username', ''))
            UserValidator.validate_email(keycloak_user_data.get('email', ''))

            # Визначаємо роль на основі Keycloak ролей
            role = self._extract_role_from_keycloak(keycloak_user_data)

            user_data = {
                'keycloak_id': keycloak_user_data['sub'],
                'username': keycloak_user_data['preferred_username'],
                'email': keycloak_user_data['email'],
                'first_name': keycloak_user_data.get('given_name', ''),
                'last_name': keycloak_user_data.get('family_name', ''),
                'role': role
            }

            UserValidator.validate_user_data(user_data)

            user = User.from_dict(user_data)
            created_user = self.user_repository.create_user(user)

            log_info(f"Створено нового користувача з Keycloak: {user.username}")

            return created_user

        except ValidationError as e:
            log_error(f"Помилка валідації при створенні користувача: {str(e)}")
            raise
        except Exception as e:
            log_error(f"Помилка при створенні користувача з Keycloak: {str(e)}")
            raise

    def _sync_user_with_keycloak(self, keycloak_user_info: Dict[str, Any]) -> User:
        """
        Синхронізація користувача з Keycloak або створення нового

        Args:
            keycloak_user_info: Інформація про користувача з Keycloak

        Returns:
            Синхронізований користувач
        """
        keycloak_id = keycloak_user_info.get('sub')
        if not keycloak_id:
            raise AuthenticationError("Відсутній Keycloak ID")

        # Шукаємо існуючого користувача
        user = self.user_repository.find_by_keycloak_id(keycloak_id)

        if user:
            # Оновлюємо існуючого користувача
            user.email = keycloak_user_info.get('email', user.email)
            user.first_name = keycloak_user_info.get('given_name', user.first_name)
            user.last_name = keycloak_user_info.get('family_name', user.last_name)

            # Оновлюємо роль якщо змінилася
            new_role = self._extract_role_from_keycloak(keycloak_user_info)
            if new_role != user.role:
                user.role = new_role
                log_info(f"Оновлено роль користувача {user.username}: {new_role.value}")

            self.user_repository.update_user(user)
            return user
        else:
            # Створюємо нового користувача
            return self.create_user_from_keycloak(keycloak_user_info)

    def _extract_role_from_keycloak(self, keycloak_data: Dict[str, Any]) -> UserRole:
        """
        Витягує роль користувача з даних Keycloak

        Args:
            keycloak_data: Дані з Keycloak

        Returns:
            UserRole
        """
        # Перевіряємо ролі в різних можливих місцях
        roles = []

        # Ролі можуть бути в realm_access
        if 'realm_access' in keycloak_data and 'roles' in keycloak_data['realm_access']:
            roles.extend(keycloak_data['realm_access']['roles'])

        # Ролі можуть бути в resource_access
        if 'resource_access' in keycloak_data:
            for client, access in keycloak_data['resource_access'].items():
                if 'roles' in access:
                    roles.extend(access['roles'])

        # Визначаємо роль за пріоритетом
        if 'ADMIN' in roles or 'admin' in roles:
            return UserRole.ADMIN
        elif 'DISPATCHER' in roles or 'dispatcher' in roles:
            return UserRole.DISPATCHER
        else:
            # За замовчуванням диспетчер
            return UserRole.DISPATCHER

    def get_current_user(self, token: str) -> Optional[User]:
        """
        Отримання поточного користувача за токеном

        Args:
            token: JWT токен

        Returns:
            User об'єкт або None
        """
        return self.validate_token(token)

    def change_user_status(self, user_id: int, is_active: bool, admin_user: User) -> bool:
        """
        Зміна статусу користувача (активний/неактивний)

        Args:
            user_id: ID користувача
            is_active: Новий статус
            admin_user: Адміністратор що виконує операцію

        Returns:
            True якщо операція успішна

        Raises:
            AuthorizationError: Якщо немає прав доступу
        """
        if not admin_user.is_admin():
            raise AuthorizationError("Тільки адміністратор може змінювати статус користувачів")

        try:
            user = self.user_repository.find_by_id(user_id)
            if not user:
                log_error(f"Користувач з ID {user_id} не знайдений")
                return False

            if is_active:
                user.activate()
            else:
                user.deactivate()

            self.user_repository.update_user(user)

            status_text = "активовано" if is_active else "деактивовано"
            log_auth_event(f"Користувача {user.username} {status_text} адміністратором {admin_user.username}")

            return True

        except Exception as e:
            log_error(f"Помилка при зміні статусу користувача: {str(e)}")
            return False