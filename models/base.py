from datetime import datetime
from typing import Any, Dict
from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from dataclasses import dataclass


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


@dataclass
class TimestampMixin:
    """Mixin for adding timestamp fields - аналог Lombok @CreationTimestamp"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary - аналог Lombok @Data"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model from dictionary - аналог Lombok @Setter"""
        for key, value in data.items():
            if hasattr(self, key) and key != 'id':
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation - аналог Lombok @ToString"""
        attrs = ', '.join(
            f"{key}={value!r}"
            for key, value in self.to_dict().items()
            if not key.startswith('_')
        )
        return f"{self.__class__.__name__}({attrs})"