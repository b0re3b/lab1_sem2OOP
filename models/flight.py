from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .flight_assignment import FlightAssignment


class FlightStatus(str, Enum):
    """Flight status enum"""
    SCHEDULED = "SCHEDULED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


@dataclass
class Flight(Base, TimestampMixin):

    __tablename__ = "flights"
    __table_args__ = (
        CheckConstraint(
            "status IN ('SCHEDULED', 'DELAYED', 'CANCELLED', 'COMPLETED')",
            name="check_flight_status"
        ),
        {"schema": "airline"}
    )

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Flight identification
    flight_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    # Route information
    departure_city: Mapped[str] = mapped_column(String(100), nullable=False)
    arrival_city: Mapped[str] = mapped_column(String(100), nullable=False)

    # Schedule
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    arrival_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Aircraft and crew requirements
    aircraft_type: Mapped[str] = mapped_column(String(50), nullable=False)
    crew_required: Mapped[int] = mapped_column(Integer, default=4, nullable=False)

    # Status
    status: Mapped[FlightStatus] = mapped_column(
        String(20),
        default=FlightStatus.SCHEDULED,
        nullable=False
    )

    # Foreign keys
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("airline.users.id", ondelete="SET NULL")
    )

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="created_flights"
    )

    flight_assignments: Mapped[List["FlightAssignment"]] = relationship(
        "FlightAssignment",
        back_populates="flight",
        cascade="all, delete-orphan"
    )

    @property
    def route(self) -> str:
        """Get flight route - аналог Lombok derived property"""
        return f"{self.departure_city} → {self.arrival_city}"

    @property
    def duration_hours(self) -> float:
        """Calculate flight duration in hours"""
        delta = self.arrival_time - self.departure_time
        return delta.total_seconds() / 3600

    @property
    def assigned_crew_count(self) -> int:
        """Count of assigned crew members"""
        return len([
            assignment for assignment in self.flight_assignments
            if assignment.status == "ASSIGNED"
        ])

    @property
    def is_fully_staffed(self) -> bool:
        """Check if flight has enough crew members"""
        return self.assigned_crew_count >= self.crew_required

    @property
    def staffing_status(self) -> str:
        """Get staffing status"""
        if self.assigned_crew_count >= self.crew_required:
            return "FULLY_STAFFED"
        elif self.assigned_crew_count > 0:
            return "PARTIALLY_STAFFED"
        return "NOT_STAFFED"

    def is_time_conflict(self, other_departure: datetime, other_arrival: datetime) -> bool:
        """Check if flight times conflict with given time range"""
        return (
                (self.departure_time <= other_departure <= self.arrival_time) or
                (self.departure_time <= other_arrival <= self.arrival_time) or
                (other_departure <= self.departure_time <= other_arrival)
        )

    def __post_init__(self):
        """Post initialization"""
        if isinstance(self.status, str):
            self.status = FlightStatus(self.status)