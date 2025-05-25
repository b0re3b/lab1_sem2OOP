from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class UserRole(enum.Enum):
    """User roles enumeration"""
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"


class User(BaseModel):
    """User model for system users (Admin, Dispatcher)"""

    __tablename__ = 'users'

    keycloak_id = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    created_flights = relationship("Flight", back_populates="created_by_user", foreign_keys="Flight.created_by")
    flight_assignments = relationship("FlightAssignment", back_populates="assigned_by_user")
    operation_logs = relationship("OperationLog", back_populates="user")

    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN

    def is_dispatcher(self):
        """Check if user is dispatcher"""
        return self.role == UserRole.DISPATCHER

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role.value}')>"