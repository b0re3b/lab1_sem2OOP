from typing import List, Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from config.database import DatabaseConfig
from config.logging_config import log_database_operation
from models.user import User
from utils.validators import UserValidator


class UserRepository:
    def __init__(self):
        self.table_name = "users"
        self.validator = UserValidator()
        self.db_manager = DatabaseConfig()
    @log_database_operation
    def create_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        """Створення нового користувача"""
        self.validator.validate_user_data(user_data)

        query = """
                INSERT INTO users (keycloak_id, username, email, first_name, last_name, role, is_active)
                VALUES (%(keycloak_id)s, %(username)s, %(email)s, %(first_name)s, %(last_name)s, %(role)s, \
                        %(is_active)s)
                RETURNING * \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, user_data)
                    result = cursor.fetchone()
                    conn.commit()
                    return User(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error creating user: {e}")

    @log_database_operation
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Пошук користувача за ID"""
        query = "SELECT * FROM users WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (user_id,))
                    result = cursor.fetchone()
                    return User(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error finding user by id: {e}")

    @log_database_operation
    def find_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        """Пошук користувача за Keycloak ID"""
        self.validator.validate_keycloak_id(keycloak_id)

        query = "SELECT * FROM users WHERE keycloak_id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (keycloak_id,))
                    result = cursor.fetchone()
                    return User(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error finding user by keycloak_id: {e}")

    @log_database_operation
    def find_by_username(self, username: str) -> Optional[User]:
        """Пошук користувача за логіном"""
        self.validator.validate_username(username)

        query = "SELECT * FROM users WHERE username = %s AND is_active = TRUE"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (username,))
                    result = cursor.fetchone()
                    return User(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error finding user by username: {e}")

    @log_database_operation
    def find_all_by_role(self, role: str) -> List[User]:
        """Пошук всіх користувачів за роллю"""
        query = "SELECT * FROM users WHERE role = %s AND is_active = TRUE ORDER BY last_name, first_name"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (role,))
                    results = cursor.fetchall()
                    return [User(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error finding users by role: {e}")

    @log_database_operation
    def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """Оновлення даних користувача"""
        if not update_data:
            return self.find_by_id(user_id)

        set_clause = ", ".join([f"{key} = %({key})s" for key in update_data.keys()])
        query = f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %(id)s RETURNING *"

        update_data['id'] = user_id

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, update_data)
                    result = cursor.fetchone()
                    conn.commit()
                    return User(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error updating user: {e}")

    @log_database_operation
    def deactivate_user(self, user_id: int) -> bool:
        """Деактивація користувача"""
        query = "UPDATE users SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (user_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except psycopg2.Error as e:
            raise Exception(f"Database error deactivating user: {e}")
