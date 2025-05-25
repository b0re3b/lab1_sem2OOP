"""
Сервіс автентифікації та авторизації
Інтеграція з Keycloak та управління користувачами
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException, status

from .base_service import BaseService
from models.user import User, UserRole
from repositories.user_repository import UserRepository
from utils.jwt_utils import (
    verify_keycloak_token, create_internal_token,
    extract_user_roles, get_current_user
)
from utils.decorators import log_execution_time
from config.settings import get_settings

settings = get_settings()


class AuthService(BaseService[User]):
    """
    Сервіс для роботи з автентифікацією та авторизацією
    """

    def __init__(self, user_repository: UserRepository):
        super().__init__(user_repository)
        self.user_repository = user_repository
        self.keycloak_base_url = settings.keycloak_url
        self.keycloak_realm = settings.keycloak_realm
        self.keycloak_client_id = settings.keycloak_client_id
        self.keycloak_client_secret = settings.keycloak_client_secret

    @log_execution_time
    async def authenticate_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Автентифікація користувача через Keycloak token

        Args:
            token: JWT токен від Keycloak

        Returns:
            Інформація про користувача або None
        """
        try:
            # Верифікація токена через Keycloak
            token_data = await verify_keycloak_token(token)
            if not token_data:
                return None

            keycloak_id = token_data.get('sub')
            username = token_data.get('preferred_username')
            email = token_data.get('email')

            if not keycloak_id:
                self.logger.warning("Token does not contain Keycloak ID")
                return None

            # Пошук або створення користувача в локальній БД
            user = await self._get_or_create_user(
                keycloak_id=keycloak_id,
                username=username,
                email=email,
                token_data=token_data
            )

            if not user or not user.is_active:
                self.logger.warning(f"User {username} is inactive or not found")
                return None

            # Створення внутрішнього токена
            internal_token = await create_internal_token(user.id, user.role.value)

            await self._log_business_event(
                'USER_AUTHENTICATED',
                user.id,
                {'username': user.username, 'role': user.role.value}
            )

            return {
                'user': user,
                'token': internal_token,
                'expires_at': datetime.utcnow() + timedelta(hours=8)
            }

        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
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
            self.logger.error(f"Authorization check failed for user {user_id}: {str(e)}")
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
            self.logger.error(f"Error getting user profile {user_id}: {str(e)}")
            raise

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
            self.logger.error(f"Error updating user role: {str(e)}")
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
            self.logger.error(f"Error deactivating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate user"
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
                    self.logger.error(f"Error syncing user: {str(e)}")

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
            self.logger.error(f"Keycloak sync failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync with Keycloak"
            )

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
            self.logger.error(f"Error getting or creating user: {str(e)}")
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
            self.logger.warning(f"Error extracting role from token: {str(e)}")
            return UserRole.DISPATCHER

    async def _get_keycloak_user_info(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Отримує додаткову інформацію про користувача з Keycloak"""
        try:
            # Тут має бути запит до Keycloak API
            # Поки що повертаємо заглушку
            return None
        except Exception as e:
            self.logger.error(f"Error getting Keycloak user info: {str(e)}")
            return None

    async def _get_keycloak_users(self) -> List[Dict[str, Any]]:
        """Отримує список користувачів з Keycloak"""
        try:
            # Тут має бути запит до Keycloak Admin API
            # Поки що повертаємо заглушку
            return []
        except Exception as e:
            self.logger.error(f"Error getting Keycloak users: {str(e)}")
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
            self.logger.error(f"Error syncing single user: {str(e)}")
            return None

    async def _update_keycloak_user_role(self, keycloak_id: str, role: str) -> bool:
        """Оновлює роль користувача в Keycloak"""
        try:
            # Тут має бути запит до Keycloak Admin API для оновлення ролі
            # Поки що повертаємо True
            self.logger.info(f"Would update Keycloak user {keycloak_id} role to {role}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating Keycloak user role: {str(e)}")
            return False