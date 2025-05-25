from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING, List
from sqlalchemy import String, Integer, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import INET, JSONB

from .base import Base

if TYPE_CHECKING:
    from .user import User


@dataclass
class OperationLog(Base):

    __tablename__ = "operation_logs"
    __table_args__ = {"schema": "airline"}

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Operation details
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Data tracking (JSON fields for PostgreSQL)
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        nullable=False
    )

    # Foreign key (optional - for anonymous operations)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("airline.users.id", ondelete="SET NULL")
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="operation_logs"
    )

    @property
    def user_name(self) -> str:
        """Get user name who performed the operation"""
        return self.user.full_name if self.user else "System"

    @property
    def is_create_operation(self) -> bool:
        """Check if this is a CREATE operation"""
        return self.operation_type.upper() == "INSERT"

    @property
    def is_update_operation(self) -> bool:
        """Check if this is an UPDATE operation"""
        return self.operation_type.upper() == "UPDATE"

    @property
    def is_delete_operation(self) -> bool:
        """Check if this is a DELETE operation"""
        return self.operation_type.upper() == "DELETE"

    @property
    def has_data_changes(self) -> bool:
        """Check if operation includes data changes"""
        return self.old_values is not None or self.new_values is not None

    @property
    def operation_summary(self) -> str:
        """Get operation summary for display"""
        base = f"{self.operation_type} on {self.table_name}"
        if self.record_id:
            base += f" (ID: {self.record_id})"
        return base

    def get_changed_fields(self) -> List[str]:
        """Get list of fields that were changed in UPDATE operations"""
        if not (self.is_update_operation and self.old_values and self.new_values):
            return []

        changed_fields = []
        for key, new_value in self.new_values.items():
            old_value = self.old_values.get(key)
            if old_value != new_value:
                changed_fields.append(key)

        return changed_fields

    def get_field_change(self, field_name: str) -> tuple[Any, Any]:
        """Get old and new values for specific field"""
        if not (self.old_values and self.new_values):
            return None, None

        old_value = self.old_values.get(field_name)
        new_value = self.new_values.get(field_name)

        return old_value, new_value

    def get_change_description(self) -> str:
        """Get human-readable description of changes"""
        if self.is_create_operation:
            return f"Created new {self.table_name} record"
        elif self.is_delete_operation:
            return f"Deleted {self.table_name} record"
        elif self.is_update_operation:
            changed_fields = self.get_changed_fields()
            if changed_fields:
                return f"Updated {', '.join(changed_fields)} in {self.table_name}"
            return f"Updated {self.table_name} record"
        return self.description or "Unknown operation"

    def to_audit_dict(self) -> Dict[str, Any]:
        """Convert to audit dictionary for external systems"""
        return {
            "id": self.id,
            "operation": self.operation_type,
            "table": self.table_name,
            "record_id": self.record_id,
            "user": self.user_name,
            "timestamp": self.created_at.isoformat(),
            "changes": self.get_changed_fields() if self.is_update_operation else None,
            "description": self.get_change_description()
        }

    @classmethod
    def create_log(
            cls,
            operation_type: str,
            table_name: str,
            record_id: Optional[int] = None,
            old_values: Optional[Dict[str, Any]] = None,
            new_values: Optional[Dict[str, Any]] = None,
            description: Optional[str] = None,
            user_id: Optional[int] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None
    ) -> "OperationLog":
        """Factory method to create operation log - аналог Lombok @Builder"""
        return cls(
            operation_type=operation_type,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @classmethod
    def log_create(
            cls,
            table_name: str,
            record_id: int,
            new_values: Dict[str, Any],
            user_id: Optional[int] = None,
            description: Optional[str] = None
    ) -> "OperationLog":
        """Log CREATE operation"""
        return cls.create_log(
            operation_type="INSERT",
            table_name=table_name,
            record_id=record_id,
            new_values=new_values,
            user_id=user_id,
            description=description or f"Created new {table_name} record"
        )

    @classmethod
    def log_update(
            cls,
            table_name: str,
            record_id: int,
            old_values: Dict[str, Any],
            new_values: Dict[str, Any],
            user_id: Optional[int] = None,
            description: Optional[str] = None
    ) -> "OperationLog":
        """Log UPDATE operation"""
        return cls.create_log(
            operation_type="UPDATE",
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            description=description or f"Updated {table_name} record"
        )

    @classmethod
    def log_delete(
            cls,
            table_name: str,
            record_id: int,
            old_values: Dict[str, Any],
            user_id: Optional[int] = None,
            description: Optional[str] = None
    ) -> "OperationLog":
        """Log DELETE operation"""
        return cls.create_log(
            operation_type="DELETE",
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            user_id=user_id,
            description=description or f"Deleted {table_name} record"
        )

    @classmethod
    def log_flight_assignment(
            cls,
            flight_id: int,
            crew_member_id: int,
            user_id: int,
            operation: str = "ASSIGN"
    ) -> "OperationLog":
        """Log flight assignment operation"""
        return cls.create_log(
            operation_type="BUSINESS_OPERATION",
            table_name="flight_assignments",
            description=f"{operation} crew member {crew_member_id} to flight {flight_id}",
            user_id=user_id,
            new_values={
                "flight_id": flight_id,
                "crew_member_id": crew_member_id,
                "operation": operation
            }
        )

    @classmethod
    def log_flight_status_change(
            cls,
            flight_id: int,
            old_status: str,
            new_status: str,
            user_id: Optional[int] = None
    ) -> "OperationLog":
        """Log flight status change"""
        return cls.create_log(
            operation_type="STATUS_CHANGE",
            table_name="flights",
            record_id=flight_id,
            old_values={"status": old_status},
            new_values={"status": new_status},
            user_id=user_id,
            description=f"Flight status changed from {old_status} to {new_status}"
        )

    def __repr__(self) -> str:
        """String representation"""
        return f"OperationLog(id={self.id}, operation={self.operation_type}, table={self.table_name}, user={self.user_name})"