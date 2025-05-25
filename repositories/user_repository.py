from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.user import User, UserRole
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Репозиторій для роботи з користувачами системи
    Реалізує всі методи для User моделі
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Отримати користувача за ID"""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by id {user_id}: {str(e)}")
            raise

    def get_all(self) -> List[User]:
        """Отримати всіх користувачів"""
        try:
            return self.db.query(User).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all users: {str(e)}")
            raise

    def create(self, user: User) -> User:
        """Створити користувача"""
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Created user with id {user.id}")
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise

    def update(self, user: User) -> User:
        """Оновити користувача"""
        try:
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Updated user with id {user.id}")
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user with id {user.id}: {str(e)}")
            raise

    def delete(self, user_id: int) -> bool:
        """Видалити користувача"""
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False

            self.db.delete(user)
            self.db.commit()
            logger.info(f"Deleted user with id {user_id}")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting user with id {user_id}: {str(e)}")
            raise

    def get_by_username(self, username: str) -> Optional[User]:
        """Отримати користувача за username"""
        try:
            return self.db.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by username {username}: {str(e)}")
            raise

    def get_by_email(self, email: str) -> Optional[User]:
        """Отримати користувача за email"""
        try:
            return self.db.query(User).filter(
                User.email == email,
                User.is_active == True
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            raise

    def get_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        """Отримати користувача за Keycloak ID"""
        try:
            return self.db.query(User).filter(
                User.keycloak_id == keycloak_id,
                User.is_active == True
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by keycloak_id {keycloak_id}: {str(e)}")
            raise

    def get_by_role(self, role: UserRole, active_only: bool = True) -> List[User]:
        """Отримати користувачів за роллю"""
        try:
            query = self.db.query(User).filter(User.role == role)
            if active_only:
                query = query.filter(User.is_active == True)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting users by role {role}: {str(e)}")
            raise

    def get_active_users(self) -> List[User]:
        """Отримати всіх активних користувачів"""
        try:
            return self.db.query(User).filter(User.is_active == True).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active users: {str(e)}")
            raise

    def deactivate_user(self, user_id: int) -> bool:
        """Деактивувати користувача (м'яке видалення)"""
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False

            user.is_active = False
            self.db.commit()
            logger.info(f"Deactivated user with id {user_id}")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deactivating user with id {user_id}: {str(e)}")
            raise

    def activate_user(self, user_id: int) -> bool:
        """Активувати користувача"""
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False

            user.is_active = True
            self.db.commit()
            logger.info(f"Activated user with id {user_id}")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error activating user with id {user_id}: {str(e)}")
            raise

    def search_users(self, search_term: str, role: Optional[UserRole] = None) -> List[User]:
        """Пошук користувачів за ім'ям, прізвищем або email"""
        try:
            query = self.db.query(User).filter(
                User.is_active == True
            ).filter(
                (User.first_name.ilike(f"%{search_term}%")) |
                (User.last_name.ilike(f"%{search_term}%")) |
                (User.email.ilike(f"%{search_term}%")) |
                (User.username.ilike(f"%{search_term}%"))
            )

            if role:
                query = query.filter(User.role == role)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching users with term {search_term}: {str(e)}")
            raise

    def create_user(self, keycloak_id: str, username: str, email: str,
                    first_name: str, last_name: str, role: UserRole) -> User:
        """Створити нового користувача"""
        try:
            # Перевірка унікальності
            if self.get_by_username(username):
                raise ValueError(f"Username {username} already exists")

            if self.get_by_email(email):
                raise ValueError(f"Email {email} already exists")

            if self.get_by_keycloak_id(keycloak_id):
                raise ValueError(f"Keycloak ID {keycloak_id} already exists")

            user = User(
                keycloak_id=keycloak_id,
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_active=True
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info(f"Created user {username} with role {role}")
            return user

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating user {username}: {str(e)}")
            raise

    def update_user_role(self, user_id: int, new_role: UserRole) -> Optional[User]:
        """Оновити роль користувача"""
        try:
            user = self.get_by_id(user_id)
            if not user:
                return None

            old_role = user.role
            user.role = new_role
            self.db.commit()
            self.db.refresh(user)

            logger.info(f"Updated user {user.username} role from {old_role} to {new_role}")
            return user

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user role for id {user_id}: {str(e)}")
            raise

    def get_admins(self) -> List[User]:
        """Отримати всіх адміністраторів"""
        return self.get_by_role(UserRole.ADMIN)

    def get_dispatchers(self) -> List[User]:
        """Отримати всіх диспетчерів"""
        return self.get_by_role(UserRole.DISPATCHER)

    def sync_with_keycloak(self, keycloak_user_data: dict) -> User:
        """Синхронізація користувача з Keycloak"""
        try:
            keycloak_id = keycloak_user_data.get('id')
            username = keycloak_user_data.get('username')
            email = keycloak_user_data.get('email')
            first_name = keycloak_user_data.get('firstName', '')
            last_name = keycloak_user_data.get('lastName', '')

            # Спроба знайти існуючого користувача
            user = self.get_by_keycloak_id(keycloak_id)

            if user:
                # Оновлення існуючого користувача
                user.username = username
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                self.db.commit()
                self.db.refresh(user)
                logger.info(f"Synced existing user {username} with Keycloak")
            else:
                # Створення нового користувача (за замовчуванням DISPATCHER)
                user = self.create_user(
                    keycloak_id=keycloak_id,
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role=UserRole.DISPATCHER
                )
                logger.info(f"Created new user {username} from Keycloak sync")

            return user

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error syncing user with Keycloak: {str(e)}")
            raise