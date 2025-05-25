from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime
import logging

from repositories.base import BaseRepository
from models.base import BaseModel
from utils.decorators import log_execution_time, audit_operation

T = TypeVar('T', bound=BaseModel)


class BaseService(Generic[T], ABC):
    """
    Базовий клас для всіх сервісів системи
    Забезпечує загальну функціональність та інтерфейс
    """

    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)

    @log_execution_time
    @audit_operation
    async def create(self, entity_data: Dict[str, Any], user_id: Optional[int] = None) -> T:
        """
        Створює новий об'єкт

        Args:
            entity_data: Дані для створення об'єкта
            user_id: ID користувача який виконує операцію

        Returns:
            Створений об'єкт
        """
        try:
            # Додаткова валідація бізнес-правил
            await self._validate_create_data(entity_data)

            # Створення через репозиторій
            entity = await self.repository.create(entity_data)

            # Пост-обробка після створення
            await self._post_create_processing(entity, user_id)

            self.logger.info(f"Created {self.__class__.__name__} entity with ID: {entity.id}")
            return entity

        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}")
            raise

    @log_execution_time
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Отримує об'єкт за ID"""
        try:
            entity = await self.repository.get_by_id(entity_id)
            if entity:
                await self._post_get_processing(entity)
            return entity
        except Exception as e:
            self.logger.error(f"Error getting entity by ID {entity_id}: {str(e)}")
            raise

    @log_execution_time
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Отримує всі об'єкти з пагінацією"""
        try:
            entities = await self.repository.get_all(skip=skip, limit=limit)
            for entity in entities:
                await self._post_get_processing(entity)
            return entities
        except Exception as e:
            self.logger.error(f"Error getting all entities: {str(e)}")
            raise

    @log_execution_time
    @audit_operation
    async def update(self, entity_id: int, update_data: Dict[str, Any],
                     user_id: Optional[int] = None) -> Optional[T]:
        """
        Оновлює об'єкт

        Args:
            entity_id: ID об'єкта для оновлення
            update_data: Дані для оновлення
            user_id: ID користувача який виконує операцію

        Returns:
            Оновлений об'єкт або None якщо не знайдено
        """
        try:
            # Перевіряємо чи існує об'єкт
            existing_entity = await self.repository.get_by_id(entity_id)
            if not existing_entity:
                return None

            # Валідація бізнес-правил для оновлення
            await self._validate_update_data(entity_id, update_data, existing_entity)

            # Оновлення через репозиторій
            updated_entity = await self.repository.update(entity_id, update_data)

            # Пост-обробка після оновлення
            if updated_entity:
                await self._post_update_processing(updated_entity, existing_entity, user_id)
                self.logger.info(f"Updated {self.__class__.__name__} entity with ID: {entity_id}")

            return updated_entity

        except Exception as e:
            self.logger.error(f"Error updating entity {entity_id}: {str(e)}")
            raise

    @log_execution_time
    @audit_operation
    async def delete(self, entity_id: int, user_id: Optional[int] = None) -> bool:
        """
        Видаляє об'єкт

        Args:
            entity_id: ID об'єкта для видалення
            user_id: ID користувача який виконує операцію

        Returns:
            True якщо видалено успішно, False якщо об'єкт не знайдено
        """
        try:
            # Перевіряємо чи існує об'єкт
            existing_entity = await self.repository.get_by_id(entity_id)
            if not existing_entity:
                return False

            # Валідація бізнес-правил для видалення
            await self._validate_delete(entity_id, existing_entity)

            # Пре-обробка перед видаленням
            await self._pre_delete_processing(existing_entity, user_id)

            # Видалення через репозиторій
            success = await self.repository.delete(entity_id)

            if success:
                # Пост-обробка після видалення
                await self._post_delete_processing(existing_entity, user_id)
                self.logger.info(f"Deleted {self.__class__.__name__} entity with ID: {entity_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error deleting entity {entity_id}: {str(e)}")
            raise

    async def exists(self, entity_id: int) -> bool:
        """Перевіряє чи існує об'єкт з даним ID"""
        return await self.repository.exists(entity_id)

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Підраховує кількість об'єктів з фільтрами"""
        return await self.repository.count(filters)

    # Методи для перевизначення у дочірніх класах

    async def _validate_create_data(self, entity_data: Dict[str, Any]) -> None:
        """Валідація даних перед створенням (для перевизначення)"""
        pass

    async def _validate_update_data(self, entity_id: int, update_data: Dict[str, Any],
                                    existing_entity: T) -> None:
        """Валідація даних перед оновленням (для перевизначення)"""
        pass

    async def _validate_delete(self, entity_id: int, existing_entity: T) -> None:
        """Валідація перед видаленням (для перевизначення)"""
        pass

    async def _post_create_processing(self, entity: T, user_id: Optional[int] = None) -> None:
        """Обробка після створення (для перевизначення)"""
        pass

    async def _post_get_processing(self, entity: T) -> None:
        """Обробка після отримання (для перевизначення)"""
        pass

    async def _post_update_processing(self, updated_entity: T, old_entity: T,
                                      user_id: Optional[int] = None) -> None:
        """Обробка після оновлення (для перевизначення)"""
        pass

    async def _pre_delete_processing(self, entity: T, user_id: Optional[int] = None) -> None:
        """Обробка перед видаленням (для перевизначення)"""
        pass

    async def _post_delete_processing(self, entity: T, user_id: Optional[int] = None) -> None:
        """Обробка після видалення (для перевизначення)"""
        pass

    # Утилітарні методи

    def _get_current_timestamp(self) -> datetime:
        """Отримує поточний час"""
        return datetime.utcnow()

    async def _log_business_event(self, event_type: str, entity_id: int,
                                  details: Dict[str, Any], user_id: Optional[int] = None) -> None:
        """Логування бізнес-подій"""
        log_data = {
            'service': self.__class__.__name__,
            'event_type': event_type,
            'entity_id': entity_id,
            'user_id': user_id,
            'details': details,
            'timestamp': self._get_current_timestamp()
        }
        self.logger.info(f"Business event: {log_data}")

    async def _validate_business_rules(self, rules: List[str], data: Dict[str, Any]) -> None:
        """
        Валідація бізнес-правил

        Args:
            rules: Список правил для валідації
            data: Дані для валідації
        """
        for rule in rules:
            validator_method = getattr(self, f'_validate_{rule}', None)
            if validator_method:
                await validator_method(data)

    def _format_error_message(self, operation: str, entity_id: Optional[int] = None,
                              details: str = "") -> str:
        """Форматує повідомлення про помилку"""
        entity_part = f" for entity {entity_id}" if entity_id else ""
        details_part = f": {details}" if details else ""
        return f"Failed to {operation}{entity_part}{details_part}"