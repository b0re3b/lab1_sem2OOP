from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .flight import Flight
    from .flight_assignment import FlightAssignment
    from .operation_log import OperationLog


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"


@dataclass
class User(Base, TimestampMixin):

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'DISPATCHER')", name="check_user_role"),
        {"schema": "airline"}
    )

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Keycloak integration
    keycloak_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Basic user info
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Role and status
    role: Mapped[UserRole] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    created_flights: Mapped[List["Flight"]] = relationship(
        "Flight",
        back_populates="creator",
        cascade="all, delete-orphan"
    )

    flight_assignments: Mapped[List["FlightAssignment"]] = relationship(
        "FlightAssignment",
        back_populates="assigned_by_user",
        cascade="all, delete-orphan"
    )

    operation_logs: Mapped[List["OperationLog"]] = relationship(
        "OperationLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get full name - аналог Lombok derived property"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN

    @property
    def is_dispatcher(self) -> bool:
        """Check if user is dispatcher"""
        return self.role == UserRole.DISPATCHER

    def __post_init__(self):
        """Post initialization - аналог Lombok @PostConstruct"""
        if isinstance(self.role, str):
            self.role = UserRole(self.role)