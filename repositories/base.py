import logging
from abc import ABC
from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy import desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """
    Базовий репозиторій з основними CRUD операціями
    Використовує Generic для типізації та Repository pattern
    """

    def __init__(self, db_session: Session, model_class: type):
        self.db = db_session
        self.model_class = model_class

    def create(self, **kwargs) -> T:
        """Створити новий запис"""
        try:
            instance = self.model_class(**kwargs)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            logger.info(f"Created {self.model_class.__name__} with id {instance.id}")
            return instance
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {str(e)}")
            raise

    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Отримати запис за ID"""
        try:
            return self.db.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model_class.__name__} by id {entity_id}: {str(e)}")
            raise

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Отримати всі записи з можливістю пагінації"""
        try:
            return self.db.query(self.model_class).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {str(e)}")
            raise

    def update(self, entity_id: int, **kwargs) -> Optional[T]:
        """Оновити запис"""
        try:
            instance = self.get_by_id(entity_id)
            if not instance:
                return None

            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            self.db.commit()
            self.db.refresh(instance)
            logger.info(f"Updated {self.model_class.__name__} with id {entity_id}")
            return instance
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model_class.__name__} with id {entity_id}: {str(e)}")
            raise

    def delete(self, entity_id: int) -> bool:
        """Видалити запис"""
        try:
            instance = self.get_by_id(entity_id)
            if not instance:
                return False

            self.db.delete(instance)
            self.db.commit()
            logger.info(f"Deleted {self.model_class.__name__} with id {entity_id}")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model_class.__name__} with id {entity_id}: {str(e)}")
            raise

    def exists(self, entity_id: int) -> bool:
        """Перевірити чи існує запис"""
        try:
            return self.db.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model_class.__name__} with id {entity_id}: {str(e)}")
            raise

    def count(self, **filters) -> int:
        """Підрахувати кількість записів з фільтрами"""
        try:
            query = self.db.query(self.model_class)
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model_class.__name__}: {str(e)}")
            raise

    def find_by_criteria(self, filters: Dict[str, Any],
                         order_by: Optional[str] = None,
                         desc_order: bool = False,
                         skip: int = 0,
                         limit: int = 100) -> List[T]:
        """Знайти записи за критеріями"""
        try:
            query = self.db.query(self.model_class)

            # Застосування фільтрів
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    if isinstance(value, list):
                        query = query.filter(getattr(self.model_class, key).in_(value))
                    else:
                        query = query.filter(getattr(self.model_class, key) == value)

            # Сортування
            if order_by and hasattr(self.model_class, order_by):
                if desc_order:
                    query = query.order_by(desc(getattr(self.model_class, order_by)))
                else:
                    query = query.order_by(asc(getattr(self.model_class, order_by)))

            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error finding {self.model_class.__name__} by criteria: {str(e)}")
            raise

    def bulk_create(self, objects_data: List[Dict[str, Any]]) -> List[T]:
        """Масове створення записів"""
        try:
            instances = [self.model_class(**data) for data in objects_data]
            self.db.add_all(instances)
            self.db.commit()

            for instance in instances:
                self.db.refresh(instance)

            logger.info(f"Bulk created {len(instances)} {self.model_class.__name__} instances")
            return instances
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error bulk creating {self.model_class.__name__}: {str(e)}")
            raise

    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Масове оновлення записів"""
        try:
            updated_count = 0
            for update_data in updates:
                entity_id = update_data.pop('id')
                result = self.db.query(self.model_class).filter(
                    self.model_class.id == entity_id
                ).update(update_data)
                updated_count += result

            self.db.commit()
            logger.info(f"Bulk updated {updated_count} {self.model_class.__name__} instances")
            return updated_count
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error bulk updating {self.model_class.__name__}: {str(e)}")
            raise