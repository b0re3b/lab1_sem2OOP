from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .crew_position import CrewPosition
    from .flight_assignment import FlightAssignment


class CertificationLevel(str, Enum):
    """Certification level enum"""
    JUNIOR = "JUNIOR"
    SENIOR = "SENIOR"
    CAPTAIN = "CAPTAIN"


@dataclass
class CrewMember(Base, TimestampMixin):

    __tablename__ = "crew_members"
    __table_args__ = (
        CheckConstraint(
            "certification_level IN ('JUNIOR', 'SENIOR', 'CAPTAIN')",
            name="check_certification_level"
        ),
        {"schema": "airline"}
    )

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Employee identification
    employee_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Professional information
    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    certification_level: Mapped[CertificationLevel] = mapped_column(
        String(20),
        default=CertificationLevel.JUNIOR,
        nullable=False
    )

    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))

    # Foreign keys
    position_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("airline.crew_positions.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Relationships
    position: Mapped["CrewPosition"] = relationship(
        "CrewPosition",
        back_populates="crew_members"
    )

    flight_assignments: Mapped[List["FlightAssignment"]] = relationship(
        "FlightAssignment",
        back_populates="crew_member",
        cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get full name - аналог Lombok derived property"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_senior(self) -> bool:
        """Check if crew member is senior level"""
        return self.certification_level in [CertificationLevel.SENIOR, CertificationLevel.CAPTAIN]

    @property
    def is_captain(self) -> bool:
        """Check if crew member is captain level"""
        return self.certification_level == CertificationLevel.CAPTAIN

    @property
    def active_assignments_count(self) -> int:
        """Count of active flight assignments"""
        return len([
            assignment for assignment in self.flight_assignments
            if assignment.status == "ASSIGNED"
        ])

    @property
    def position_name(self) -> str:
        """Get position name"""
        return self.position.position_name if self.position else ""

    def can_be_assigned(self, flight_departure, flight_arrival) -> bool:
        """
        Check if crew member can be assigned to flight at given time
        """
        if not self.is_available:
            return False

        # Check for time conflicts with existing assignments
        for assignment in self.flight_assignments:
            if (assignment.status == "ASSIGNED" and
                    assignment.flight.is_time_conflict(flight_departure, flight_arrival)):
                return False

        return True

    def get_experience_level(self) -> str:
        """Get experience level description"""
        if self.experience_years < 2:
            return "Beginner"
        elif self.experience_years < 5:
            return "Intermediate"
        elif self.experience_years < 10:
            return "Experienced"
        else:
            return "Expert"

    def __post_init__(self):
        """Post initialization"""
        if isinstance(self.certification_level, str):
            self.certification_level = CertificationLevel(self.certification_level)