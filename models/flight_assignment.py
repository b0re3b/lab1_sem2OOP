from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class AssignmentStatus(enum.Enum):
    """Assignment status enumeration"""
    ASSIGNED = "ASSIGNED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class FlightAssignment(BaseModel):
    """Flight assignment model for crew assignments to flights"""

    __tablename__ = 'flight_assignments'

    flight_id = Column(Integer, ForeignKey('flights.id'), nullable=False)
    crew_member_id = Column(Integer, ForeignKey('crew_members.id'), nullable=False)
    assigned_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_at = Column(DateTime, nullable=False)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.ASSIGNED)
    notes = Column(Text)

    # Unique constraint to prevent double assignment
    __table_args__ = (
        UniqueConstraint('crew_member_id', 'flight_id', name='unique_crew_flight_assignment'),
    )

    # Relationships
    flight = relationship("Flight", back_populates="flight_assignments")
    crew_member = relationship("CrewMember", back_populates="flight_assignments")
    assigned_by_user = relationship("User", back_populates="flight_assignments")

    def is_active(self):
        """Check if assignment is active"""
        return self.status in [AssignmentStatus.ASSIGNED, AssignmentStatus.CONFIRMED]

    def confirm(self):
        """Confirm the assignment"""
        self.status = AssignmentStatus.CONFIRMED

    def cancel(self):
        """Cancel the assignment"""
        self.status = AssignmentStatus.CANCELLED

    def __repr__(self):
        return f"<FlightAssignment(flight='{self.flight.flight_number}', crew='{self.crew_member.full_name}', status='{self.status.value}')>"