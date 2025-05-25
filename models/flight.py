from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class FlightStatus(enum.Enum):
    """Flight status enumeration"""
    SCHEDULED = "SCHEDULED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Flight(BaseModel):
    """Flight model for airline flights"""

    __tablename__ = 'flights'

    flight_number = Column(String(10), unique=True, nullable=False)
    departure_city = Column(String(100), nullable=False)
    arrival_city = Column(String(100), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    aircraft_type = Column(String(50), nullable=False)
    status = Column(Enum(FlightStatus), default=FlightStatus.SCHEDULED)
    crew_required = Column(Integer, default=4)
    created_by = Column(Integer, ForeignKey('users.id'))

    # Relationships
    created_by_user = relationship("User", back_populates="created_flights", foreign_keys=[created_by])
    flight_assignments = relationship("FlightAssignment", back_populates="flight", cascade="all, delete-orphan")

    @property
    def duration(self):
        """Calculate flight duration"""
        if self.departure_time and self.arrival_time:
            return self.arrival_time - self.departure_time
        return None

    @property
    def route(self):
        """Get flight route as string"""
        return f"{self.departure_city} → {self.arrival_city}"

    def is_scheduled(self):
        """Check if flight is scheduled"""
        return self.status == FlightStatus.SCHEDULED

    def is_active(self):
        """Check if flight is active (not cancelled or completed)"""
        return self.status in [FlightStatus.SCHEDULED, FlightStatus.DELAYED]

    def get_assigned_crew_count(self):
        """Get count of assigned crew members"""
        return len([a for a in self.flight_assignments if a.status == 'ASSIGNED'])

    def is_fully_staffed(self):
        """Check if flight has required crew members"""
        return self.get_assigned_crew_count() >= self.crew_required

    def __repr__(self):
        return f"<Flight(number='{self.flight_number}', route='{self.route}', status='{self.status.value}')>"