from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException, status
import logging
from models.user import User, UserRole
from repositories.user_repository import UserRepository
from utils.jwt_utils import JWTConfig, JWTManager
from utils.decorators import log_execution_time
from config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class AuthService:
    """
    Сервіс для роботи з автентифікацією та авторизацією
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.keycloak_base_url = settings.keycloak_url
        self.keycloak_realm = settings.keycloak_realm
        self.keycloak_client_id = settings.keycloak_client_id
        self.keycloak_client_secret = settings.keycloak_client_secret
        self.jwt_config = JWTConfig()
        self.jwt_manager = JWTManager(self.jwt_config)
        self.admin_token = None
        self.admin_token_expires_at = None

    @log_execution_time
    def authenticate_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Автентифікація користувача через Keycloak token

        Args:
            token: JWT токен від Keycloak

        Returns:
            Інформація про користувача або None
        """
        try:
            # Верифікація токена через Keycloak
            token_data = self.jwt_manager.verify_keycloak_token(token)
            if not token_data:
                return None

            keycloak_id = token_data.get('sub')
            username = token_data.get('preferred_username')
            email = token_data.get('email')

            if not keycloak_id:
                logger.warning("Token does not contain Keycloak ID")
                return None

            # Пошук або створення користувача в локальній БД
            user =  self._get_or_create_user(
                keycloak_id=keycloak_id,
                username=username,
                email=email,
                token_data=token_data
            )

            if not user or not user.is_active:
                logger.warning(f"User {username} is inactive or not found")
                return None

            # Створення внутрішнього токена
            internal_token_data = {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value,
                'keycloak_id': user.keycloak_id
            }
            internal_token = self.jwt_manager.create_internal_token(
                internal_token_data,
                timedelta(hours=8)
            )


            return {
                'user': user,
                'token': internal_token,
                'expires_at': datetime.utcnow() + timedelta(hours=8)
            }

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None

    @log_execution_time
    def authenticate_with_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Автентифікація користувача через логін/пароль в Keycloak

        Args:
            username: Ім'я користувача
            password: Пароль

        Returns:
            Інформація про користувача та токени
        """
        try:
            token_data =  self._authenticate_with_keycloak(username, password)
            if not token_data:
                return None

            access_token = token_data.get('access_token')
            if not access_token:
                return None

            # Використовуємо отриманий токен для автентифікації
            return  self.authenticate_user(access_token)

        except Exception as e:
            logger.error(f"Credential authentication failed: {str(e)}")
            return None

    @log_execution_time
    async def authorize_user(self, user_id: int, required_roles: List[str]) -> bool:
        """
        Авторизація користувача для виконання операції

        Args:
            user_id: ID користувача
            required_roles: Список необхідних ролей

        Returns:
            True якщо користувач має права, False інакше
        """
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user or not user.is_active:
                return False

            # Перевірка ролі користувача
            user_role = user.role.value
            has_permission = user_role in required_roles

            if not has_permission:
                await self._log_business_event(
                    'AUTHORIZATION_DENIED',
                    user_id,
                    {
                        'user_role': user_role,
                        'required_roles': required_roles
                    }
                )

            return has_permission

        except Exception as e:
            logger.error(f"Authorization check failed for user {user_id}: {str(e)}")
            return False

    @log_execution_time
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Оновлення access токена за допомогою refresh токена

        Args:
            refresh_token: Refresh токен

        Returns:
            Нові токени або None
        """
        try:
            async with httpx.AsyncClient() as client:
                token_url = f"{self.keycloak_base_url}/auth/realms/{self.keycloak_realm}/protocol/openid_connect/token"

                data = {
                    'grant_type': 'refresh_token',
                    'client_id': self.keycloak_client_id,
                    'client_secret': self.keycloak_client_secret,
                    'refresh_token': refresh_token
                }

                response = await client.post(token_url, data=data)

                if response.status_code == 200:
                    token_info = response.json()
                    return {
                        'access_token': token_info.get('access_token'),
                        'refresh_token': token_info.get('refresh_token'),
                        'expires_in': token_info.get('expires_in'),
                        'token_type': token_info.get('token_type', 'Bearer')
                    }
                else:
                    logger.warning(f"Token refresh failed: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return None

    @log_execution_time
    async def logout_user(self, user_id: int, refresh_token: str = None) -> bool:
        """
        Вихід користувача з системи

        Args:
            user_id: ID користувача
            refresh_token: Refresh токен для відкликання в Keycloak

        Returns:
            True якщо успішно
        """
        try:
            # Відкликання токена в Keycloak
            if refresh_token:
                await self._revoke_keycloak_token(refresh_token)

            # Логування події
            await self._log_business_event(
                'USER_LOGGED_OUT',
                user_id,
                {'timestamp': datetime.utcnow().isoformat()}
            )

            return True

        except Exception as e:
            logger.error(f"Logout failed for user {user_id}: {str(e)}")
            return False

    @log_execution_time
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Отримання профілю користувача

        Args:
            user_id: ID користувача

        Returns:
            Дані профілю користувача
        """
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return None

            # Додаткова інформація з Keycloak (якщо потрібно)
            keycloak_data = await self._get_keycloak_user_info(user.keycloak_id)

            profile = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'role': user.role.value,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'is_dispatcher': user.is_dispatcher,
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }

            # Додаємо інформацію з Keycloak якщо є
            if keycloak_data:
                profile.update({
                    'keycloak_data': keycloak_data
                })

            return profile

        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {str(e)}")
            raise

    @log_execution_time
    async def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Optional[User]:
        """
        Оновлення профілю користувача

        Args:
            user_id: ID користувача
            profile_data: Дані для оновлення

        Returns:
            Оновлений користувач
        """
        try:
            # Фільтруємо дозволені поля для оновлення
            allowed_fields = ['first_name', 'last_name', 'email']
            filtered_data = {k: v for k, v in profile_data.items() if k in allowed_fields}

            if not filtered_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid fields to update"
                )

            updated_user = await self.user_repository.update(user_id, filtered_data)

            if updated_user:
                await self._log_business_event(
                    'USER_PROFILE_UPDATED',
                    user_id,
                    {'updated_fields': list(filtered_data.keys())}
                )

                # Також оновлюємо дані в Keycloak
                await self._update_keycloak_user_profile(updated_user.keycloak_id, filtered_data)

            return updated_user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )

    @log_execution_time
    async def update_user_role(self, user_id: int, new_role: str,
                               admin_user_id: int) -> Optional[User]:
        """
        Оновлення ролі користувача (тільки для адміністраторів)

        Args:
            user_id: ID користувача
            new_role: Нова роль
            admin_user_id: ID адміністратора який виконує операцію

        Returns:
            Оновлений користувач
        """
        try:
            # Перевіряємо чи є адміністратор
            admin_user = await self.user_repository.get_by_id(admin_user_id)
            if not admin_user or not admin_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators can change user roles"
                )

            # Валідація нової ролі
            try:
                role_enum = UserRole(new_role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {new_role}"
                )

            # Оновлення ролі
            updated_user = await self.user_repository.update_user_role(user_id, role_enum)

            if updated_user:
                await self._log_business_event(
                    'USER_ROLE_UPDATED',
                    user_id,
                    {
                        'new_role': new_role,
                        'admin_user_id': admin_user_id
                    },
                    admin_user_id
                )

                # Також оновлюємо роль в Keycloak
                await self._update_keycloak_user_role(updated_user.keycloak_id, new_role)

            return updated_user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user role"
            )

    @log_execution_time
    async def deactivate_user(self, user_id: int, admin_user_id: int) -> bool:
        """
        Деактивація користувача

        Args:
            user_id: ID користувача для деактивації
            admin_user_id: ID адміністратора

        Returns:
            True якщо успішно деактивовано
        """
        try:
            # Перевіряємо права адміністратора
            admin_user = await self.user_repository.get_by_id(admin_user_id)
            if not admin_user or not admin_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators can deactivate users"
                )

            # Не можна деактивувати себе
            if user_id == admin_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate yourself"
                )

            success = await self.user_repository.deactivate_user(user_id)

            if success:
                # Також деактивуємо в Keycloak
                user = await self.user_repository.get_by_id(user_id)
                if user:
                    await self._deactivate_keycloak_user(user.keycloak_id)

                await self._log_business_event(
                    'USER_DEACTIVATED',
                    user_id,
                    {'admin_user_id': admin_user_id},
                    admin_user_id
                )

            return success

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deactivating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate user"
            )

    @log_execution_time
    async def activate_user(self, user_id: int, admin_user_id: int) -> bool:
        """
        Активація користувача

        Args:
            user_id: ID користувача для активації
            admin_user_id: ID адміністратора

        Returns:
            True якщо успішно активовано
        """
        try:
            # Перевіряємо права адміністратора
            admin_user = await self.user_repository.get_by_id(admin_user_id)
            if not admin_user or not admin_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators can activate users"
                )

            success = await self.user_repository.activate_user(user_id)

            if success:
                # Також активуємо в Keycloak
                user = await self.user_repository.get_by_id(user_id)
                if user:
                    await self._activate_keycloak_user(user.keycloak_id)

                await self._log_business_event(
                    'USER_ACTIVATED',
                    user_id,
                    {'admin_user_id': admin_user_id},
                    admin_user_id
                )

            return success

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error activating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate user"
            )

    @log_execution_time
    async def sync_with_keycloak(self) -> Dict[str, int]:
        """
        Синхронізація користувачів з Keycloak

        Returns:
            Статистика синхронізації
        """
        try:
            # Отримуємо користувачів з Keycloak
            keycloak_users = await self._get_keycloak_users()

            created_count = 0
            updated_count = 0
            errors = []

            for kc_user in keycloak_users:
                try:
                    user = await self._sync_single_user(kc_user)
                    if user:
                        if hasattr(user, '_was_created') and user._was_created:
                            created_count += 1
                        else:
                            updated_count += 1
                except Exception as e:
                    errors.append(f"Error syncing user {kc_user.get('username', 'unknown')}: {str(e)}")
                    logger.error(f"Error syncing user: {str(e)}")

            await self._log_business_event(
                'KEYCLOAK_SYNC_COMPLETED',
                0,
                {
                    'created_count': created_count,
                    'updated_count': updated_count,
                    'errors_count': len(errors)
                }
            )

            return {
                'created': created_count,
                'updated': updated_count,
                'errors': len(errors),
                'error_details': errors
            }

        except Exception as e:
            logger.error(f"Keycloak sync failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync with Keycloak"
            )

    @log_execution_time
    async def validate_token(self, token: str, token_type: str = 'keycloak') -> Optional[Dict[str, Any]]:
        """
        Валідація токена

        Args:
            token: JWT токен
            token_type: Тип токена ('keycloak' або 'internal')

        Returns:
            Дані токена або None
        """
        try:
            if token_type == 'keycloak':
                return self.jwt_manager.verify_keycloak_token(token)
            else:
                return self.jwt_manager.verify_internal_token(token)
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return None

    @log_execution_time
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Отримання користувача за ID

        Args:
            user_id: ID користувача

        Returns:
            Користувач або None
        """
        try:
            return await self.user_repository.get_by_id(user_id)
        except Exception as e:
            logger.error(f"Error getting user by id {user_id}: {str(e)}")
            return None

    @log_execution_time
    async def get_user_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        """
        Отримання користувача за Keycloak ID

        Args:
            keycloak_id: Keycloak ID користувача

        Returns:
            Користувач або None
        """
        try:
            return await self.user_repository.get_by_keycloak_id(keycloak_id)
        except Exception as e:
            logger.error(f"Error getting user by keycloak_id {keycloak_id}: {str(e)}")
            return None

    @log_execution_time
    async def get_users_list(self, skip: int = 0, limit: int = 100,
                           filters: Optional[Dict[str, Any]] = None) -> List[User]:
        """
        Отримання списку користувачів з фільтрацією

        Args:
            skip: Кількість записів для пропуску
            limit: Максимальна кількість записів
            filters: Фільтри для пошуку

        Returns:
            Список користувачів
        """
        try:
            return await self.user_repository.get_all(skip=skip, limit=limit, filters=filters)
        except Exception as e:
            logger.error(f"Error getting users list: {str(e)}")
            return []

    @log_execution_time
    async def get_users_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Отримання кількості користувачів

        Args:
            filters: Фільтри для підрахунку

        Returns:
            Кількість користувачів
        """
        try:
            return await self.user_repository.count(filters=filters)
        except Exception as e:
            logger.error(f"Error getting users count: {str(e)}")
            return 0

    # Приватні методи

    async def _get_or_create_user(self, keycloak_id: str, username: str,
                                  email: str, token_data: Dict[str, Any]) -> Optional[User]:
        """Отримує або створює користувача в локальній БД"""
        try:
            # Спочатку шукаємо по Keycloak ID
            user = await self.user_repository.get_by_keycloak_id(keycloak_id)

            if not user:
                # Якщо не знайшли, створюємо нового
                user_data = {
                    'keycloak_id': keycloak_id,
                    'username': username,
                    'email': email,
                    'first_name': token_data.get('given_name', ''),
                    'last_name': token_data.get('family_name', ''),
                    'role': self._extract_role_from_token(token_data),
                    'is_active': True
                }

                user = await self.user_repository.create_user(user_data)

                if user:
                    await self._log_business_event(
                        'USER_CREATED_FROM_KEYCLOAK',
                        user.id,
                        {'keycloak_id': keycloak_id, 'username': username}
                    )

            return user

        except Exception as e:
            logger.error(f"Error getting or creating user: {str(e)}")
            return None

    def _extract_role_from_token(self, token_data: Dict[str, Any]) -> UserRole:
        """Витягує роль користувача з токена Keycloak"""
        try:
            # Шукаємо ролі в різних місцях токена
            roles = []

            # Ролі з realm_access
            if 'realm_access' in token_data and 'roles' in token_data['realm_access']:
                roles.extend(token_data['realm_access']['roles'])

            # Ролі з resource_access
            if 'resource_access' in token_data:
                for client, client_data in token_data['resource_access'].items():
                    if 'roles' in client_data:
                        roles.extend(client_data['roles'])

            # Визначаємо роль за пріоритетом
            if 'ADMIN' in roles or 'admin' in roles:
                return UserRole.ADMIN
            elif 'DISPATCHER' in roles or 'dispatcher' in roles:
                return UserRole.DISPATCHER
            else:
                # За замовчуванням диспетчер
                return UserRole.DISPATCHER

        except Exception as e:
            logger.warning(f"Error extracting role from token: {str(e)}")
            return UserRole.DISPATCHER

    async def _authenticate_with_keycloak(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Автентифікація через Keycloak з логіном/паролем"""
        try:
            async with httpx.AsyncClient() as client:
                token_url = f"{self.keycloak_base_url}/auth/realms/{self.keycloak_realm}/protocol/openid_connect/token"

                data = {
                    'grant_type': 'password',
                    'client_id': self.keycloak_client_id,
                    'client_secret': self.keycloak_client_secret,
                    'username': username,
                    'password': password
                }

                response = await client.post(token_url, data=data)

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Keycloak authentication failed: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Keycloak authentication error: {str(e)}")
            return None

    async def _get_admin_token(self) -> Optional[str]:
        """Отримання admin токена для Keycloak Admin API"""
        try:
            # Перевіряємо чи є кешований токен
            if (self.admin_token and self.admin_token_expires_at and
                datetime.utcnow() < self.admin_token_expires_at):
                return self.admin_token

            async with httpx.AsyncClient() as client:
                token_url = f"{self.keycloak_base_url}/auth/realms/master/protocol/openid_connect/token"

                data = {
                    'grant_type': 'client_credentials',
                    'client_id': self.keycloak_client_id,
                    'client_secret': self.keycloak_client_secret
                }

                response = await client.post(token_url, data=data)

                if response.status_code == 200:
                    token_data = response.json()
                    self.admin_token = token_data.get('access_token')
                    expires_in = token_data.get('expires_in', 300)
                    self.admin_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 30)
                    return self.admin_token
                else:
                    logger.error(f"Failed to get admin token: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error getting admin token: {str(e)}")
            return None

    async def _get_keycloak_user_info(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Отримує додаткову інформацію про користувача з Keycloak"""
        try:
            admin_token = await self._get_admin_token()
            if not admin_token:
                return None

            async with httpx.AsyncClient() as client:
                url = f"{self.keycloak_base_url}/auth/admin/realms/{self.keycloak_realm}/users/{keycloak_id}"
                headers = {'Authorization': f'Bearer {admin_token}'}

                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get Keycloak user info: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error getting Keycloak user info: {str(e)}")
            return None

    async def _get_keycloak_users(self) -> List[Dict[str, Any]]:
        """Отримує список користувачів з Keycloak"""
        try:
            admin_token = await self._get_admin_token()
            if not admin_token:
                return []

            async with httpx.AsyncClient() as client:
                url = f"{self.keycloak_base_url}/auth/admin/realms/{self.keycloak_realm}/users"
                headers = {'Authorization': f'Bearer {admin_token}'}

                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get Keycloak users: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error getting Keycloak users: {str(e)}")
            return []

    async def _sync_single_user(self, kc_user: Dict[str, Any]) -> Optional[User]:
        """Синхронізує одного користувача з Keycloak"""
        try:
            keycloak_id = kc_user.get('id')
            if not keycloak_id:
                return None

            # Пошук існуючого користувача
            existing_user = await self.user_repository.get_by_keycloak_id(keycloak_id)

            user_data = {
                'keycloak_id': keycloak_id,
                'username': kc_user.get('username', ''),
                'email': kc_user.get('email', ''),
                'first_name': kc_user.get('firstName', ''),
                'last_name': kc_user.get('lastName', ''),
                'is_active': kc_user.get('enabled', True)
            }

            if existing_user:
                # Оновлюємо існуючого
                return await self.user_repository.update(existing_user.id, user_data)
            else:
                # Створюємо нового
                user_data['role'] = UserRole.DISPATCHER  # За замовчуванням
                user = await self.user_repository.create_user(user_data)
                if user:
                    user._was_created = True
                return user

        except Exception as e:
            logger.error(f"Error syncing single user: {str(e)}")
            return None

