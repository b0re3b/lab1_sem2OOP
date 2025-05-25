from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, func, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .flight import Flight
    from .crew import CrewMember
    from .user import User


class AssignmentStatus(str, Enum):
    """Assignment status enum"""
    ASSIGNED = "ASSIGNED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


@dataclass
class FlightAssignment(Base):
    __tablename__ = "flight_assignments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ASSIGNED', 'CONFIRMED', 'CANCELLED')",
            name="check_assignment_status"
        ),
        UniqueConstraint(
            "crew_member_id", "flight_id",
            name="unique_crew_flight_assignment"
        ),
        {"schema": "airline"}
    )

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Assignment status and notes
    status: Mapped[AssignmentStatus] = mapped_column(
        String(20),
        default=AssignmentStatus.ASSIGNED,
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        nullable=False
    )

    # Foreign keys
    flight_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("airline.flights.id", ondelete="CASCADE"),
        nullable=False
    )

    crew_member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("airline.crew_members.id", ondelete="CASCADE"),
        nullable=False
    )

    assigned_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("airline.users.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Relationships
    flight: Mapped["Flight"] = relationship(
        "Flight",
        back_populates="flight_assignments"
    )

    crew_member: Mapped["CrewMember"] = relationship(
        "CrewMember",
        back_populates="flight_assignments"
    )

    assigned_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="flight_assignments"
    )

    @property
    def is_active(self) -> bool:
        """Check if assignment is active"""
        return self.status == AssignmentStatus.ASSIGNED

    @property
    def is_confirmed(self) -> bool:
        """Check if assignment is confirmed"""
        return self.status == AssignmentStatus.CONFIRMED

    @property
    def is_cancelled(self) -> bool:
        """Check if assignment is cancelled"""
        return self.status == AssignmentStatus.CANCELLED

    @property
    def crew_member_name(self) -> str:
        """Get crew member full name"""
        return self.crew_member.full_name if self.crew_member else ""

    @property
    def crew_position_name(self) -> str:
        """Get crew member position name"""
        return self.crew_member.position_name if self.crew_member else ""

    @property
    def flight_number(self) -> str:
        """Get flight number"""
        return self.flight.flight_number if self.flight else ""

    @property
    def flight_route(self) -> str:
        """Get flight route"""
        return self.flight.route if self.flight else ""

    @property
    def assigned_by_name(self) -> str:
        """Get name of user who made the assignment"""
        return self.assigned_by_user.full_name if self.assigned_by_user else ""

    def confirm_assignment(self, notes: Optional[str] = None) -> None:
        """Confirm the assignment"""
        self.status = AssignmentStatus.CONFIRMED
        if notes:
            self.notes = notes

    def cancel_assignment(self, notes: Optional[str] = None) -> None:
        """Cancel the assignment"""
        self.status = AssignmentStatus.CANCELLED
        if notes:
            self.notes = notes

    def has_time_conflict(self) -> bool:
        """Check if assignment has time conflict with other assignments"""
        if not self.crew_member or not self.flight:
            return False

        for other_assignment in self.crew_member.flight_assignments:
            if (other_assignment.id != self.id and
                    other_assignment.is_active and
                    other_assignment.flight.is_time_conflict(
                        self.flight.departure_time,
                        self.flight.arrival_time
                    )):
                return True
        return False

    def __post_init__(self):
        """Post initialization"""
        if isinstance(self.status, str):
            self.status = AssignmentStatus(self.status)